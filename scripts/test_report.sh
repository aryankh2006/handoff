#!/usr/bin/env bash
# POST one plain report, then one in Vapi tool-call format.
BASE="${BASE:-http://localhost:8000}"
set -e

echo "== plain report =="
curl -sS -X POST "$BASE/report" -H 'Content-Type: application/json' \
  -d '{"unit":"Medic 12","age":67,"complaint":"chest pain","acuity":"critical","eta_min":8}'
echo; echo

echo "== Vapi tool-call format =="
curl -sS -X POST "$BASE/report" -H 'Content-Type: application/json' \
  -d '{"message":{"type":"tool-calls","toolCalls":[{"id":"call_test_1","type":"function","function":{"name":"submit_report","arguments":{"unit":"Medic 4","age":29,"complaint":"ankle injury","acuity":"stable","eta_min":25}}}]}}'
echo
