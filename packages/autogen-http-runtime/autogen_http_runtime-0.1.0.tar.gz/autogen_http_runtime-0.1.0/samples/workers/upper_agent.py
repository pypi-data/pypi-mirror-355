import asyncio
import logging
from dataclasses import dataclass

from autogen_core import BaseAgent, MessageContext
from autogen_core._serialization import DataclassJsonMessageSerializer

from autogen_http_runtime.runtimes.http import HttpWorkerAgentRuntime


@dataclass
class TextMessage:
    text: str


class UpperAgent(BaseAgent):
    def __init__(self):
        super().__init__("Agent that converts text to uppercase")
    
    async def on_message_impl(self, message: TextMessage, ctx: MessageContext):
        return TextMessage(text=message.text.upper())


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    rt = HttpWorkerAgentRuntime("http://127.0.0.1:9000")
    
    # Register serializer for our message type
    rt.add_message_serializer(DataclassJsonMessageSerializer(TextMessage))
    
    await rt.register_factory("upper", lambda: UpperAgent())
    await rt.start()
    print("\U0001f527  UpperAgent registered – waiting for messages…")  # noqa: T201
    await rt.stop_when_signal()


if __name__ == "__main__":
    asyncio.run(main())
