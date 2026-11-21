# REVIEW.md — Mailroom Code Review Checklist

Reviewers (human and automated) check every pull request against these rules from `AGENTS.md`:

1. **Module boundaries:** One module per job; only `src/mailroom/commands.py` calls `print()`.
2. **Types:** Every function has full type hints and `uv run pyright` reports `0 errors`.
3. **Domain objects & validation:** External CSV/JSON data passes through `Subscriber`, `Issue`, `PlannedEmail`, or `SendPlan` before use.
4. **Pure dates:** Business logic never calls `date.today()`; `run_date` is passed in from `commands.py`.
5. **Sending safety:**
   - `RESEND_API_URL` must be `localhost` or `127.0.0.1`.
   - Recipients must end with `@example.com` or `@resend.dev`.
   - `4xx` responses are never retried; retries only happen on `5xx`/network errors with `Idempotency-Key`.
6. **Issue rules:** `Subject` <= 50 chars (`len()`), `Preview` <= 90 chars (`len()`), `{{first_name}}` greeting, exactly 1 `https://` link, and plain-text footer.
7. **Tests & evidence:** New behavior is covered by `pytest` tests and real command outputs are included in the PR description.
