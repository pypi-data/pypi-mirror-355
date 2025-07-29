# HTTP runtime sample

```bash
# start host
python samples/run_server.py
# in two extra shells
python samples/workers/reverse_agent.py
python samples/workers/upper_agent.py
# exercise the agents
python samples/orchestrator.py
```

Works on Python 3.10+.  No gRPC, no Protobufs, just FastAPI + HTTPX + WebSockets.  Happy hacking!

