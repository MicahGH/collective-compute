# CollectiveCompute

Initial MVP implementation of a central gateway and provider-node boundary.

## Two-laptop smoke test

Install [uv](https://docs.astral.sh/uv/) and run `uv sync --extra dev` on both
laptops. Copy `.env.example` into each machine's environment (PowerShell does
not load `.env` files automatically); use a long random value for each key.

On the **gateway laptop**, set its two API keys and start the gateway on every
network interface:

```powershell
$env:CC_PROVIDER_API_KEY = "a-long-provider-secret"
$env:CC_CLIENT_API_KEY = "a-long-client-secret"
uv run uvicorn collective_compute.gateway.app:app --host 0.0.0.0 --port 8000
```

Find the gateway's LAN address with `ipconfig`. On the **provider laptop**, set
the same provider key, replace the two LAN addresses, and start the node:

```powershell
$env:CC_PROVIDER_API_KEY = "a-long-provider-secret"
$env:CC_GATEWAY_URL = "http://192.168.1.10:8000"
$env:CC_NODE_ID = "laptop-provider-1"
$env:CC_NODE_ENDPOINT_URL = "http://192.168.1.11:8001"
$env:CC_NODE_GPU_NAME = "RTX 3060"
$env:CC_NODE_VRAM_GB = "12"
$env:CC_NODE_MAX_GPU_USAGE_PERCENT = "50"
uv run uvicorn collective_compute.node.app:app --host 0.0.0.0 --port 8001
```

The node registers itself and sends a heartbeat every 15 seconds. From the
gateway laptop, confirm it appears online:

```powershell
Invoke-RestMethod http://localhost:8000/providers -Headers @{ "X-API-Key" = "a-long-client-secret" }
```

Then submit a simulated inference request:

```powershell
$body = @{ model = "demo-model"; prompt = "Hello from the other laptop"; parameters = @{ max_tokens = 32; temperature = 0.7 } } | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/inference -Method Post -Headers @{ "X-API-Key" = "a-long-client-secret"; "Content-Type" = "application/json" } -Body $body
```

Both laptops must be on a network that allows the selected ports. Windows may
ask to permit Python through the private-network firewall; allow it only on the
private network. Use HTTPS and distinct, rotated secrets before exposing either
service outside your LAN.

Run tests with:

```powershell
uv run pytest
```

## Quality checks

The project enforces Black formatting, Ruff linting, and strict Pyright/Pylance
type checking. Run all checks before committing:

```powershell
uv run black --check .
uv run ruff check .
uv run pyright
```

Install the Git pre-commit hook to run these checks automatically before every
commit:

```powershell
uv run pre-commit install
```
