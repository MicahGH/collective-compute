# CollectiveCompute

Initial MVP implementation of a central gateway and provider-node boundary.

## Run locally

Install [uv](https://docs.astral.sh/uv/) if needed, then create the local
environment and install the locked dependencies:

```powershell
uv sync --extra dev
uv run uvicorn collective_compute.gateway.app:app --reload --port 8000
```

In another terminal, start a sample provider node:

```powershell
uv run uvicorn collective_compute.node.app:app --port 8001
```

Register the node with the gateway using `POST /providers/register`, setting
`endpoint_url` to `http://localhost:8001`. The gateway exposes `/docs` for the
available API schema.

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
