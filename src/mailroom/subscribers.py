from collections import Counter
import csv
from datetime import date, timedelta
from pathlib import Path
from typing import TypedDict

from mailroom.models import ImportProblem, ImportResult, Subscriber

ALLOWED_PRACTICE_DOMAINS: tuple[str, ...] = ("@example.com", "@resend.dev")


class SubscriberSummary(TypedDict):
    total: int
    groups: dict[str, int]
    consents: dict[str, int]


def load_subscribers(csv_path: Path) -> list[Subscriber]:
    """Load and shape-validate all subscribers from a CSV file."""
    subscribers: list[Subscriber] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            subscribers.append(Subscriber.from_row(row))
    return subscribers


def count_subscribers(
    csv_path: Path,
    *,
    since: date | None = None,
    since_days: int | None = None,
    run_date: date | None = None,
) -> SubscriberSummary:
    """Count total subscribers, group breakdown, and consent breakdown."""
    cutoff: date | None = since
    if since_days is not None:
        if run_date is None:
            raise ValueError("run_date is required when using since_days")
        days_cutoff = run_date - timedelta(days=since_days)
        cutoff = days_cutoff if cutoff is None else max(cutoff, days_cutoff)

    groups: Counter[str] = Counter()
    consents: Counter[str] = Counter()
    total = 0

    for sub in load_subscribers(csv_path):
        if cutoff is not None and sub.joined_on < cutoff:
            continue
        if run_date is not None and sub.joined_on > run_date:
            continue
        total += 1
        groups[sub.group] += 1
        consents[sub.consent] += 1

    return {
        "total": total,
        "groups": dict(groups),
        "consents": dict(consents),
    }


def validate_subscriber_domain(sub: Subscriber, *, run_date: date) -> list[tuple[str, str]]:
    """Check business/domain rules beyond basic data shape."""
    errors: list[tuple[str, str]] = []
    lowered = sub.email.lower()
    if not lowered.endswith(ALLOWED_PRACTICE_DOMAINS):
        errors.append(
            ("email", f"non-practice email address is not allowed: {sub.email}")
        )
    if sub.joined_on > run_date:
        errors.append(
            (
                "joined_on",
                f"join date {sub.joined_on.isoformat()} is after run date {run_date.isoformat()}",
            )
        )
    return errors


def _infer_field(message: str) -> str:
    for field in ("first_name", "last_name", "email", "group", "joined_on", "consent"):
        if field in message:
            return field
    return "row"


def import_signups(
    csv_path: Path,
    *,
    run_date: date,
    apply_domain_rules: bool = True,
) -> ImportResult:
    """Import signups CSV, validating shape and optionally domain rules."""
    accepted: list[Subscriber] = []
    problems: list[ImportProblem] = []

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row_number, row in enumerate(reader, start=1):
            try:
                sub = Subscriber.from_row(row)
            except ValueError as exc:
                msg = str(exc)
                problems.append(
                    ImportProblem(
                        row_number=row_number,
                        field=_infer_field(msg),
                        message=msg,
                    )
                )
                continue

            if apply_domain_rules:
                domain_errors = validate_subscriber_domain(sub, run_date=run_date)
                if domain_errors:
                    for field, msg in domain_errors:
                        problems.append(
                            ImportProblem(
                                row_number=row_number,
                                field=field,
                                message=msg,
                            )
                        )
                    continue

            accepted.append(sub)

    return ImportResult(accepted=accepted, problems=problems)
