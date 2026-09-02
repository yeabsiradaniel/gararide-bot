# Gara Ride Brand Reference

Source: `C:\Users\yeabs\OneDrive\Documents\bike\rework\gara_bike\assets\images\Logo2.png`
Captured: 2026-09-02 (Task 0). Colours sampled pixel-exact from the logo with Pillow;
values marked *(derived)* are not in the file — they are neutrals tinted toward the
brand hue per the Impeccable `frontend-design` guidance (never pure black/white).

## The mark

A **"share" / network glyph**: three ring-nodes joined by connectors — literally
shared connections between people. It is a pure icon with **no wordmark**, so the
file encodes no typeface (see Type below). It sits on transparency and is a single
vertical gradient, deep green at the edges rising to a bright lime highlight through
the centre.

## Colours

| Role | Hex | Where it is used |
|---|---|---|
| Primary | `#0DA200` | Deep brand green. Logo base, primary buttons, links, the QR-standee field. |
| Secondary | `#53C830` | Mid gradient green (the logo's "heart"). Hover/secondary fills, the everyday green. |
| Accent | `#9AEF61` | Light lime highlight — the "connection glow". Success states, emphasis, badges. |
| Sunset accent | `#FF7A45` *(chosen, not sampled)* | Warm counterpoint to the green. Sparing use only — a single CTA highlight, a moment of delight, warmth on a poster. Never a large field or body text. |
| Ink / text | `#0B2E08` *(derived)* | Near-black tinted with the brand green. Body text on light surfaces. |
| Surface | `#EEFDE3` *(derived from logo's lightest wash)* | Light background wash / cards. |
| Paper | `#FBFEF9` *(derived)* | Off-white page background, faintly green-tinted (not pure `#fff`). |

**Brand gradient (the logo's own):** linear `#0DA200 → #53C830 → #9AEF61`.
Use it sparingly — the mark, hero panels on the standees/posters, not body UI.

### Contrast notes (WCAG)
- `#0B2E08` on `#FBFEF9` / `#EEFDE3` → strong contrast, safe for body text.
- `#0DA200` with **white** text passes AA for large/bold text and buttons; do **not**
  use `#0DA200` as small body text on white (borderline). Reserve the bright
  `#9AEF61`/`#53C830` for fills and accents, never as text on light backgrounds.
- `#FF7A45` (sunset) is an accent, not a text colour — fine on white for large/bold or
  as a fill with dark ink; avoid it as small body text on white.
- On dark backgrounds the light greens (`#9AEF61`, `#53C830`) carry the mark; the
  deep `#0DA200` goes muddy on black. **The logo works on light and dark, but favour
  light** — a compound/transport brand reads as trustworthy and legible, not neon.

## Type

**Wordmark typeface: none in the file** — the logo is icon-only. A wordmark decision
is still open and belongs to the founder. Starting recommendations (Impeccable rules:
avoid Inter/Roboto/Arial/system defaults):

- **Amharic / ግዕዝ (primary language):** **Noto Sans Ethiopic** — well-hinted, renders
  the ግዕዝ script cleanly at small sizes on cheap phones, which is the binding
  constraint (trip cards read at 06:45 on a lock screen). Fallback: Abyssinica SIL.
- **Latin pairing (wordmark / numerals like "85 ETB"):** a distinctive grotesque with
  a warm, human feel — e.g. **Hanken Grotesk** or **Bricolage Grotesque** for the
  wordmark. Confirm before printing; this is a starting point, not a decision.

## Where this applies in Phase 1

Phase 1 is a Telegram bot — Telegram controls message rendering, so there is **no CSS
surface** in the bot itself. The brand lives in the **physical + copy** layer:

- QR standees for the onboarding desk and lift lobbies (execution plan §2 print budget)
- Windshield packets, elevator posters, lobby banner, vehicle decals & carpool passes
- Emoji and tone in `gararide/strings_am.py` — green-forward, warm, neighbourly.
  The "share" framing (§28: *share the empty seat*) matches the mark. Lean on 🚗 ✅ and
  the green palette; avoid loud/neon tone that undercuts the trust positioning.

## Where this applies later

- The Phase 2 mini app (the real visual-design payoff — full palette + type system)
- Any admin dashboard
