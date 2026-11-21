# Mailroom Predictions (`notes/predictions.md`)

> Rule: Write each prediction **before** running the code, and never change it afterwards.

## Step 0 — Newsletter & Audience
- **Newsletter:** Kettlebird Tea — *The Steep Club* (monthly tea subscription box).
- **Audience:** Waitlist subscribers split into three groups: `tea-curious`, `gift-buyers`, and `daily-drinkers`.
- **Prediction:** `uv init` creates a minimal Python project (`pyproject.toml`, `main.py`, `.python-version`, `.gitignore`, `README.md`) with a local `.git` repository ready to push to GitHub.

## Step 1 — Count Subscribers (`data/subscribers.csv`)
- **Prediction (written before code):**
  - Total subscribers: `24`
  - By group: `tea-curious: 8`, `gift-buyers: 8`, `daily-drinkers: 8`
  - By consent: `waitlist form: 24`

## Step 2 — Dates (`--since-days`, `--since`, `first_monday_of_next_month`)
- **Prediction (written before code):**
  - With `--run-date 2026-11-20` and `--since-days 30` (cutoff `2026-10-21` inclusive): `7` subscribers (`Amara` on `2026-10-21` is included; `Hiroshi` on `2026-10-20` is excluded).
  - With `--since 2026-10-01`: `12` subscribers.
  - `first_monday_of_next_month`:
    - `2026-11-20` -> `2026-12-07`
    - `2026-12-07` -> `2027-01-04`
    - `2026-12-31` -> `2027-01-04`
