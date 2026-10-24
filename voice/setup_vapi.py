"""Idempotent Vapi setup for Handoff. Run from repo root: python voice/setup_vapi.py

Creates or updates (by name):
  - tool       "submit_report"              -> {PUBLIC_URL}/report   (from submit_report_tool.json)
  - assistant  "Handoff Paramedic Line"     (from paramedic_assistant_prompt.md)
  - assistant  "Handoff Charge Nurse Alert" (from nurse_assistant_prompt.md)
  - a free Vapi phone number, inbound -> Paramedic Line
Then writes VAPI_PHONE_NUMBER_ID and VAPI_NURSE_ASSISTANT_ID into .env.
Re-run whenever the ngrok URL or a prompt changes.
"""
import json
import re
import sys
import time
from pathlib import Path

import httpx
from dotenv import dotenv_values

VOICE = Path(__file__).resolve().parent
ROOT = VOICE.parent
ENV_PATH = ROOT / ".env"
API = "https://api.vapi.ai"

PARAMEDIC_NAME = "Handoff Paramedic Line"
NURSE_NAME = "Handoff Charge Nurse Alert"
NUMBER_NAME = "Handoff Paramedic Line"
AREA_CODE = "619"  # San Diego; falls back to any area code if unavailable

env = dotenv_values(ENV_PATH)
API_KEY = (env.get("VAPI_API_KEY") or "").strip()
PUBLIC_URL = (env.get("PUBLIC_URL") or "").strip().rstrip("/")
if not API_KEY or not PUBLIC_URL:
    sys.exit("Set VAPI_API_KEY and PUBLIC_URL in .env first.")

client = httpx.Client(base_url=API, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=30)


def call(method: str, path: str, body: dict | None = None):
    r = client.request(method, path, json=body)
    if r.status_code >= 300:
        sys.exit(f"{method} {path} failed ({r.status_code}): {r.text}")
    return r.json()


def find_by_name(path: str, name: str, key=lambda x: x.get("name")) -> dict | None:
    return next((x for x in call("GET", path) if key(x) == name), None)


def upsert(path: str, name: str, body: dict, key=lambda x: x.get("name")) -> dict:
    existing = find_by_name(path, name, key)
    if existing:
        body = {k: v for k, v in body.items() if k != "type"}  # type is immutable on PATCH
        out = call("PATCH", f"{path}/{existing['id']}", body)
        print(f"updated {path} {name!r}: {out['id']}")
    else:
        out = call("POST", path, body)
        print(f"created {path} {name!r}: {out['id']}")
    return out


def read_prompt(filename: str) -> tuple[str, str]:
    """Return (first_message, system_prompt) from the '## First message' / '## System prompt' sections."""
    text = (VOICE / filename).read_text()
    sections = dict(re.findall(r"^## (.+?)\n(.*?)(?=^## |\Z)", text, flags=re.S | re.M))
    return sections["First message"].strip(), sections["System prompt"].strip()


def assistant_body(name: str, first: str, system: str, tool_ids: list[str], end_message: str) -> dict:
    return {
        "name": name,
        "firstMessage": first,
        "firstMessageMode": "assistant-speaks-first",
        "model": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.2,
            "maxTokens": 120,
            "messages": [{"role": "system", "content": system}],
            "toolIds": tool_ids,
            "tools": [{"type": "endCall"}],
        },
        "voice": {"provider": "vapi", "voiceId": "Elliot"},
        "transcriber": {"provider": "deepgram", "model": "nova-3", "language": "en"},
        "endCallMessage": end_message,
        "maxDurationSeconds": 180,
    }


def update_env(values: dict[str, str]):
    lines = ENV_PATH.read_text().splitlines()
    for key, val in values.items():
        pattern = re.compile(rf"^\s*{key}\s*=")
        idx = next((i for i, l in enumerate(lines) if pattern.match(l)), None)
        if idx is None:
            lines.append(f"{key}={val}")
        else:
            lines[idx] = f"{key}={val}"
    ENV_PATH.write_text("\n".join(lines) + "\n")


# 1. submit_report tool (definition lives in submit_report_tool.json)
tool_body = json.loads((VOICE / "submit_report_tool.json").read_text().replace("{PUBLIC_URL}", PUBLIC_URL))
tool = upsert("/tool", "submit_report", tool_body, key=lambda x: (x.get("function") or {}).get("name"))

# 2. Paramedic Line assistant
first, system = read_prompt("paramedic_assistant_prompt.md")
paramedic = upsert("/assistant", PARAMEDIC_NAME,
                   assistant_body(PARAMEDIC_NAME, first, system, [tool["id"]], "Copy, see you soon."))

# 3. Charge Nurse Alert assistant
first, system = read_prompt("nurse_assistant_prompt.md")
nurse = upsert("/assistant", NURSE_NAME,
               assistant_body(NURSE_NAME, first, system, [], "Thank you. The board is updated. Goodbye."))

# 4. Phone number: reuse any existing one (prefer ours), else create a free Vapi number
numbers = call("GET", "/phone-number")
phone = next((n for n in numbers if n.get("name") == NUMBER_NAME), None) or (numbers[0] if numbers else None)
if phone:
    phone = call("PATCH", f"/phone-number/{phone['id']}", {"assistantId": paramedic["id"]})
    print(f"reused phone number {phone['id']}")
else:
    r = client.post("/phone-number", json={"provider": "vapi", "name": NUMBER_NAME,
                                           "numberDesiredAreaCode": AREA_CODE, "assistantId": paramedic["id"]})
    if r.status_code >= 300:
        print(f"area code {AREA_CODE} unavailable ({r.status_code}), trying any area code")
        phone = call("POST", "/phone-number", {"provider": "vapi", "name": NUMBER_NAME, "assistantId": paramedic["id"]})
    else:
        phone = r.json()
    print(f"created phone number {phone['id']}")

# Free numbers can take a few seconds to get digits assigned
for _ in range(15):
    if phone.get("number"):
        break
    time.sleep(2)
    phone = call("GET", f"/phone-number/{phone['id']}")

update_env({"VAPI_PHONE_NUMBER_ID": phone["id"], "VAPI_NURSE_ASSISTANT_ID": nurse["id"]})

print()
print(f"Tool server URL:      {PUBLIC_URL}/report")
print(f"Paramedic assistant:  {paramedic['id']}")
print(f"Nurse assistant:      {nurse['id']}  (written to .env)")
print(f"Phone number ID:      {phone['id']}  (written to .env)")
print(f"Phone status:         {phone.get('status')}")
print(f"CALL THIS NUMBER:     {phone.get('number') or '(not assigned yet - re-run in a minute)'}")
print("Restart uvicorn so the server picks up the new .env values.")
