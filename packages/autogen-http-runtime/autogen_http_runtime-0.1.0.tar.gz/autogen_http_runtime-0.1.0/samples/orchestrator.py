import asyncio
import logging
from dataclasses import dataclass

from autogen_core import AgentId
from autogen_core._serialization import DataclassJsonMessageSerializer

from autogen_http_runtime.runtimes.http import HttpWorkerAgentRuntime


@dataclass
class TextMessage:
    text: str


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    rt = HttpWorkerAgentRuntime("http://127.0.0.1:9000")
    
    # Register serializer for our message type
    rt.add_message_serializer(DataclassJsonMessageSerializer(TextMessage))
    
    await rt.start()

    reverse = AgentId("reverse", "default")
    upper = AgentId("upper", "default")

    msg = TextMessage(text="Hello distributed HTTP runtime!")
    out1 = await rt.send_message(msg, reverse)
    out2 = await rt.send_message(msg, upper)
    print(f"{reverse.type} → {out1.text}")  # noqa: T201
    print(f"{upper.type}   → {out2.text}")  # noqa: T201

    await rt.stop()


if __name__ == "__main__":
    asyncio.run(main())
