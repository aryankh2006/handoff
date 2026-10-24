# CLAUDE.md — read this first

Read [docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md) for the why.

## Project
**Handoff** lets paramedics call a Vapi voice phone line to report an incoming ambulance (unit, age,
complaint, stable/critical, ETA). A FastAPI server keeps each report in memory, detects surges
(3+ ambulances with status `incoming` and ETA ≤ 20 min), and places an outbound Vapi call warning the
ER charge nurse. A static HTML ER board shows incoming ambulance cards, a red surge banner, and
handoff-time compliance stats against California's 30-minute ambulance offload standard (AB 40).
**Simulated patients only — never use real patient data.**

The data contract lives in [contract.md](contract.md). It is the single source of truth.

## Roles and folder ownership
| Person | Folder    | Owns                                                  |
|--------|-----------|-------------------------------------------------------|
| 1      | `voice/`  | Vapi assistants, `submit_report` tool, ngrok          |
| 2      | `server/` | FastAPI, surge logic, outbound nurse call, stats      |
| 3      | `board/`  | ER board UI                                           |
| 4      | `pitch/`  | Pitch, demo script, judge Q&A, testing (`scripts/`)   |

## Rules
- Only edit files in **your own folder**. Need a change elsewhere? Ask the owner.
- Never change `contract.md` without telling the team.
- No databases, no auth, no new frameworks. Plain FastAPI + plain HTML/JS.
- Keep the app runnable at every commit.
- Commit small and often.
- Always `git pull --rebase` before `git push`.

## Timeline
- **4:15 PM** checkpoint — a real phone call creates a card on the board.
- **5:15 PM** feature freeze. Bug fixes and demo polish only.
- **6:15 PM** submit.

## Fallback
If Vapi inbound fails, use the "Manual report" form on `board/index.html` (POSTs to `/report`) and
keep only the outbound nurse call as the live voice moment. If the outbound call also fails, the
server dry-runs it into the call log so the board still shows it.

## Quick reference
- Run: `uvicorn server.main:app --reload --port 8000` (from repo root, venv active)
- Board: http://localhost:8000/board/ (or open `board/index.html` directly)
- Reset demo: `curl -X POST localhost:8000/reset`
