"""Handoff server: in-memory ambulance reports, surge detection, outbound Vapi nurse call.

Implements contract.md. Run from repo root: uvicorn server.main:app --reload --port 8000
"""
import json
import math
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

VAPI_API_KEY = os.getenv("VAPI_API_KEY", "")
VAPI_PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER_ID", "")
VAPI_NURSE_ASSISTANT_ID = os.getenv("VAPI_NURSE_ASSISTANT_ID", "")
NURSE_PHONE = os.getenv("NURSE_PHONE", "")

SURGE_COUNT = 3
SURGE_ETA_MIN = 20
SURGE_COOLDOWN = timedelta(minutes=10)
# An "incoming" ambulance this many minutes past its ETA (never marked arrived) is treated as stale
# and no longer counts toward a surge, so a forgotten Arrived click can't pin the banner on.
STALE_AFTER_MIN = 15
HANDOFF_LIMIT_MIN = 30

app = FastAPI(title="Handoff")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ---- in-memory store ----
ambulances: dict[str, dict] = {}
call_log: list[dict] = []
last_surge_call: datetime | None = None


def now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def make_ambulance(unit, age, complaint, acuity, eta_min, reported_at=None) -> dict:
    try:
        age = int(age)
    except (TypeError, ValueError):
        age = 0
    try:
        eta_min = int(eta_min)
    except (TypeError, ValueError):
        eta_min = 0
    acuity = str(acuity).lower().strip()
    return {
        "id": str(uuid.uuid4()),
        "unit": str(unit or "Unknown unit"),
        "age": age,
        "complaint": str(complaint or "unspecified"),
        "acuity": acuity if acuity in ("stable", "critical") else "stable",
        "eta_min": eta_min,
        "reported_at": iso(reported_at or now()),
        "status": "incoming",
        "arrived_at": None,
        "handoff_at": None,
    }


def seed():
    global last_surge_call
    ambulances.clear()
    call_log.clear()
    last_surge_call = None
    t = now()
    # Already handed off, slow handoff (42 min) so stats show an AB 40 violation.
    done = make_ambulance("Medic 7", 81, "hip fracture after fall", "stable", 10, t - timedelta(minutes=70))
    done.update(status="handed_off", arrived_at=iso(t - timedelta(minutes=60)), handoff_at=iso(t - timedelta(minutes=18)))
    # Currently incoming.
    inc = make_ambulance("Medic 3", 54, "shortness of breath", "critical", 12)
    for a in (done, inc):
        ambulances[a["id"]] = a


def eta_remaining(a: dict) -> float:
    """Minutes until arrival right now: eta_min counts down from reported_at (negative = overdue)."""
    elapsed = (now() - datetime.fromisoformat(a["reported_at"])).total_seconds() / 60
    return a["eta_min"] - elapsed


def surge_window() -> list[dict]:
    """Incoming ambulances arriving within SURGE_ETA_MIN, excluding stale ones long past their ETA."""
    return [
        a for a in ambulances.values()
        if a["status"] == "incoming" and -STALE_AFTER_MIN <= eta_remaining(a) <= SURGE_ETA_MIN
    ]


def is_surge() -> bool:
    return len(surge_window()) >= SURGE_COUNT


def compute_stats() -> dict:
    mins = []
    for a in ambulances.values():
        if a["arrived_at"] and a["handoff_at"]:
            delta = datetime.fromisoformat(a["handoff_at"]) - datetime.fromisoformat(a["arrived_at"])
            mins.append(delta.total_seconds() / 60)
    if not mins:
        return {"avg_handoff_min": 0, "p90_handoff_min": 0, "over_30_count": 0, "total": 0}
    mins.sort()
    p90 = mins[max(0, math.ceil(0.9 * len(mins)) - 1)]  # nearest-rank
    return {
        "avg_handoff_min": round(sum(mins) / len(mins), 1),
        "p90_handoff_min": round(p90, 1),
        "over_30_count": sum(1 for m in mins if m > HANDOFF_LIMIT_MIN),
        "total": len(mins),
    }


def state() -> dict:
    return {
        "ambulances": sorted(ambulances.values(), key=lambda a: a["reported_at"], reverse=True),
        "surge": is_surge(),
        "call_log": call_log,
        "stats": compute_stats(),
    }


def surge_message() -> str:
    incoming = surge_window()
    critical = sum(1 for a in incoming if a["acuity"] == "critical")
    soonest = max(0, round(min(eta_remaining(a) for a in incoming)))
    return (
        f"Surge warning from Handoff. {len(incoming)} ambulances arriving within {SURGE_ETA_MIN} minutes, "
        f"{critical} critical. First one in {soonest} minutes. Please prepare beds and staff for offload."
    )


