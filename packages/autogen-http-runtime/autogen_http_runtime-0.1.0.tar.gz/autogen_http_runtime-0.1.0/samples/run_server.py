import asyncio
import logging

from autogen_http_runtime.runtimes.http import HttpAgentServer


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    server = HttpAgentServer(address="127.0.0.1", port=9000)
    server.start()
    print("\U0001f680  HTTP Agent Server running at http://127.0.0.1:9000  –  press Ctrl‑C to stop")  # noqa: T201
    await server.stop_when_signal()


if __name__ == "__main__":
    asyncio.run(main())
