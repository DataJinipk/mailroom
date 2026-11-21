import argparse
from collections import Counter
import csv
from datetime import date, timedelta
from pathlib import Path


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

    args = parser.parse_args()
    effective_run_date = args.run_date if args.run_date is not None else date.today()

    if args.command == "subscribers":
        summary = count_subscribers(
            args.file,
            since=args.since,
            since_days=args.since_days,
            run_date=effective_run_date if (args.since_days is not None or args.run_date is not None) else None,
        )
        print(f"Total subscribers: {summary['total']}")
        print("By group:")
        for name, count in summary["groups"].items():
            print(f"  {name}: {count}")
        print("By consent:")
        for name, count in summary["consents"].items():
            print(f"  {name}: {count}")
        print(f"Next send date: {first_monday_of_next_month(effective_run_date).isoformat()}")
        return 0

    if args.command == "next-send":
        print(first_monday_of_next_month(effective_run_date).isoformat())
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
