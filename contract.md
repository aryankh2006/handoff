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
### `POST /reset`        → clears everything, reloads 2 seed ambulances. Returns `/state`.

## Surge rule
- `surge = true` when **≥ 3** ambulances have `status == "incoming"` **and** remaining ETA `<= 20` min,
  where remaining ETA = `eta_min` − minutes since `reported_at` (the same live countdown the board shows).
- An `incoming` ambulance more than **15 min past** its ETA (never marked arrived) is stale and does not count.
- When a surge is detected, place **one** outbound Vapi call to the charge nurse, then a **10-minute cooldown**.
- Outbound call: `POST https://api.vapi.ai/call` with `assistantId=VAPI_NURSE_ASSISTANT_ID`,
  `phoneNumberId=VAPI_PHONE_NUMBER_ID`, `customer.number=NURSE_PHONE`, and the warning text as
  `assistantOverrides.firstMessage` (also `assistantOverrides.variableValues.surge_message`).
- If any Vapi env var is missing → **dry run**: only append to `call_log`.

## Stats
- Handoff minutes = `handoff_at - arrived_at` (only ambulances with both set).
- `avg_handoff_min`, `p90_handoff_min` (rounded to 1 decimal, `0` when no data),
  `over_30_count` (handoffs > 30 min — California AB 40 standard), `total` (number of completed handoffs).
