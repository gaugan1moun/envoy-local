# envoy-local

Minimal wrapper to spin up local Envoy proxy configs for service mesh testing.

---

## Installation

```bash
pip install envoy-local
```

> Requires [Envoy proxy](https://www.envoyproxy.io/docs/envoy/latest/start/install) to be installed and available on your `PATH`.

---

## Usage

Initialize a basic Envoy config and start a local proxy:

```python
from envoy_local import EnvoyLocal

proxy = EnvoyLocal(
    listen_port=10000,
    upstream_host="127.0.0.1",
    upstream_port=8080
)

proxy.start()
print("Envoy proxy running on port 10000")
proxy.stop()
```

Or use the CLI:

```bash
envoy-local start --listen 10000 --upstream 127.0.0.1:8080
envoy-local stop
```

Generated configs are written to `./envoy-local-config/` by default and can be inspected or modified before use.

---

## Features

- Auto-generates valid Envoy v3 bootstrap configs
- Supports HTTP, TCP, and gRPC listeners
- Configurable cluster definitions and health checks
- Teardown cleans up processes and temp files automatically

---

## License

MIT © [envoy-local contributors](LICENSE)