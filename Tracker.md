
---

### `Tracker.md` (all complete + journey)

```markdown
# Webhook Verification — Solo Prototype Tracker
### Assignment 1: Independent Learning & Blocker Log — The Meridian Pivot

**Tool:** Webhook verification (HMAC) → async check-in (Redis queue + webhook)  
**Time-box:** Day 1–2 (+ pivot completion)  
**Rule:** No teammate/instructor technical help for implementation.

---

## Original checklist (HMAC prototype)

- [x] Day 1 10 AM — Understand HMAC-based webhook verification (notes in own words)
- [x] Day 1 6 PM — Build sender script (fake warehouse POST + HMAC signature header)
- [x] Day 2 10 AM — Build receiver endpoint (recompute HMAC, timing-safe compare, accept/reject)
- [x] Day 2 5 PM — Break it on purpose (wrong secret / tampered payload / missing header / replay) + log each
- [x] Journal written up in full sentences, ready to submit
- [x] Prototype demoable end-to-end (valid request accepted, invalid rejected)

---

## Pivot checklist (Solstice Events Co.)

### Domain
- [x] Attendee statuses: not_checked_in / pending / checked_in
- [x] Seed at least 3 test attendees (ATT-001, ATT-002, ATT-003)
- [x] Duplicate-scan protection (already checked_in → no second print job)

### Async print flow (Redis)
- [x] Redis for queue + attendee state (new technology)
- [x] On check-in → set pending + enqueue print job
- [x] Worker simulates badge printer
- [x] Valid success path → mark checked_in
- [x] Late / duplicate callbacks handled safely (only pending → checked_in)

### Webhook security
- [x] Modern signature header: `t=...,v1=...`
- [x] Timestamp tolerance (±5 minutes)
- [x] Timing-safe HMAC verify
- [x] Missing / invalid signature → 401 + log

### Kiosk UI
- [x] Status board for attendees
- [x] Check-in by attendee ID
- [x] Shows Pending until confirmation (spinner + colour)
- [x] Shows already checked in on duplicate
- [x] QR codes on page for ATT-001 / ATT-002 / ATT-003

### Demo / ship
- [x] Happy path works end-to-end
- [x] Duplicate scan works
- [x] Public HTTPS (Render)
- [x] GET /checkin/{id} for QR scans
- [x] Admin reset for demo re-runs (`POST /admin/reset`)
- [x] README reflects full journey
- [x] Tracker.md updated
- [x] Blocker log completed

---

## Journey summary

1. **HMAC fundamentals** — generate/verify, timing-safe compare, tests  
2. **Warehouse sender + webhook** — valid accept / invalid reject  
3. **Modern signatures** — timestamp + replay protection  
4. **Meridian pivot** — Solstice async kiosk: Redis queue, pending UI, webhook callback  
5. **Deploy** — Render HTTPS; in-process worker (free tier has no Background Worker)  
6. **Demo polish** — QR codes, spinner UI, admin reset  

---

## Blocker Journal

> Full entries also in blocker.log

### Entry 1
- **Timestamp:** 2026-08-17 ~15:37
- **What I was trying to do:** Run `pytest -v --cov=hmac_service`
- **Exact error / symptom:** `unrecognized arguments: --cov=hmac_service` even with pytest-cov installed
- **Resources checked:** pip list, `which pytest`, Python import paths
- **What fixed it:** System pytest was on PATH; used `python -m pytest` so the venv plugins loaded
- **Time spent stuck:** ~25 minutes

### Entry 2
- **Timestamp:** 2026-08-17 ~16:02
- **What I was trying to do:** Run warehouse sender against the receiver
- **Exact error / symptom:** HTTP 404 `{"detail":"Not Found"}` on `/webhook`
- **Resources checked:** FastAPI routes, sender URL
- **What fixed it:** Implemented `/webhook` endpoint; sender then received 200/401 as expected
- **Time spent stuck:** ~15 minutes

### Entry 3
- **Timestamp:** 2026-08-17 ~19:13
- **What I was trying to do:** First `git push` to GitHub
- **Exact error / symptom:** rejected non-fast-forward / divergent branches
- **Resources checked:** git status, git pull docs
- **What fixed it:** `git pull --rebase origin main` then push; removed accidentally committed `.env`
- **Time spent stuck:** ~20 minutes

### Entry 4
- **Timestamp:** 2026-08-20 ~13:17
- **What I was trying to do:** Run Redis printer worker (`python sender.py`)
- **Exact error / symptom:** `redis.exceptions.TimeoutError: Timeout reading from socket` on BRPOP
- **Resources checked:** redis-py docs, redis-cli ping
- **What fixed it:** `socket_timeout=None` on Redis client; catch TimeoutError in `pop_print_job`
- **Time spent stuck:** ~20 minutes

### Entry 5
- **Timestamp:** 2026-08-20 (Railway attempt)
- **What I was trying to do:** Deploy free tier on Railway
- **Exact error / symptom:** Free-tier deploys blocked in region during peak hours (EU)
- **Resources checked:** Railway status banner / docs
- **What fixed it:** Switched target to Render for HTTPS demo
- **Time spent stuck:** ~30–40 minutes (including wait/decision)

### Entry 6
- **Timestamp:** 2026-08-20 (Render setup)
- **What I was trying to do:** Add Redis and a background worker on Render
- **Exact error / symptom:** No clear “Redis” product in New menu; Background Worker requires paid plan
- **Resources checked:** Render docs, dashboard UI
- **What fixed it:** Upstash/Key Value for Redis URL; in-process worker thread inside FastAPI (Option B)
- **Time spent stuck:** ~45 minutes

### Entry 7
- **Timestamp:** 2026-08-20 ~11:46
- **What I was trying to do:** Deploy after adding admin reset
- **Exact error / symptom:** `IndentationError` in `app.py` (broken `admin_reset` / mount order)
- **Resources checked:** Local `py_compile`, traceback from Render logs
- **What fixed it:** Restructured end of `app.py` (function body intact; mount and `/` at module level)
- **Time spent stuck:** ~25 minutes

### Entry 8
- **Timestamp:** 2026-08-21
- **What I was trying to do:** Call `/admin/reset` from the browser
- **Exact error / symptom:** `{"detail":"Method Not Allowed"}`
- **Resources checked:** FastAPI method routing, OpenAPI `/docs`
- **What fixed it:** Use POST with `X-Admin-Token` header (browser address bar sends GET)
- **Time spent stuck:** ~10 minutes

---

## Resources consulted (running list)

- Python `hmac` / `hashlib` docs  
- FastAPI docs (headers, startup, static files)  
- Stripe / GitHub style webhook signature patterns  
- redis-py blocking commands (BRPOP) and socket timeout behaviour  
- Railway free-tier region limits  
- Render free tier (Web Service vs Background Worker)  
- Upstash Redis connection URLs  

---

## Final notes

**Functional correctness**  
- Valid HMAC callbacks accepted; invalid/missing/expired rejected  
- Check-in is async: UI stays pending until confirmation  
- Duplicate scan returns 409 and does not enqueue a second print  
- Live at https://solstice-checkin.onrender.com  

**What I would do differently with more time**  
- Dedicated worker process in production  
- Stronger admin auth  
- Automated e2e tests against the full Redis path on CI  
- Standard Webhooks-compatible header profile  