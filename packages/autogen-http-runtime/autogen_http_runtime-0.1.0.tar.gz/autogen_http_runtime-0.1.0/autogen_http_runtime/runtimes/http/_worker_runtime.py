import asyncio
import json
import logging
import signal
import uuid
from typing import Any, Awaitable, Callable, Dict, Mapping, Optional, Sequence, Set, Type, TypedDict, Union, List

import httpx
from autogen_core import (
    Agent,
    AgentId,
    AgentInstantiationContext,
    AgentMetadata,
    AgentRuntime,
    AgentType,
    CancellationToken,
    MessageContext,
    MessageSerializer,
    TopicId,
)
from autogen_core._runtime_impl_helpers import SubscriptionManager, get_impl
from autogen_core._serialization import JSON_DATA_CONTENT_TYPE, PROTOBUF_DATA_CONTENT_TYPE, SerializationRegistry
from autogen_core._telemetry import MessageRuntimeTracingConfig, TraceHelper
from opentelemetry.trace import TracerProvider

from ._json_rpc import JsonRpcRequest, JsonRpcResponse

# Import Subscription related types directly
from autogen_core import TypeSubscription as CoreTypeSubscription
from autogen_core import TypePrefixSubscription as CoreTypePrefixSubscription
from autogen_core import Subscription as CoreSubscription

logger = logging.getLogger(__name__)


# TypedDicts for subscription serialization
class TypeSubscriptionDict(TypedDict):
    topic_type: str
    agent_type: str


class TypePrefixSubscriptionDict(TypedDict):
    topic_type_prefix: str
    agent_type: str


class SubscriptionDict(TypedDict, total=False):
    id: str
    type_subscription: TypeSubscriptionDict
    type_prefix_subscription: TypePrefixSubscriptionDict


# Helper functions moved/duplicated here as they are now needed by client
def subscription_from_json(data: SubscriptionDict) -> CoreSubscription:
    sub_id = data.get("id", "")
    ts_data = data.get("type_subscription")
    tps_data = data.get("type_prefix_subscription")

    if ts_data:
        # Assuming CoreTypeSubscription can be constructed this way or needs a specific factory
        return CoreTypeSubscription(topic_type=ts_data["topic_type"], agent_type=ts_data["agent_type"], id=sub_id)
    elif tps_data:
        # Assuming CoreTypePrefixSubscription can be constructed this way or needs a specific factory
        return CoreTypePrefixSubscription(topic_type_prefix=tps_data["topic_type_prefix"], agent_type=tps_data["agent_type"], id=sub_id)
    else:
        raise ValueError("Invalid subscription JSON")


def subscription_to_json(s: CoreSubscription) -> SubscriptionDict:
    d: SubscriptionDict = {"id": s.id}
    if isinstance(s, CoreTypeSubscription):
        d["type_subscription"] = {
            "topic_type": s.topic_type,
            "agent_type": s.agent_type,
        }
    elif isinstance(s, CoreTypePrefixSubscription):
        d["type_prefix_subscription"] = {
            "topic_type_prefix": s.topic_type_prefix,
            "agent_type": s.agent_type,
        }
    return d


