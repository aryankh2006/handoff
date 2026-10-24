# Handoff — Project Context

## Event
c0mpiled-16 hackathon at UCSD, Oct 24 2026. Theme: "Invisible Interfaces" (voice, sensors, live data, agents — no traditional screens). We are entering the DISPATCH track (use live information to coordinate the movement of physical things). Judges are YC founders. Submissions due 6:30 PM, top 5 demo live at 7:45 PM.

## The problem
- When ERs are crowded, ambulance crews "wait on the wall" with their patient until ER staff take over. While waiting, that ambulance can't answer new 911 calls.
- California AB 40 requires a local offload standard of no more than 30 minutes, 90% of the time; the state (EMSA) monitors monthly offload times and reports hospitals that exceed it.
- San Diego standard: 30 min. EMSA Jan 2026 data: UC San Diego Medical Center 90th-percentile offload 1:21 (81 min) over 1,331 transports; Paradise Valley Hospital 1:13.
- Statewide study of ~5.9M offloads: mean offload time 42.8 min; nearly half of local EMS agencies averaged above 30 min.
- Longer offload times are associated with higher 30-day risk of death for chest-pain patients.
- A major contributor: ERs get surprised when several ambulances arrive at once.

## Our solution
Handoff is an AI early-warning system for ERs:
1. Paramedics just talk (hands-free phone call, no app): "Medic 14, 62-year-old, chest pain, stable, 12 minutes out."
2. AI extracts the details; the ER board shows each incoming ambulance with an ETA countdown.
3. Surge detection: 3+ incoming ambulances within 20 min -> AI phones the ER charge nurse to staff the ambulance door.
4. Handoff times are logged automatically against the 30-minute standard (compliance stats).
Humans make all medical decisions; the AI only communicates, predicts, and logs. Simulated patients only — no real PHI.

## Who pays
Hospitals — they are now publicly reported under AB 40 and must file offload-reduction protocols.

## Competition and our edge
- Pulsara (app-based EMS/hospital communication platform; case studies: Ambulance Victoria ~5 min faster off stretchers; Cy-Fair FD offload 45 -> ~10 min with a new protocol).
- FirstWatch (real-time transport/offload tracking, e.g., Las Vegas), ReddiNet (CA hospital alerts), San Diego County digital prearrival notification pilot (Mar 2026).
- Our edge: voice-only for paramedics (no app), AI-first, proactively detects surges and calls the charge nurse, built around the AB 40 30-minute standard.
- Honest limit: we don't create ER beds; we help ERs prepare earlier and cut minutes per handoff.

## Pitch line
"UCSD Medical Center: 81 minutes. Legal limit: 30. Handoff lets paramedics just talk, warns the ER before the wave hits, and gets ambulances back on the street."

## Judge Q&A (short answers)
- "Isn't this Pulsara?" -> Pulsara is a great app-based messaging tool; we're app-free and AI-first — paramedics talk, our AI spots surges and calls the nurse automatically.
- "Privacy?" -> Demo uses simulated patients; production would need HIPAA-compliant voice and storage and a BAA with providers.
- "Who pays?" -> Hospitals under AB 40 pressure; per-hospital subscription.
- "Medical risk?" -> AI makes no clinical decisions; it only relays, predicts arrivals, and logs times.

## Sources
- CA EMSA APOT Exceedance Reports (Jan/Feb 2026): https://emsa.ca.gov/wp-content/uploads/sites/71/2026/02/February-2026-APOT-Exceedance-Report-to-the-Commission-on-EMS.pdf
- AB 40 text: https://legiscan.com/CA/text/AB40/2023
- CA offload patterns study: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11650417/
- Pulsara offload/mortality study post: https://www.pulsara.com/blog/study-shows-correlation-between-ambulance-offload-times-and-30-day-risk-of-death
- Pulsara Cy-Fair case study: https://www.pulsara.com/blog/case-study-cy-fair-fire-department-cuts-ems-offload-times-by-77-percent
- FirstWatch Las Vegas: https://firstwatch.net/?p=14760
- San Diego County EMS: https://www.sandiegocounty.gov/content/sdc/ems.html
