# CollectiveCompute

Initial MVP implementation of a central gateway and provider-node boundary.

## Two-laptop smoke test

Install [uv](https://docs.astral.sh/uv/) and run `uv sync --extra dev` on both
laptops. Copy `.env.example` to `.env` in the project root on each laptop, then
replace the sample values with long random secrets and the appropriate LAN IPs.
The services load `.env` automatically; it is excluded from Git.

On the **gateway laptop**, set `CC_PROVIDER_API_KEY` and `CC_CLIENT_API_KEY` in
its `.env`, then start the gateway on every network interface:

```powershell
uv run uvicorn collective_compute.gateway.app:app --host 0.0.0.0 --port 8000
```

Find the gateway's LAN address with `ipconfig`. On the **provider laptop**, set
the same provider key and replace the two LAN addresses in its `.env`, then
start the node:

```powershell
uv run uvicorn collective_compute.node.app:app --host 0.0.0.0 --port 8001
```

The node registers itself and sends a heartbeat every 15 seconds. From the
gateway laptop, confirm it appears online:

```powershell
Invoke-RestMethod http://localhost:8000/providers -Headers @{ "X-API-Key" = "your-client-api-key" }
```

Then submit a simulated inference request:

```powershell
$body = @{ model = "demo-model"; prompt = "Hello from the other laptop"; parameters = @{ max_tokens = 32; temperature = 0.7 } } | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/inference -Method Post -Headers @{ "X-API-Key" = "your-client-api-key"; "Content-Type" = "application/json" } -Body $body
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
