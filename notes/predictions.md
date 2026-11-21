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

## Step 3 — Reading an Error (`2026-02-30`)
- **Prediction (written before running):**
  - Changing Jonas Berg's `joined_on` to `2026-02-30` will raise `ValueError: day is out of range for month` in `date.fromisoformat(joined_raw)` inside `count_subscribers` (`mailroom.py`).

## Step 4 — Real Tests (`pytest`)
- **Prediction (written before running `pytest`):**
  - Migrating the 5 behavior checks from `checks.py` into `tests/test_subscribers.py` and removing `checks.py` will run `5` tests and report `5 passed`.

## Step 5 — Subject Line Checks (`check_subject`)
- **Prediction (written before code):**
  - `issues/issue-01.md` (`"The Steep Club opens Monday"`, 26 chars): valid (0 problems).
  - Exactly 50 chars: valid (0 problems).
  - 51 chars: fails (exceeds 50-character limit).
  - Empty `Subject: ` or whitespace-only `Subject:   `: fails (subject is empty).
  - Missing `Subject:` on line 1: fails (missing Subject line).

## Step 6 — Full Issue Rules & `check` CLI
- **Prediction (written before code):**
  - `issues/issue-01.md` satisfies all 5 rules in `docs/email-rules.md` -> prints `OK` and exits `0`.
  - Bad issues (long preview > 90 chars, missing `{{first_name}}`, 0 or 2 links, missing footer lines) return problems with line numbers and exit `1`.

## Step 7 — Emoji Length (`len()`)
- **Prediction (written before code):**
  - `"👍🏽 Thanks for joining"` has `len() == 20` (`👍` + `🏽` = 2 code points + 18 chars), which is `<= 50` and passes.
  - A subject with 49 ASCII chars + `"👍🏽"` has `len() == 51` and fails the 50-char limit under Python `len()`.
