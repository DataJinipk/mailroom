import argparse
import asyncio
from datetime import date
import json
import os
from pathlib import Path
import sys

from mailroom.dates import first_monday_of_next_month
from mailroom.guard import evaluate_hook_payload
from mailroom.issues import check_issue
from mailroom.models import Issue, SendPlan
from mailroom.sender import SendError, build_send_plan, send_plan
from mailroom.subscribers import count_subscribers, import_signups, load_subscribers


def main(argv: list[str] | None = None) -> int:
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

    import_parser = subparsers.add_parser(
        "import", help="Validate and import new signups CSV"
    )
    import_parser.add_argument("csv_path", type=Path, help="Path to signups CSV")
    import_parser.add_argument(
        "--run-date",
        type=date.fromisoformat,
        default=None,
        help="Reference date (YYYY-MM-DD); defaults to today",
    )
    import_parser.add_argument(
        "--strict",
        action="store_true",
        help="Stop on the first invalid row",
    )

    send_parser = subparsers.add_parser(
        "send", help="Plan or send a newsletter issue to the practice server"
    )
    send_parser.add_argument(
        "issue_path",
        type=Path,
        nargs="?",
        default=None,
        help="Path to issue markdown",
    )
    send_parser.add_argument(
        "--file",
        type=Path,
        default=Path("data/subscribers.csv"),
        help="Path to subscribers CSV",
    )
    send_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write outbox/plan.json without sending",
    )
    send_parser.add_argument(
        "--plan-out",
        type=Path,
        default=Path("outbox/plan.json"),
        help="Output path for --dry-run plan JSON",
    )
    send_parser.add_argument(
        "--from-plan",
        type=Path,
        default=None,
        help="Send from a previously generated plan JSON",
    )
    send_parser.add_argument(
        "--at-once",
        type=int,
        default=5,
        help="Maximum concurrent sends",
    )

    report_parser = subparsers.add_parser(
        "report", help="Print a summary of subscribers, next send date, and issue status"
    )
    report_parser.add_argument(
        "--file",
        type=Path,
        default=Path("data/subscribers.csv"),
        help="Path to subscribers CSV",
    )
    report_parser.add_argument(
        "--issue",
        type=Path,
        default=Path("issues/issue-01.md"),
        help="Path to issue markdown",
    )
    report_parser.add_argument(
        "--run-date",
        type=date.fromisoformat,
        default=None,
        help="Reference date (YYYY-MM-DD); defaults to today",
    )

    guard_parser = subparsers.add_parser(
        "guard", help="Validate Claude Code hook JSON from stdin"
    )
    guard_parser.add_argument(
        "--subscribers",
        type=Path,
        default=None,
        help="Optional path to subscribers CSV",
    )

    args = parser.parse_args(argv)

    if args.command == "subscribers":
        effective_run_date = (
            args.run_date if args.run_date is not None else date.today()
        )
        try:
            summary = count_subscribers(
                args.file,
                since=args.since,
                since_days=args.since_days,
                run_date=effective_run_date
                if (args.since_days is not None or args.run_date is not None)
                else None,
            )
        except FileNotFoundError:
            print(f"File not found: {args.file}.", file=sys.stderr)
            return 2
        except ValueError as exc:
            print(f"Invalid subscriber data: {exc}", file=sys.stderr)
            return 1

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
        effective_run_date = (
            args.run_date if args.run_date is not None else date.today()
        )
        print(first_monday_of_next_month(effective_run_date).isoformat())
        return 0

    if args.command == "check":
        try:
            issue = Issue.from_file(args.issue_path)
        except FileNotFoundError:
            print(f"File not found: {args.issue_path}.", file=sys.stderr)
            return 2
        problems = check_issue(issue)
        if problems:
            for problem in problems:
                print(problem)
            return 1
        print("OK")
        return 0

    if args.command == "import":
        effective_run_date = (
            args.run_date if args.run_date is not None else date.today()
        )
        try:
            result = import_signups(args.csv_path, run_date=effective_run_date)
        except FileNotFoundError:
            print(f"File not found: {args.csv_path}.", file=sys.stderr)
            return 2

        if args.strict and result.problems:
            first = result.problems[0]
            print(f"Row {first.row_number} ({first.field}): {first.message}")
            return 1

        print(f"Accepted: {len(result.accepted)}")
        for sub in result.accepted:
            print(f"  {sub.full_name} <{sub.email}> ({sub.group})")
        print(f"Rejected: {len(result.problems)}")
        for prob in result.problems:
            print(f"  Row {prob.row_number} ({prob.field}): {prob.message}")
        return 1 if result.problems else 0

    if args.command == "send":
        try:
            if args.from_plan is not None:
                plan = SendPlan.from_file(args.from_plan)
            else:
                if args.issue_path is None:
                    print("Provide an issue_path or --from-plan.", file=sys.stderr)
                    return 2
                issue = Issue.from_file(args.issue_path)
                subscribers = load_subscribers(args.file)
                plan = build_send_plan(
                    issue=issue,
                    subscribers=subscribers,
                    sender=os.environ.get(
                        "SENDER_EMAIL_ADDRESS", "onboarding@resend.dev"
                    ),
                    company_address=os.environ.get(
                        "COMPANY_ADDRESS", "Kettlebird Tea, 12 Tea Lane"
                    ),
                    unsubscribe_base_url=os.environ.get(
                        "UNSUBSCRIBE_URL", "https://kettlebird.example/unsubscribe"
                    ),
                )
        except FileNotFoundError as exc:
            print(f"File not found: {exc.filename}.", file=sys.stderr)
            return 2
        except (ValueError, SendError) as exc:
            print(f"Cannot prepare send plan: {exc}", file=sys.stderr)
            return 1

        if args.dry_run:
            plan.save(args.plan_out)
            print(f"Dry run: wrote {len(plan.emails)} emails to {args.plan_out}.")
            return 0

        api_url = os.environ.get("RESEND_API_URL", "http://localhost:4000")
        api_key = os.environ.get("RESEND_API_KEY", "re_practice")
        try:
            receipts = asyncio.run(
                send_plan(
                    plan,
                    api_url=api_url,
                    api_key=api_key,
                    at_once=args.at_once,
                )
            )
        except SendError as exc:
            print(f"Send failed: {exc}", file=sys.stderr)
            return 1

        print(f"Sent {len(receipts)} emails.")
        return 0

    if args.command == "report":
        effective_run_date = (
            args.run_date if args.run_date is not None else date.today()
        )
        try:
            summary = count_subscribers(args.file)
            issue = Issue.from_file(args.issue)
        except FileNotFoundError as exc:
            print(f"File not found: {exc.filename}.", file=sys.stderr)
            return 2
        problems = check_issue(issue)
        issue_label = args.issue.as_posix()
        status = "OK" if not problems else f"{len(problems)} problem(s)"
        print(f"Subscribers: {summary['total']}")
        print(f"Next send: {first_monday_of_next_month(effective_run_date).isoformat()}")
        print(f"{issue_label}: {status}")
        return 1 if problems else 0

    if args.command == "guard":
        raw_stdin = sys.stdin.read().strip()
        if not raw_stdin:
            return 0
        try:
            payload: object = json.loads(raw_stdin)
        except json.JSONDecodeError as exc:
            print(f"Invalid hook JSON: {exc}", file=sys.stderr)
            return 2
        decision = evaluate_hook_payload(
            payload,
            my_email=os.environ.get("MY_EMAIL"),
        )
        if decision.message:
            print(decision.message, file=sys.stderr)
        return decision.exit_code

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