class HttpHostConnection:
    """
    Manages the underlying connection(s) to the HTTP host.
    - Uses an async HTTP client for normal requests (RegisterAgent, AddSubscription, etc.).
    - Uses an async WebSocket for the "channel" to exchange streaming messages (request/response, events).
    """

    def __init__(self, base_url: str, client_id: str):
        self._base_url = base_url.rstrip("/")
        self._client_id = client_id
        self._http = httpx.AsyncClient()
        self._ws: Optional[Any] = None  # will be a connected websockets session
        self._send_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self._recv_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self._run_read_task: Optional[asyncio.Task[Any]] = None
        self._run_send_task: Optional[asyncio.Task[Any]] = None
        self._connected = False

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def client_id(self) -> str:
        return self._client_id

    async def connect(self) -> None:
        """
        Opens a WebSocket to the server for streaming messages, and starts
        a background read loop putting messages onto _recv_queue.
        """
        import websockets  # type: ignore[import-not-found]

        ws_url = f"{self._base_url.replace('http', 'ws')}/open_channel?client_id={self._client_id}"
        logger.info(f"Connecting WebSocket to: {ws_url}")
        self._ws = await websockets.connect(ws_url)
        self._connected = True

        # Start a background read loop
        self._run_read_task = asyncio.create_task(self._read_loop())

        # Start a background send loop (optional, or you can push messages as needed)
        self._run_send_task = asyncio.create_task(self._send_loop())

    async def close(self) -> None:
        if self._connected and self._ws is not None:
            await self._ws.close()
            self._connected = False
        if self._run_read_task:
            self._run_read_task.cancel()
            try:
                await self._run_read_task
            except asyncio.CancelledError:
                pass
        if self._run_send_task:
            self._run_send_task.cancel()
            try:
                await self._run_send_task
            except asyncio.CancelledError:
                pass
        await self._http.aclose()

    async def _read_loop(self) -> None:
        """
        Continuously read from the WebSocket and push incoming messages to _recv_queue.
        """
        try:
            while True:
                if self._ws is None:
                    await asyncio.sleep(0.1)
                    continue
                raw_msg = await self._ws.recv()
                if isinstance(raw_msg, str):
                    data = json.loads(raw_msg)
                    await self._recv_queue.put(data)
        except asyncio.CancelledError:
            # normal on shutdown
            pass
        except Exception as ex:
            logger.error("Error in _read_loop", exc_info=ex)

    async def _send_loop(self) -> None:
        """
        Continuously get messages from _send_queue and send them over the WebSocket.
        """
        try:
            while True:
                data = await self._send_queue.get()
                if self._connected and self._ws is not None:
                    await self._ws.send(json.dumps(data))
        except asyncio.CancelledError:
            # normal on shutdown
            pass
        except Exception as ex:
            logger.error("Error in _send_loop", exc_info=ex)

    async def call_rpc(self, method: str, params: Dict[str, Any], rpc_id: str | int | None) -> Optional[Any]:
        payload = JsonRpcRequest(method=method, params=params, id=rpc_id).model_dump()
        logger.info(f"Sending RPC request to {self._base_url}/rpc with method={method}, id={rpc_id}")
        try:
            r = await self._http.post(f"{self._base_url}/rpc", json=payload, headers={"x-client-id": self._client_id})
            r.raise_for_status()
            reply = JsonRpcResponse(**r.json())
            if reply.error is not None:
                logger.error(f"RPC error: {reply.error}")
                raise RuntimeError(reply.error.get("message", "unknown rpc error"))
            logger.info(f"Received RPC response for id={rpc_id}")
            return reply.result
        except Exception as e:
            logger.error(f"Error in call_rpc: {str(e)}")
            raise

    async def send_channel_message(self, message_dict: Dict[str, Any]) -> None:
        """
        Enqueue a JSON-serializable dict to be sent over the WebSocket channel.
        """
        await self._send_queue.put(message_dict)

    async def recv_channel_message(self) -> Dict[str, Any]:
        """
        Receive the next inbound message from the WebSocket channel.
        """
        return await self._recv_queue.get()


