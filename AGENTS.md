# AGENTS.md — Mailroom Project Rules

Mailroom is a Python CLI tool for Kettlebird Tea's *The Steep Club* newsletter, built test-first across Steps 0–26 (Chapters 13–15 of *The AI Agent Factory*).

## How I learn
- **Current lesson:** Step 24 (`15.10 After the merge`).
- Only use Python concepts and tooling introduced up to the current step.

## Core Rules
- **No real emails:** Never send email to real people or real addresses. Practice sends only target `@resend.dev` or `http://localhost:4000`.
- **Honest predictions:** Record every step's prediction in `notes/predictions.md` **before** running code, and never edit a prediction afterwards.
- **Plain English:** Keep CLI output, docs, and commit messages clear and concise.
- **Behaviors first:** I give the expected answers, you write them as checks, show them failing, then write the code.
- **Pure dates:** Never read today's date inside the logic. Pass the run date in.
- **Errors first:** When something breaks, show me the full error before changing anything.
- **Test authority:** I decide the test cases and their answers. Never change an expected answer to make a test pass.
- **Length rule:** Subject and preview length count what Python's `len()` counts.
- **Module boundaries:** One module per job. Only the commands module prints.
- **Types:** Every function has type hints, and `pyright` must be clean.
- **Domain objects:** Pass `Subscriber` and `Issue` objects around, never raw rows or raw text.
- **Validation boundary:** Data from outside goes through the model before any code uses it.
- **Shape vs meaning:** The model checks the shape. Our own rules check the meaning.
- **Error design:** Report every problem with its row. No traceback for a user's mistake.
- **JSON boundary:** JSON read from a file is outside data: it goes through a model too.
- **Environment & localhost guard:** The key and the address come from the environment. Sending works only against localhost.
- **HTTP status handling:** Handle each status on purpose. Never retry a 4xx.
- **Concurrency:** Send with a limit on how many at once.
- **Retries & client choice:** Retry only what can succeed later, and every send has an idempotency key. Using `httpx.AsyncClient` directly for explicit concurrency, status handling, and idempotency headers.
- **Branch & PR workflow:** Every change goes on a branch and arrives as a pull request.
- **PR evidence:** A pull request shows its evidence (`pytest`, `pyright`, `mailroom check`).
- **CI gate:** The checks must pass before a merge.
- **Reviewer guide:** Reviewers read `REVIEW.md`.
- **Revert & regression:** Undo a bad merge with a revert pull request, then add the test that would have caught it.
