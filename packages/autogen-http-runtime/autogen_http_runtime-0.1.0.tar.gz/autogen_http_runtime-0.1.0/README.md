**TL;DR**
`autogen_http_runtime` is a *community‑maintained* drop‑in runtime for the \[Microsoft AutoGen] core framework that works as a drop-in replacement to the gRPC/Protobuf transport with a pure‑HTTP stack built on FastAPI, WebSockets and HTTPX. It lets you run agents locally, on remote machines, or inside container clusters without installing gRPC toolchains or generating code. The package exposes three public classes – `HttpAgentServer`, `HttpAgentService`, and `HttpWorkerAgentRuntime` – that together form a minimal host‑and‑worker model for AutoGen agents. Everything is 100  % Python 3.10+, uses standard asyncio, and is ready to hack on.

---

## 1. Why another runtime?

AutoGen defines an *agent runtime* abstraction to decouple agent logic from the underlying transport and execution environment. The reference runtimes use gRPC/Protobuf, which adds excellent performance but also extra tooling, generated stubs and language bindings. Another additional advantage is being able to leverage FastAPI vast middleware ecosystem to build agentic applications.

This repository demonstrates that the same runtime contract can be satisfied with nothing more than:

| Layer                    | Library                        | File(s)                                                        |
| ------------------------ | ------------------------------ | -------------------------------------------------------------- |
| HTTP/1.1 + HTTP/2 client | `httpx.AsyncClient`            | `_worker_runtime.py`([medium.com][5])                          |
| Server + REST + WS       | `FastAPI` & `WebSocket` routes | `_worker_runtime_server.py`([fastapi.tiangolo.com][3])         |
| Raw WS transport         | `websockets`                   | `_worker_runtime.py`([websockets.readthedocs.io][6])           |
| Embedded server          | `uvicorn`                      | `_worker_runtime_server.py`([uvicorn.org][7])                  |
| Tracing (optional)       | OpenTelemetry                  | `_worker_runtime.py`([opentelemetry-python.readthedocs.io][8]) |

No code generation, no `.proto` files, no C extensions – just pure Python.

---

## 2. Architecture at a glance

```text
┌────────────┐              ┌────────────────────┐              ┌────────────┐
│  Worker 1  │              │   HTTP Agent Host  │              │  Worker 2  │
│ (Reverse)  │──WS/HTTP────▶│  FastAPI+Uvicorn   │◀──WS/HTTP────│  (Upper)   │
└────────────┘   register   │  _worker_runtime_* │   register   └────────────┘
      ▲   ▲     call/publish└────────────────────┘     ▲   ▲
      │   └─events────────────┬────────────────────────┘   │
      └────────rpc────────────┘                            └──events
```

* **Host** (`HttpAgentServer`) keeps a registry of agent **types** → connected **clients** and routes all RPCs/events.
* **Workers** run `HttpWorkerAgentRuntime`, register the agent factory or concrete instance, and wait for messages.
* The contract is identical to the official `AgentRuntime` API, so any AutoGen agent or orchestrator can switch transports just by instantiating a different runtime class.([microsoft.com][9])

---

## 3. Quick start

### 3.1 Installation

```bash
pip install autogen-core httpx fastapi websockets uvicorn[standard] opentelemetry-sdk
# until published to PyPI:
pip install -e .
```

### 3.2 Run the demo

```bash
# ➊ start the host
python samples/run_server.py                         # listens on :9000

# ➋ start two workers (in separate shells)
python samples/workers/reverse_agent.py              # registers type "reverse"
python samples/workers/upper_agent.py                # registers type "upper"

# ➌ call them
python samples/orchestrator.py
# → reverse → !emitnur etouR PTTH detubirtsid olleH
# → upper   → HELLO DISTRIBUTED HTTP RUNTIME!
```

All communication flows over **JSON‑RPC 2.0** for point‑to‑point calls and CloudEvents‑style envelopes for pub/sub. No ports other than 9000 are needed.

---

## 4. Using in your own project

### 4.1 Switch an existing AutoGen app to HTTP

```python
from autogen_http_runtime.runtimes.http import HttpWorkerAgentRuntime
runtime = HttpWorkerAgentRuntime("http://my‑host:9000")
await runtime.start()
# rest of your orchestrator or agent code is unchanged
```

### 4.2 Write a new worker agent

```python
class EchoAgent(BaseAgent):
    async def on_message(self, message: str, ctx: MessageContext):
        return f"echo: {message}"
        
rt = HttpWorkerAgentRuntime("http://127.0.0.1:9000")
await rt.register_factory("echo", lambda: EchoAgent())
await rt.start()
await rt.stop_when_signal()
```

### 4.3 Publish/subscribe

```python
# subscribe worker to any topic type that starts with "news."
from autogen_core import TypePrefixSubscription, TopicId
await rt.add_subscription(TypePrefixSubscription("news.*", agent_type="my_agent"))

# publish an event from anywhere
await rt.publish_message({"headline": "42"}, TopicId("news.tech", "server"))
```

Subscriptions are stored centrally in the host so multiple workers can react to the same topics without extra plumbing.

### 4.4 Message serialization
When sending messages between agents over HTTP, `autogen-core` requires explicit serialization. It does **not** serialize primitive Python types like `str` or `int` out of the box. Attempting to send a raw string to a remote agent will raise a `ValueError` because no serializer is found.

To ensure messages can be sent across processes, you have two options:

**1. Use structured messages (recommended)**
Wrap your data in a `dataclass` or a Pydantic `BaseModel`. This is the most robust and common approach. You must then register a corresponding serializer with your runtime instance.

```python
from dataclasses import dataclass
from autogen_core import DataclassJsonMessageSerializer

@dataclass
class TextMessage:
    content: str

# Assuming 'runtime' is your HttpWorkerAgentRuntime instance
runtime.add_message_serializer(DataclassJsonMessageSerializer(TextMessage))

# Now you can send and receive TextMessage objects
# e.g. from an agent's on_message handler:
# return TextMessage("this is a reply")
```

**2. Create a custom serializer**
For simple cases, you can implement `MessageSerializer` for a primitive type and register it.

```python
import json
from autogen_core import MessageSerializer

class StringSerializer(MessageSerializer[str]):
    @property
    def data_content_type(self) -> str:
        return "application/json"
    
    @property
    def type_name(self) -> str:
        return "str"
    
    def deserialize(self, payload: bytes) -> str:
        return json.loads(payload.decode("utf-8"))
    
    def serialize(self, message: str) -> bytes:
        return json.dumps(message).encode("utf-8")

# Register with your runtime instance
runtime.add_message_serializer(StringSerializer())
```
With this serializer, agents can exchange raw `str` messages.

---

## 5. Graceful shutdown & signals

Both server and worker runtimes expose `stop_when_signal()` helpers that attach `SIGINT`/`SIGTERM` handlers via `asyncio.add_signal_handler`, ensuring a tidy close of WebSocket connections and outstanding RPC futures.([stackoverflow.com][10], [docs.python.org][11])

---

## 6. Tracing & observability

If you pass an `opentelemetry.trace.TracerProvider` to the worker runtime, every inbound and outbound message is wrapped in spans named `agent.call`, `agent.publish`, etc., so you can pipe traces to Jaeger, OTLP or Azure Monitor with a couple of environment variables.([opentelemetry-python.readthedocs.io][8], [opentelemetry.io][12])

---