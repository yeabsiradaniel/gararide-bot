# Gara Ride Pilot — Project Design Config

This file persists the Impeccable (`frontend-design`) design context for the team.
Generated during Task 0. Brand tokens live in `docs/brand.md` (the source of truth for
colour/type); this file holds the design *reasoning* that steers copy and later UI.

## Design Context

### Users
Two roles, one gated compound (Ayat 49 ET Village, Addis Ababa). **Drivers** are
neighbours already commuting who share empty seats — they earn nothing by design and
must never feel like taxi operators. **Riders** are verified residents, a meaningful
share of them women whose participation depends on the women-only safety toggles (§19).
Context of use: a cheap Android phone, mobile data, often at 06:45 in low light at a
gate. Amharic is the primary language; every time is shown on both clocks (§23).
The job: find a trusted seat going your way, fast, or fill your empty seats.

### Brand Personality
Neighbourly, trustworthy, calm, non-commercial. Three words: **trusted · neighbourly ·
effortless.** The emotional goal is *reassurance*, not excitement — "I know where you
live" is the trust mechanism (§18), and the design must never feel like a flashy
startup or a ride-hailing app. Warm, plain, honest copy. No hype.

### Aesthetic Direction
Green-forward and clean (brand mark is a green "share" glyph — shared connections).
Light theme favoured over dark. Anti-references: ride-hailing surge/neon aesthetics,
star-rating economies, dark-mode-with-glow "AI slop", gradient text on metrics.
Physical artefacts (standees, packets, decals) carry the visual brand in Phase 1;
the Telegram bot is message + inline-keyboard only.

### Design Principles
1. **Every screen answers "find a seat, or trust the person in it" — or it is cut (§28).**
2. **Show, don't ask** — pre-fill the locked origin and pre-tick common drop-offs;
   never make someone answer a question with one possible answer (§12).
3. **Over-specify the trip card** — plate, tower, exact bay, exact price, both clocks.
   Every detail removes a 06:50 phone call and works offline on a lock screen (§20).
4. **Price on every view, both sides, every time (§12/§13). Tower only — never floor (§18).**
5. **Never show an empty result** — near-misses, social proof, post-a-request,
   notify-me. A thin market must never feel empty (§8).
6. **Reassure, don't dazzle.** Trust comes from in-person verification, not UI polish;
   copy and colour stay warm and plain, never neon or commercial.

## Impeccable steering commands available
`/critique /clarify /simplify /polish /harden /onboard` and others are provided by the
`tommasoronchin.impeccable-universal` extension (status-bar ✨). For Phase 1 the
highest-value ones are **/clarify** and **/harden** on the Amharic copy in
`gararide/strings_am.py`, and **/critique** + **/polish** on the printed QR standees and
windshield packets. The full visual-design surface arrives with the Phase 2 mini app.
