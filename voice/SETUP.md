# Vapi setup (Person 1)

Goal for the **4:15 PM checkpoint**: a real phone call creates a card on the board.

## Fast path (does steps 2–6 for you)
With `VAPI_API_KEY` and `PUBLIC_URL` in `.env`:
```bash
python voice/setup_vapi.py
```
It creates or updates the tool, both assistants, and a free phone number, then writes
`VAPI_PHONE_NUMBER_ID` and `VAPI_NURSE_ASSISTANT_ID` into `.env`. Run it again whenever the ngrok
URL or a prompt changes. Restart uvicorn afterwards. The manual steps below are the fallback.

## 1. Run the server and ngrok
```bash
source .venv/bin/activate
uvicorn server.main:app --reload --port 8000
ngrok http 8000          # in a second terminal
```
Copy the `https://....ngrok-free.app` URL. Put it in `.env` as `PUBLIC_URL` (no trailing slash).
Check: open `{PUBLIC_URL}/state` in a browser — you should see JSON.

## 2. Create the `submit_report` tool
Vapi dashboard → **Tools** → Create Tool → Function.
- Name `submit_report`, description and parameters from `submit_report_tool.json`.
- Server URL: `{PUBLIC_URL}/report` (paste the real ngrok URL).
- Add the request-start / request-failed messages from the JSON.

## 3. Create the paramedic assistant
Vapi → **Assistants** → Create → Blank.
- Name "Handoff Intake". Paste first message + system prompt from `paramedic_assistant_prompt.md`.
- Tools tab: attach `submit_report`.
- Test with the "Talk" button in the dashboard first — a card should appear on the board.

## 4. Create the nurse assistant
- Name "Handoff Nurse Alert". Paste from `nurse_assistant_prompt.md`.
- Copy its **Assistant ID** → `.env` `VAPI_NURSE_ASSISTANT_ID`.

## 5. Phone number
Vapi → **Phone Numbers** → Create (free Vapi number).
- Inbound: assign assistant "Handoff Intake".
- Copy the **Phone Number ID** → `.env` `VAPI_PHONE_NUMBER_ID`.

## 6. Keys
- Vapi → **API Keys** → private key → `.env` `VAPI_API_KEY`.
- `.env` `NURSE_PHONE` = phone of whoever plays the charge nurse, E.164 (`+15551234567`).
- Restart uvicorn after editing `.env`.

## 7. Verify
- Call the Vapi number, give a report → card appears.
- `bash scripts/test_surge.sh` → nurse phone rings (call log shows no `[DRY RUN]`).
- If ngrok restarts, the URL changes: update the tool server URL in Vapi and `PUBLIC_URL`.

## Troubleshooting
- Tool never hits server → check uvicorn logs for `POST /report`; check the ngrok URL in the tool.
- Call log says `[VAPI ERROR 4xx]` → uvicorn console prints Vapi's response body.
- Free Vapi numbers may not dial international numbers; use a US number for `NURSE_PHONE`.
