# Design Tokens — derived from nerdy.com

Captured live with Playwright (`design/nerdy-home.png`, `scripts/tokens.mjs`). These are the
*real* computed styles from Nerdy's homepage, so the product reads as a first-party Nerdy tool.

## Brand read
Nerdy's homepage is a **dark, premium "Live + AI" canvas**: deep indigo background, a luminous
magenta→violet→cyan gradient wordmark, generous whitespace, soft-glow cards. The feeling is
*calm futuristic confidence* — exactly the tone an autonomous sales agent should project.

## Color
| Token | Value | Use |
|---|---|---|
| `--bg` | `#0F0928` | App canvas (deep indigo) |
| `--bg-2` | `#161C2C` | Panels / raised surfaces |
| `--bg-3` | `#202344` | Cards, inputs |
| `--surface-line` | `rgba(255,255,255,0.08)` | Hairline borders |
| `--text` | `#FFFFFF` | Primary text |
| `--text-dim` | `rgba(255,255,255,0.64)` | Secondary text |
| `--accent` | `#17E2EA` | Electric cyan — primary action / live state |
| `--accent-2` | `#8B5CFF` | Violet — secondary |
| `--accent-3` | `#FF4FD8` | Magenta — highlights |
| `--ok` | `#28E0A8` | Success / promote |
| `--warn` | `#FFC53D` | Escalate / caution |
| `--bad` | `#FF5C7A` | Retire / failure |
| `--grad` | `linear-gradient(100deg,#FF4FD8,#8B5CFF,#17E2EA)` | Wordmark, hero, active rails |

## Type
- **Display / UI:** `Poppins` (400/500/600/700) — Nerdy's primary face.
- **Body / data:** `Karla`, fallback to system sans.
- **Mono (transcripts, logs):** `"JetBrains Mono", ui-monospace`.
- Scale: 12 / 14 / 16 / 20 / 28 / 40 / 64. Hero uses gradient text at 40–64.

## Shape & depth
- Radius: cards `20px`, controls `12px`, pills `999px`.
- Elevation: `0 8px 40px rgba(0,0,0,0.45)` plus a 1px inner light line on cards.
- Buttons: pill or 12px radius, `font-weight:600`, accent fill with subtle glow
  `box-shadow:0 0 24px rgba(23,226,234,0.35)` on primary.
- Motion: 150–250ms ease-out; "live" elements get a slow cyan pulse.

## Voice-product specifics
- **Live state** = cyan pulse + animated waveform. **Listening** vs **speaking** color-coded
  (cyan = agent speaking, violet = prospect speaking).
- Decision events render as a vertical timeline rail using `--grad`.
- KPI deltas: green up / red down chips, never ambiguous.
