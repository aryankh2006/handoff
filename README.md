# Handoff

Paramedics phone in incoming ambulances → ER board updates live → surge triggers a phone call to the
charge nurse. Tracks handoff times against California's 30-minute offload standard (AB 40).
Simulated patients only. See [CLAUDE.md](CLAUDE.md) for roles and rules, [contract.md](contract.md) for the API.

## Setup
```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r server/requirements.txt
cp .env.example .env   # fill in Vapi keys (optional — without them the nurse call is a dry run)
```

## Run
```bash
uvicorn server.main:app --reload --port 8000
```

## Expose to Vapi
```bash
ngrok http 8000
```
Put the `https://...ngrok-free.app` URL into `PUBLIC_URL` in `.env` and into the Vapi tool's server URL
as `{PUBLIC_URL}/report`. Full steps: [voice/SETUP.md](voice/SETUP.md).

## Board
Open http://localhost:8000/board/ (served by the API), or open `board/index.html` directly in a browser.
`API_BASE` at the top of the file defaults to `http://localhost:8000`. If the server is unreachable the
board falls back to `board/fake_state.json` (only works when served over http, not `file://`).

## Test
```bash
bash scripts/test_report.sh
bash scripts/test_surge.sh
curl -X POST localhost:8000/reset    # restart the demo
```
Scripts use `BASE=http://localhost:8000` by default; override with `BASE=https://... bash scripts/test_surge.sh`.
