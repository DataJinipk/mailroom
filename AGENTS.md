# AGENTS.md — Mailroom Project Rules

Mailroom is a Python CLI tool for Kettlebird Tea's *The Steep Club* newsletter, built test-first across Steps 0–26 (Chapters 13–15 of *The AI Agent Factory*).

## How I learn
- **Current lesson:** Step 4 (`13.11 Tests first`).
- Only use Python concepts and tooling introduced up to the current step.

## Core Rules
- **No real emails:** Never send email to real people or real addresses. Practice sends only target `@resend.dev` or `http://localhost:4000`.
- **Honest predictions:** Record every step's prediction in `notes/predictions.md` **before** running code, and never edit a prediction afterwards.
- **Plain English:** Keep CLI output, docs, and commit messages clear and concise.
- **Behaviors first:** I give the expected answers, you write them as checks, show them failing, then write the code.
- **Pure dates:** Never read today's date inside the logic. Pass the run date in.
- **Errors first:** When something breaks, show me the full error before changing anything.
