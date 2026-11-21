import argparse
from datetime import date
from pathlib import Path
import sys

from mailroom.dates import first_monday_of_next_month
from mailroom.issues import check_issue
from mailroom.models import Issue
from mailroom.subscribers import count_subscribers, import_signups


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

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
