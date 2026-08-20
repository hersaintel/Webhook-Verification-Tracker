# Webhook Verification — Solo Prototype Tracker
### Assignment 1: Independent Learning & Blocker Log — The Meridian Pivot

**Tool:** Webhook verification (HMAC signature)
**Time-box:** Day 1–2, spread across both days
**Rule:** No teammate/instructor technical help from here on.

---

## Progress Checklist

[✓] Day 1 10 AM — Understand HMAC-based webhook verification (Stripe/GitHub docs), notes in own words

[✓] Day 1 6 PM — Build sender script (fake warehouse POST + HMAC signature header)

[✓] Day 2 10 AM — Build receiver endpoint (recompute HMAC, timing-safe compare, accept/reject)

[✓] Day 2 5 PM — Break it on purpose (wrong secret / tampered payload / missing header / replay) + log each

[✓] Journal written up in full sentences, ready to submit

[✓] Prototype demoable end-to-end (valid request accepted, invalid rejected)

---

## Blocker Journal

> Blockers added to blocker.log

### Entry #
- **Timestamp:**
- **What I was trying to do:**
- **Exact error / symptom:**
- **Resources checked:**
- **What fixed it (or didn't):**
- **Time spent stuck:**

---

## Resources Consulted (running list)

-

## Final Notes

- Functional correctness — does it actually accept valid / reject invalid?
- What I'd do differently with more time:

# Project Tracker – Webhook Verification → Solstice Check-in

## Original scope
- HMAC-signed webhook verification
- Valid request accepted, invalid rejected
- Timing-safe compare + logging

## Completed (pre-pivot)
- [x] hmac_service (generate/verify)
- [x] Unit + e2e tests
- [x] Sender + /webhook
- [x] Modern signature format with timestamp / replay window

### Local 
- [x] Redis + 3 attendees
- [x] Check-in → pending → enqueue
- [x] Worker callback with HMAC
- [x] Duplicate protection
- [x] Kiosk UI local

### Public demo
- [ ] requirements.txt + start commands
- [ ] Deploy web + worker on Railway/Render
- [ ] Redis add-on + env vars
- [ ] GET /checkin/{id} for QR scans
- [ ] Public HTTPS URL working
- [ ] QR codes for ATT-001/002/003
- [ ] Phone test of full flow
- [ ] README + tracker.md

## Pivot (Solstice Events Co.)
Client deprecates synchronous badge-printer API.
Required: async print via queue + webhook callback; UI stays Pending until confirmation; duplicate scan must not print a second badge.

## Post-pivot
- [x] Redis queue + attendee state
- [x] Check-in API + duplicate protection
- [x] Worker (printer simulator) + HMAC callback
- [x] Kiosk UI (local)
- [ ] Railway HTTPS deploy
- [ ] QR codes for remote demo
- [ ] Final README reflecting full journey

## Blockers
- Check blocker.log for details
