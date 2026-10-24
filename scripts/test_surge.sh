#!/usr/bin/env bash
# POST 3 reports with ETA <= 20 to trigger a surge, then show surge flag + call log.
BASE="${BASE:-http://localhost:8000}"
set -e

post() {
  curl -sS -o /dev/null -w "POST /report -> %{http_code}\n" -X POST "$BASE/report" \
    -H 'Content-Type: application/json' -d "$1"
}
post '{"unit":"Medic 21","age":72,"complaint":"stroke symptoms","acuity":"critical","eta_min":6}'
post '{"unit":"Medic 9","age":45,"complaint":"motor vehicle crash","acuity":"critical","eta_min":11}'
post '{"unit":"Medic 15","age":33,"complaint":"abdominal pain","acuity":"stable","eta_min":18}'

sleep 1  # nurse call runs in the background
echo
curl -sS "$BASE/state" | python3 -c 'import json,sys; s=json.load(sys.stdin); print("surge:", s["surge"]); [print("call:", c["to"], "-", c["message"]) for c in s["call_log"]]'
