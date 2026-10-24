# Handoff Data Contract

**Single source of truth.** Server, board, voice tool, and test scripts all follow this file.
Do not change it without telling the whole team first.

## Ambulance object

| field         | type                                         | notes                              |
|---------------|----------------------------------------------|------------------------------------|
| `id`          | string (uuid4)                               | set by server                      |
| `unit`        | string                                       | e.g. `"Medic 12"`                  |
| `age`         | int                                          | patient age in years               |
| `complaint`   | string                                       | e.g. `"chest pain"`                |
| `acuity`      | `"stable"` \| `"critical"`                   |                                    |
| `eta_min`     | int                                          | minutes from `reported_at`         |
| `reported_at` | ISO 8601 string (UTC)                        | set by server                      |
| `status`      | `"incoming"` \| `"arrived"` \| `"handed_off"` | starts `"incoming"`                |
| `arrived_at`  | ISO 8601 string \| null                      | set by `POST /arrive/{id}`         |
| `handoff_at`  | ISO 8601 string \| null                      | set by `POST /handoff/{id}`        |

```json
{
  "id": "6f1c2a4e-1b2c-4d5e-8f90-123456789abc",
  "unit": "Medic 12",
  "age": 67,
  "complaint": "chest pain",
  "acuity": "critical",
  "eta_min": 8,
  "reported_at": "2026-10-24T22:10:00+00:00",
  "status": "incoming",
  "arrived_at": null,
  "handoff_at": null
}
```

## Endpoints

### `POST /report`
Two accepted body formats:

1. **Plain JSON** → returns the ambulance object.
   ```json
   {"unit": "Medic 12", "age": 67, "complaint": "chest pain", "acuity": "critical", "eta_min": 8}
   ```
2. **Vapi tool call** (arguments in `message.toolCalls[].function.arguments`, object or JSON string;
   `message.toolCallList` also accepted) → returns Vapi tool result format:
   ```json
   {"results": [{"toolCallId": "call_abc", "result": "Got it. Medic 12, 67 year old, chest pain, critical, ETA 8 minutes. The ER has been notified."}]}
   ```

Invalid `acuity` defaults to `"stable"`; missing/invalid ints default to `0`.

### `GET /state`
```json
{
  "ambulances": [ /* Ambulance objects, newest first */ ],
  "surge": false,
  "call_log": [{"time": "ISO string", "to": "+15551234567", "message": "SURGE WARNING: ..."}],
  "stats": {"avg_handoff_min": 22.5, "p90_handoff_min": 41.0, "over_30_count": 1, "total": 2}
}
```

### `POST /arrive/{id}`  → sets `status="arrived"`, `arrived_at=now`. Returns ambulance. 404 if unknown.
### `POST /handoff/{id}` → sets `status="handed_off"`, `handoff_at=now` (also sets `arrived_at` if missing). Returns ambulance. 404 if unknown.
### `POST /reset`        → clears everything and reloads the simulated seed: 10 completed handoffs (shift history for
the stats), Medic 1 already `arrived` ~32 min ago (demo: click "Handed off" on it), and Medic 3 `incoming`. Returns `/state`.
### `GET|POST /twiml/surge` → TwiML (XML) Twilio fetches when the nurse answers: the latest surge warning, said twice.

## Surge rule
- `surge = true` when **≥ 3** ambulances have `status == "incoming"` **and** remaining ETA `<= 20` min,
  where remaining ETA = `eta_min` − minutes since `reported_at` (the same live countdown the board shows).
- An `incoming` ambulance more than **15 min past** its ETA (never marked arrived) is stale and does not count.
- When a surge is detected, place **one** outbound call to the charge nurse, then a **10-minute cooldown**.
- Outbound call provider, first match wins:
  1. **Twilio** (primary) — if `NURSE_PHONE`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
     and `PUBLIC_URL` are all set: `POST https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Calls.json`
     (basic auth `TWILIO_ACCOUNT_SID:TWILIO_AUTH_TOKEN`) with `From=TWILIO_PHONE_NUMBER`, `To=NURSE_PHONE`,
     `Url={PUBLIC_URL}/twiml/surge`. When the nurse answers, Twilio fetches that URL, which reads the warning
     text aloud twice. (A URL is used because Twilio trial accounts reject inline TwiML.)
  2. **Vapi** (fallback) — if `NURSE_PHONE`, `VAPI_API_KEY`, `VAPI_PHONE_NUMBER_ID` and `VAPI_NURSE_ASSISTANT_ID`
     are set: `POST https://api.vapi.ai/call` with `assistantId`, `phoneNumberId`, `customer.number=NURSE_PHONE`,
     and the warning text as `assistantOverrides.firstMessage`. (Free Vapi numbers are inbound-only, so this
     usually needs a paid or imported number.)
  3. **Dry run** — otherwise, only append to `call_log` with a `[DRY RUN]` prefix.
- Errors never crash the server: the `call_log` entry is prefixed `[TWILIO ERROR …]` or `[VAPI ERROR …]` with
  the provider's reason.
- **Twilio trial limits (demo):** only verified numbers can receive calls, and each call starts with a Twilio
  trial message — the person answering presses any key, then the warning plays.

## Stats
- Handoff minutes = `handoff_at - arrived_at` (only ambulances with both set).
- `avg_handoff_min`, `p90_handoff_min` (rounded to 1 decimal, `0` when no data),
  `over_30_count` (handoffs > 30 min — California AB 40 standard), `total` (number of completed handoffs).