class HttpWorkerAgentRuntime(AgentRuntime):
    """
    HTTP-based runtime that connects to a "host" that is itself a FastAPI server.
    """

    @staticmethod
    def _placeholder_instance_factory() -> Agent:
        # This factory should ideally never be called if logic is correct.
        # It indicates an attempt to instantiate an agent type that is managed by direct instance registration.
        raise RuntimeError(
            "Internal error: _placeholder_instance_factory was called. "
            "This agent type is managed by direct instance registration, not by factory."
        )

    def __init__(
        self,
        host_address: str,
        tracer_provider: TracerProvider | None = None,
        payload_serialization_format: str = JSON_DATA_CONTENT_TYPE,
    ) -> None:
        self._host_address = host_address
        self._trace_helper = TraceHelper(
            tracer_provider,
            MessageRuntimeTracingConfig("HTTP Worker Runtime"))
        self._agent_factories: Dict[str,
                                    Callable[...,
                                             Agent | Awaitable[Agent]]] = {}
        self._instantiated_agents: Dict[AgentId, Agent] = {}
        self._agent_instance_types: Dict[str, Type[Agent]] = {}
        self._subscription_manager = SubscriptionManager()
        self._serialization_registry = SerializationRegistry()

        if payload_serialization_format not in {
                JSON_DATA_CONTENT_TYPE, PROTOBUF_DATA_CONTENT_TYPE
        }:
            raise ValueError(
                f"Unsupported format: {payload_serialization_format}")
        self._payload_format = payload_serialization_format

        # "connection" to the host. We'll store an ID to identify ourselves.
        self._client_id = str(uuid.uuid4())
        self._host_connection = HttpHostConnection(base_url=host_address,
                                                   client_id=self._client_id)

        # A task to read inbound channel messages from the server
        self._read_task: Optional[asyncio.Task[Any]] = None
        self._running = False

        # Keep track of pending requests by request_id -> Future
        self._pending_requests: Dict[str, asyncio.Future[Any]] = {}
        self._next_request_id = 0
        self._pending_lock = asyncio.Lock()
        self._background_tasks: Set[asyncio.Task[Any]] = set()

    async def start(self) -> None:
        if self._running:
            raise RuntimeError("Already running")
        # Connect the WebSocket
        await self._host_connection.connect()
        # Start read loop
        self._read_task = asyncio.create_task(self._read_loop())
        self._running = True

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        # Cancel read loop
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass

        # close connection
        await self._host_connection.close()
        # wait for any background tasks
        await asyncio.gather(*self._background_tasks, return_exceptions=True)

    async def stop_when_signal(
        self,
        signals: Sequence[signal.Signals] = (signal.SIGINT, signal.SIGTERM)
    ) -> None:
        loop = asyncio.get_running_loop()
        done_event = asyncio.Event()

        def on_signal() -> None:
            done_event.set()

        for s in signals:
            loop.add_signal_handler(s, on_signal)

        await done_event.wait()
        await self.stop()

    async def send_message(
        self,
        message: Any,
        recipient: AgentId,
        *,
        sender: AgentId | None = None,
        cancellation_token: CancellationToken | None = None,
        message_id: str | None = None,
    ) -> Any:
        if not self._running:
            raise RuntimeError("Not running")

        data_type = self._serialization_registry.type_name(message)
        blob = self._serialization_registry.serialize(
            message,
            type_name=data_type,
            data_content_type=self._payload_format)
        req_id = await self._new_request_id()

        params = {
            "target": {
                "type": recipient.type,
                "key": recipient.key
            },
            "source": ({
                "type": sender.type,
                "key": sender.key
            } if sender else None),
            "data_type":
            data_type,
            "data_content_type":
            self._payload_format,
            "data":
            blob.decode() if isinstance(blob, bytes) else blob,
        }

        # "agent.call" is an arbitrary method name – see server handler below
        raw_result: dict[str,
                         Any] | None = await self._host_connection.call_rpc(
                             "agent.call", params, req_id)

        # raw_result is a dict mirroring RpcResponse Payload
        if raw_result is None or not isinstance(raw_result, dict):
            raise ValueError("Invalid RPC response from host")

        assert isinstance(
            raw_result.get("data"),
            (str, bytes)), "RPC response data must be str or bytes"
        assert isinstance(raw_result.get("data_type"),
                          str), "RPC response data_type must be str"
        assert isinstance(raw_result.get("data_content_type"),
                          str), "RPC response data_content_type must be str"

        body = self._serialization_registry.deserialize(
            raw_result["data"].encode()
            if isinstance(raw_result["data"], str) else raw_result["data"],
            type_name=raw_result["data_type"],
            data_content_type=raw_result["data_content_type"],
        )
        return body

    async def publish_message(
        self,
        message: Any,
        topic_id: TopicId,
        *,
        sender: AgentId | None = None,
        cancellation_token: CancellationToken | None = None,
        message_id: str | None = None,
    ) -> None:
        if not self._running:
            raise RuntimeError("Not running")
        if message_id is None:
            message_id = str(uuid.uuid4())

        data_type = self._serialization_registry.type_name(message)
        blob = self._serialization_registry.serialize(
            message,
            type_name=data_type,
            data_content_type=self._payload_format)

        payload = {
            "topic": {
                "type": topic_id.type,
                "source": topic_id.source
            },
            "sender": ({
                "type": sender.type,
                "key": sender.key
            } if sender else None),
            "data_type":
            data_type,
            "data_content_type":
            self._payload_format,
            "data":
            blob.decode() if isinstance(blob, bytes) else blob,
            "id":
            message_id,
        }
        # id = None makes it a notification so no reply is expected
        await self._host_connection.call_rpc("agent.publish",
                                             payload,
                                             rpc_id=None)

    async def save_state(self) -> Mapping[str, Any]:
        raise NotImplementedError(
            "save_state not yet implemented in HTTP runtime.")

    async def load_state(self, state: Mapping[str, Any]) -> None:
        raise NotImplementedError(
            "load_state not yet implemented in HTTP runtime.")

    async def agent_metadata(self, agent: AgentId) -> AgentMetadata:
        raise NotImplementedError(
            "agent_metadata not yet implemented in HTTP runtime.")

    async def agent_save_state(self, agent: AgentId) -> Mapping[str, Any]:
        raise NotImplementedError(
            "agent_save_state not yet implemented in HTTP runtime.")

    async def agent_load_state(self, agent: AgentId,
                               state: Mapping[str, Any]) -> None:
        raise NotImplementedError(
            "agent_load_state not yet implemented in HTTP runtime.")

    async def register_factory(
        self,
        type: str | AgentType,
        agent_factory: Callable[..., Agent | Awaitable[Agent]],
        *,
        expected_class: Type[Agent] | None = None,
    ) -> AgentType:
        if isinstance(type, str):
            type = AgentType(type)
        if type.type in self._agent_factories:
            raise ValueError(f"Agent type {type} already registered.")
        self._agent_factories[type.type] = agent_factory

        # Send a JSON-RPC call to the host to register
        await self._host_connection.call_rpc(
            method="runtime.register_agent",
            params={"type": type.type},
            rpc_id=await
            self._new_request_id(),  # Use new_request_id for admin tasks too
        )

        return type

    async def try_get_underlying_agent_instance(self,
                                                id: AgentId,
                                                type: Optional[
                                                    Type[Agent]] = None
                                                ) -> Agent:
        if id.type not in self._agent_factories:
            raise LookupError(f"Agent type {id.type} not found.")
        agent = await self._get_agent(id)
        if type is not None and not isinstance(agent, type):
            raise TypeError("Agent is not of the expected type.")
        return agent

    async def add_subscription(self, subscription: CoreSubscription) -> None:
        # Send request to host via JSON-RPC
        sub_dict = subscription_to_json(subscription)

        await self._host_connection.call_rpc(
            method="runtime.add_subscription",
            params=sub_dict,  # type: ignore
            rpc_id=await self._new_request_id()  # type: ignore
        )
        await self._subscription_manager.add_subscription(subscription)

    async def remove_subscription(self, id: str) -> None:
        # Send request to host via JSON-RPC
        await self._host_connection.call_rpc(
            method="runtime.remove_subscription",
            params={"id": id},
            rpc_id=await self._new_request_id())
        await self._subscription_manager.remove_subscription(id)

    async def get(
        self,
        id_or_type: AgentId | AgentType | str,
        /,
        key: str = "default",
        *,
        lazy: bool = True,
    ) -> AgentId:
        return await get_impl(id_or_type=id_or_type,
                              key=key,
                              lazy=lazy,
                              instance_getter=self._get_agent)

    def add_message_serializer(
        self, serializer: Union[MessageSerializer[Any],
                                Sequence[MessageSerializer[Any]]]
    ) -> None:
        self._serialization_registry.add_serializer(serializer)

    async def _read_loop(self) -> None:
        """
        Read inbound messages from the server WebSocket channel.
        Dispatch them to either _process_request, _process_response, or _process_event
        depending on the 'type' field.
        """
        while self._running:
            try:
                raw_msg = await self._host_connection.recv_channel_message()
            except asyncio.CancelledError:
                break
            except Exception as ex:
                logger.error("Error reading inbound channel message",
                             exc_info=ex)
                continue

            msg_type = raw_msg.get("type")
            if msg_type == "request":
                task = asyncio.create_task(self._process_request(raw_msg))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
            elif msg_type == "response":
                task = asyncio.create_task(self._process_response(raw_msg))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
            elif msg_type == "cloud_event":
                task = asyncio.create_task(self._process_event(raw_msg))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
            else:
                logger.warning(f"Unknown inbound message type: {msg_type}")

    async def _process_request(self, raw: Dict[str, Any]) -> None:
        """
        The host is delivering an RPC request to us, so we should handle it by
        looking up the agent, calling on_message, then sending a 'response'.
        """
        try:
            req_id = raw["request_id"]
            target = raw["target"]
            agent_id = AgentId(target["type"], target["key"])
            logger.info(
                f"Processing request with ID={req_id} for agent {agent_id}")

            sender = raw.get("source")
            if sender:
                sender_id = AgentId(sender["type"], sender["key"])
            else:
                sender_id = None

            data_type = raw.get("data_type", "unknown")
            data_content_type = raw.get("data_content_type",
                                        JSON_DATA_CONTENT_TYPE)
            body_str = raw.get("data", "")

            # deserialize
            logger.info(
                f"Deserializing message of type {data_type} with content type {data_content_type}"
            )
            try:
                body = self._serialization_registry.deserialize(
                    body_str.encode("utf-8")
                    if isinstance(body_str, str) else body_str,
                    type_name=data_type,
                    data_content_type=data_content_type,
                )
                logger.info(f"Successfully deserialized message")
            except Exception as e:
                logger.error(f"Failed to deserialize message: {str(e)}")
                error_envelope = {
                    "type": "response",
                    "request_id": req_id,
                    "error": f"Failed to deserialize message: {str(e)}",
                }
                await self._host_connection.send_channel_message(error_envelope
                                                                 )
                return

            try:
                logger.info(f"Getting agent {agent_id}")
                agent = await self._get_agent(agent_id)
                ctx = MessageContext(
                    sender=sender_id,
                    topic_id=None,
                    is_rpc=True,
                    cancellation_token=CancellationToken(),
                    message_id=req_id,
                )

                logger.info(f"Calling on_message for agent {agent_id}")
                result = await agent.on_message(body, ctx=ctx)
                logger.info(f"Received result from agent {agent_id}")

                # serialize
                res_type = self._serialization_registry.type_name(result)
                logger.info(f"Serializing result of type {res_type}")
                serialized = self._serialization_registry.serialize(
                    result,
                    type_name=res_type,
                    data_content_type=data_content_type)

                envelope = {
                    "type":
                    "response",
                    "request_id":
                    req_id,
                    "error":
                    "",
                    "data_type":
                    res_type,
                    "data_content_type":
                    data_content_type,
                    "data":
                    serialized.decode("utf-8") if isinstance(
                        serialized, bytes) else serialized,
                    "original_sender":
                    raw.get("original_sender"),
                }
                logger.info(f"Sending response for request {req_id}")
                await self._host_connection.send_channel_message(envelope)
                logger.info(f"Response sent for request {req_id}")
            except Exception as ex:
                logger.error(f"Error processing request: {str(ex)}",
                             exc_info=ex)
                envelope = {
                    "type": "response",
                    "request_id": req_id,
                    "error": str(ex),
                    "original_sender": raw.get("original_sender"),
                }
                await self._host_connection.send_channel_message(envelope)
        except Exception as ex:
            logger.error(f"Unexpected error in _process_request: {str(ex)}",
                         exc_info=ex)

    async def _process_response(self, raw: Dict[str, Any]) -> None:
        try:
            req_id = raw.get("request_id")
            assert isinstance(req_id, str), "request_id must be a string"
            logger.info(f"Processing response for request_id={req_id}")
            error = raw.get("error", "")
            fut = self._pending_requests.get(req_id)
            if not fut:
                logger.warning(f"No pending future for request_id={req_id}")
                return

            if error:
                logger.error(f"Response contains error: {error}")
                fut.set_exception(Exception(error))
                return

            data_type = raw.get("data_type", "unknown")
            data_content_type = raw.get("data_content_type",
                                        JSON_DATA_CONTENT_TYPE)
            body_str = raw.get("data", "")

            logger.info(
                f"Deserializing response of type {data_type} with content type {data_content_type}"
            )
            try:
                body = self._serialization_registry.deserialize(
                    body_str.encode("utf-8")
                    if isinstance(body_str, str) else body_str,
                    type_name=data_type,
                    data_content_type=data_content_type,
                )
                logger.info(
                    f"Successfully deserialized response for request_id={req_id}"
                )
                fut.set_result(body)
                logger.info(f"Set result for future with request_id={req_id}")
            except Exception as e:
                logger.error(
                    f"Failed to deserialize response for request_id={req_id}: {str(e)}"
                )
                fut.set_exception(
                    Exception(f"Failed to deserialize response: {str(e)}"))
        except Exception as ex:
            logger.error(f"Unexpected error in _process_response: {str(ex)}",
                         exc_info=ex)

    async def _process_event(self, raw: Dict[str, Any]) -> None:
        """
        A 'cloud_event' from the host.
        We'll check topic -> see which local agent is subscribed -> deliver it.
        (For brevity, the example does direct dispatch to agents the same way the gRPC runtime does.)
        """
        topic_info = raw.get("topic", {})
        topic_id = TopicId(topic_info.get("type", ""),
                           topic_info.get("source", ""))
        data_content_type = raw.get("data_content_type",
                                    JSON_DATA_CONTENT_TYPE)
        data_type = raw.get("data_type", "unknown")
        payload_str = raw.get("payload", "")
        body = self._serialization_registry.deserialize(
            payload_str.encode("utf-8")
            if isinstance(payload_str, str) else payload_str,
            type_name=data_type,
            data_content_type=data_content_type,
        )
        # figure out which local agents want it
        recipients = await self._subscription_manager.get_subscribed_recipients(
            topic_id)
        sender = raw.get("sender")
        if sender:
            sender_id = AgentId(sender["type"], sender["key"])
        else:
            sender_id = None

        # deliver
        coros: List[Awaitable[Any]] = []
        for agent_id in recipients:
            if agent_id == sender_id:
                continue
            coros.append(
                self._deliver_event(agent_id, body, topic_id,
                                    raw.get("id", "")))

        await asyncio.gather(*coros, return_exceptions=True)

    async def _deliver_event(self, agent_id: AgentId, message: Any,
                             topic_id: TopicId, msg_id: str) -> None:
        agent = await self._get_agent(agent_id)
        ctx = MessageContext(
            sender=None,  # we pass None or real sender if needed
            topic_id=topic_id,
            is_rpc=False,
            cancellation_token=CancellationToken(),
            message_id=msg_id,
        )
        try:
            await agent.on_message(message, ctx=ctx)
        except Exception as ex:
            logger.error(f"Error delivering event to agent {agent_id}",
                         exc_info=ex)

    async def _new_request_id(self) -> str:
        async with self._pending_lock:
            self._next_request_id += 1
            return str(self._next_request_id)

    async def _get_agent(self, agent_id: AgentId) -> Agent:
        if agent_id in self._instantiated_agents:
            return self._instantiated_agents[agent_id]

        # Build from factory
        if agent_id.type not in self._agent_factories:
            raise ValueError(f"Agent type not found: {agent_id.type}")

        factory = self._agent_factories[agent_id.type]
        if factory == HttpWorkerAgentRuntime._placeholder_instance_factory:
            # This means _get_agent was called for an agent_id whose type is managed by instances,
            # but the specific key was not explicitly registered.
            raise LookupError(
                f"Agent with id {agent_id} not found. Agent type '{agent_id.type}' is managed by "
                f"direct instance registration, and this specific key '{agent_id.key}' was not registered."
            )

        with AgentInstantiationContext.populate_context((self, agent_id)):
            maybe = factory() if callable(
                factory) else factory  # depends on signature
            agent = maybe
            if asyncio.iscoroutine(agent):
                agent = await agent
            assert isinstance(agent, Agent)
        self._instantiated_agents[agent_id] = agent
        return agent

    async def register_agent_instance(
        self,
        agent_instance: Agent,
        agent_id: AgentId,
    ) -> AgentId:
        if agent_id in self._instantiated_agents:
            raise ValueError(f"Agent with id {agent_id} already exists.")

        if agent_id.type in self._agent_factories:
            registered_factory = self._agent_factories[agent_id.type]
            # Check if the registered factory is our specific placeholder
            is_placeholder = (registered_factory == HttpWorkerAgentRuntime.
                              _placeholder_instance_factory)

            if not is_placeholder:
                raise ValueError(
                    f"Cannot register instance for agent type '{agent_id.type}'. "
                    f"A different factory is already registered for this type. "
                    f"Mixing factories and direct instance registrations for the same type is not allowed."
                )
            else:
                # It's our placeholder, check Python class consistency
                expected_type = self._agent_instance_types.get(agent_id.type)
                instance_type = type(agent_instance)
                if expected_type != instance_type:
                    raise ValueError(
                        f"All agent instances for type '{agent_id.type}' must be of the same Python class. "
                        f"Expected {expected_type.__name__ if expected_type else 'None'}, got {instance_type.__name__}."
                    )
        else:
            # First time for this agent type (for instances). Register with placeholder.
            self._agent_factories[
                agent_id.
                type] = HttpWorkerAgentRuntime._placeholder_instance_factory
            self._agent_instance_types[agent_id.type] = type(agent_instance)

        # The agent's `bind_id_and_runtime` method (if it's a BaseAgent derivative)
        # is assumed to be called by the static `Agent.register_instance`
        # or equivalent caller, before `runtime.register_agent_instance` is invoked by the client.
        self._instantiated_agents[agent_id] = agent_instance

        # Inform the host about this specific agent instance
        await self._host_connection.call_rpc(
            method="runtime.register_agent_instance",
            params={"agent_id": {
                "type": agent_id.type,
                "key": agent_id.key
            }},
            rpc_id=await self._new_request_id(),
        )

        return agent_id