def place_nurse_call(message: str):
    """Runs as a background task so the Vapi tool response stays fast."""
    entry = {"time": iso(now()), "to": NURSE_PHONE or "(dry run)", "message": message}
    if not (VAPI_API_KEY and VAPI_PHONE_NUMBER_ID and VAPI_NURSE_ASSISTANT_ID and NURSE_PHONE):
        entry["message"] = "[DRY RUN] " + message
        call_log.append(entry)
        print("DRY RUN nurse call:", message)
        return
    try:
        r = httpx.post(
            "https://api.vapi.ai/call",
            headers={"Authorization": f"Bearer {VAPI_API_KEY}"},
            json={
                "assistantId": VAPI_NURSE_ASSISTANT_ID,
                "phoneNumberId": VAPI_PHONE_NUMBER_ID,
                "customer": {"number": NURSE_PHONE},
                "assistantOverrides": {
                    "firstMessage": message,
                    "variableValues": {"surge_message": message},
                },
            },
            timeout=15,
        )
        if r.status_code >= 300:
            try:
                reason = r.json().get("message", r.text)
            except ValueError:
                reason = r.text
            entry["message"] = f"[VAPI ERROR {r.status_code}: {reason}] {message}"
            print(f"Vapi call failed: {r.status_code}\n  response body: {r.text}")
    except Exception as e:  # never break the demo on a network error
        entry["message"] = f"[VAPI ERROR] {message}"
        print("Vapi call exception:", e)
    call_log.append(entry)


def check_surge(background: BackgroundTasks):
    global last_surge_call
    if not is_surge():
        return
    if last_surge_call and now() - last_surge_call < SURGE_COOLDOWN:
        return
    last_surge_call = now()
    background.add_task(place_nurse_call, surge_message())


def extract_tool_calls(body: dict) -> list[dict] | None:
    """Return Vapi tool calls if this is a Vapi webhook, else None (plain JSON report).

    A Vapi webhook with no tool calls (status-update, end-of-call-report, ...) returns [] so it is
    ignored rather than treated as a plain report, which would create an "Unknown unit" card.
    """
    msg = body.get("message")
    if not isinstance(msg, dict):
        return None
    calls = msg.get("toolCalls") or msg.get("toolCallList")
    return calls if isinstance(calls, list) else []


def parse_args(call: dict) -> dict:
    args = (call.get("function") or {}).get("arguments") or call.get("arguments") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            args = {}
    return args


def add_report(args: dict) -> dict:
    a = make_ambulance(args.get("unit"), args.get("age"), args.get("complaint"), args.get("acuity"), args.get("eta_min"))
    ambulances[a["id"]] = a
    return a


# ---- endpoints ----
@app.post("/report")
async def report(request: Request, background: BackgroundTasks):
    try:
        body = await request.json()
    except ValueError:
        raise HTTPException(400, "body must be JSON")
    if not isinstance(body, dict):
        raise HTTPException(400, "body must be a JSON object")
    tool_calls = extract_tool_calls(body)
    if tool_calls is None:
        a = add_report(body)
        check_surge(background)
        return a
    results = []
    for call in tool_calls:
        a = add_report(parse_args(call))
        results.append({
            "toolCallId": call.get("id", ""),
            "result": (
                f"Got it. {a['unit']}, {a['age']} year old, {a['complaint']}, {a['acuity']}, "
                f"ETA {a['eta_min']} minutes. The ER has been notified."
            ),
        })
    check_surge(background)
    return {"results": results}


@app.get("/state")
def get_state():
    return state()


@app.post("/arrive/{amb_id}")
def arrive(amb_id: str):
    a = ambulances.get(amb_id)
    if not a:
        raise HTTPException(404, "ambulance not found")
    a["status"] = "arrived"
    a["arrived_at"] = iso(now())
    return a


@app.post("/handoff/{amb_id}")
def handoff(amb_id: str):
    a = ambulances.get(amb_id)
    if not a:
        raise HTTPException(404, "ambulance not found")
    a["status"] = "handed_off"
    a["arrived_at"] = a["arrived_at"] or iso(now())
    a["handoff_at"] = iso(now())
    return a


@app.post("/reset")
def reset():
    seed()
    return state()


seed()

# Convenience: board also served at http://localhost:8000/board/
app.mount("/board", StaticFiles(directory=ROOT / "board", html=True), name="board")
