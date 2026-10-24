# Demo script (~45s)

**Before:** `curl -X POST localhost:8000/reset`. Board full-screen on projector. Nurse phone on loud.

| Who | Role |
|-----|------|
| Person 1 | Paramedic caller #1 (live call) |
| Person 4 | Narrator |
| Person 2 | Runs `scripts/test_surge.sh` / extra calls on cue |
| Person 3 | Plays the **charge nurse** (their phone = `NURSE_PHONE`) |

1. **Narrator:** "A paramedic is 8 minutes out. They just call."
2. **Person 1** calls the Vapi number on speaker:
   "Medic 12, 67-year-old male, chest pain, critical, ETA 8 minutes."
   → Card appears, red, countdown running.
3. **Narrator:** "Now it's Friday night. Two more crews call in."
   → Person 2 runs `bash scripts/test_surge.sh` (or two more live calls).
4. **Red SURGE banner** appears. **Person 3's phone rings** on stage.
   Person 3 answers on speaker: AI reads the surge warning. Person 3: "Copy, thanks."
5. **Narrator** clicks "Arrived" then "Handed off" on a card, points at stats strip:
   "Every handoff is timed against the 30-minute legal limit."

**Fallbacks:** inbound call fails → use board "Manual report" form. Nurse call fails → call log
still shows the warning (dry run).
