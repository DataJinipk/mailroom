import argparse
from collections import Counter
import csv
from datetime import date, timedelta
from pathlib import Path
import re

LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def first_monday_of_next_month(run_date: date) -> date:
    """Return the first Monday of the month following run_date."""
    if run_date.month == 12:
        first_of_next = date(run_date.year + 1, 1, 1)
    else:
        first_of_next = date(run_date.year, run_date.month + 1, 1)
    days_until_monday = (0 - first_of_next.weekday()) % 7
    return first_of_next + timedelta(days=days_until_monday)


def count_subscribers(
    csv_path: Path,
    *,
    since: date | None = None,
    since_days: int | None = None,
    run_date: date | None = None,
) -> dict[str, object]:
    """Count total subscribers, group breakdown, and consent breakdown from CSV."""
    cutoff: date | None = since
    if since_days is not None:
        if run_date is None:
            raise ValueError("run_date is required when using since_days")
        days_cutoff = run_date - timedelta(days=since_days)
        cutoff = days_cutoff if cutoff is None else max(cutoff, days_cutoff)

    groups: Counter[str] = Counter()
    consents: Counter[str] = Counter()
    total = 0

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            joined_raw = (row.get("joined_on") or "").strip()
            joined = date.fromisoformat(joined_raw)
            if cutoff is not None and joined < cutoff:
                continue
            if run_date is not None and joined > run_date:
                continue

            total += 1
            group = (row.get("group") or "").strip()
            consent = (row.get("consent") or "").strip()
            if group:
                groups[group] += 1
            if consent:
                consents[consent] += 1

    return {
        "total": total,
        "groups": dict(groups),
        "consents": dict(consents),
    }


def check_subject(text: str) -> list[str]:
    """Validate line 1 Subject: rule (present, non-empty, <= 50 chars via len())."""
    lines = text.splitlines()
    if not lines or not lines[0].startswith("Subject:"):
        return ["Line 1: missing 'Subject: ...' line."]
    subject = lines[0][len("Subject:") :].strip()
    if not subject:
        return ["Line 1: Subject is empty."]
    if len(subject) > 50:
        return [f"Line 1: Subject is {len(subject)} characters (limit is 50)."]
    return []


def check_issue(text: str) -> list[str]:
    """Validate an issue markdown file against docs/email-rules.md."""
    problems = check_subject(text)
    lines = text.splitlines()

    if len(lines) < 2 or not lines[1].startswith("Preview:"):
        problems.append("Line 2: missing 'Preview: ...' line.")
    else:
        preview = lines[1][len("Preview:") :].strip()
        if not preview:
            problems.append("Line 2: Preview is empty.")
        elif len(preview) > 90:
            problems.append(
                f"Line 2: Preview is {len(preview)} characters (limit is 90)."
            )

    if "{{first_name}}" not in text:
        problems.append("Missing '{{first_name}}' greeting.")

    links = LINK_PATTERN.findall(text)
    if len(links) != 1:
        problems.append(f"Expected exactly 1 main link, found {len(links)}.")
    elif not links[0][1].startswith("https://"):
        problems.append(f"Main link must use https:// (found {links[0][1]}).")

    in_code_block = False
    has_getting_line = False
    has_unsub_line = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if not in_code_block:
            if line.startswith("You're getting this because"):
                has_getting_line = True
            if "Unsubscribe: {{unsubscribe_url}}" in line:
                has_unsub_line = True

    if not has_getting_line:
        problems.append(
            "Missing plain-text footer line starting with \"You're getting this because\"."
        )
    if not has_unsub_line:
        problems.append(
            "Missing plain-text footer line containing 'Unsubscribe: {{unsubscribe_url}}'."
        )

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Mailroom newsletter CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subs_parser = subparsers.add_parser("subscribers", help="Count subscribers")
    subs_parser.add_argument(
        "--file",
        type=Path,
        default=Path("data/subscribers.csv"),
        help="Path to subscribers CSV",
    )
    subs_parser.add_argument(
        "--since-days",
        type=int,
        default=None,
        help="Only count subscribers who joined within the last N days",
    )
    subs_parser.add_argument(
        "--since",
        type=date.fromisoformat,
        default=None,
        help="Only count subscribers who joined on or after YYYY-MM-DD",
    )
    subs_parser.add_argument(
        "--run-date",
        type=date.fromisoformat,
        default=None,
        help="Reference date (YYYY-MM-DD); defaults to today",
    )

    next_parser = subparsers.add_parser("next-send", help="Show next monthly send date")
    next_parser.add_argument(
        "--run-date",
        type=date.fromisoformat,
        default=None,
        help="Reference date (YYYY-MM-DD); defaults to today",
    )

    check_parser = subparsers.add_parser("check", help="Check a newsletter issue")
    check_parser.add_argument("issue_path", type=Path, help="Path to issue markdown")

    args = parser.parse_args()

    if args.command == "subscribers":
        effective_run_date = args.run_date if args.run_date is not None else date.today()
        summary = count_subscribers(
            args.file,
            since=args.since,
            since_days=args.since_days,
            run_date=effective_run_date
            if (args.since_days is not None or args.run_date is not None)
            else None,
        )
        print(f"Total subscribers: {summary['total']}")
        print("By group:")
        for name, count in summary["groups"].items():
            print(f"  {name}: {count}")
        print("By consent:")
        for name, count in summary["consents"].items():
            print(f"  {name}: {count}")
        print(
            f"Next send date: {first_monday_of_next_month(effective_run_date).isoformat()}"
        )
        return 0

    if args.command == "next-send":
        effective_run_date = args.run_date if args.run_date is not None else date.today()
        print(first_monday_of_next_month(effective_run_date).isoformat())
        return 0

    if args.command == "check":
        text = args.issue_path.read_text(encoding="utf-8")
        problems = check_issue(text)
        if problems:
            for problem in problems:
                print(problem)
            return 1
        print("OK")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
