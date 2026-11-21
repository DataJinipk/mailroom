import argparse
from collections import Counter
import csv
from pathlib import Path


def count_subscribers(csv_path: Path) -> dict[str, object]:
    """Count total subscribers, group breakdown, and consent breakdown from CSV."""
    groups: Counter[str] = Counter()
    consents: Counter[str] = Counter()
    total = 0

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
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

    args = parser.parse_args()
    if args.command == "subscribers":
        summary = count_subscribers(args.file)
        print(f"Total subscribers: {summary['total']}")
        print("By group:")
        for name, count in summary["groups"].items():
            print(f"  {name}: {count}")
        print("By consent:")
        for name, count in summary["consents"].items():
            print(f"  {name}: {count}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
