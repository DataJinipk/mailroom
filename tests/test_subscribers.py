from datetime import date
from pathlib import Path

from mailroom import Subscriber, count_subscribers, first_monday_of_next_month


def test_counts_default_subscribers_total_groups_and_consents() -> None:
    result = count_subscribers(Path("data/subscribers.csv"))
    assert result["total"] == 24
    assert result["groups"] == {
        "tea-curious": 8,
        "gift-buyers": 8,
        "daily-drinkers": 8,
    }
    assert result["consents"] == {"waitlist form": 24}


def test_counts_external_six_row_copy(tmp_path: Path) -> None:
    sample = "\n".join(
        [
            "first_name,last_name,email,group,joined_on,consent",
            "A,One,a1@example.com,tea-curious,2026-09-01,waitlist form",
            "B,Two,b2@example.com,tea-curious,2026-09-02,waitlist form",
            "C,Three,c3@example.com,gift-buyers,2026-09-03,waitlist form",
            "D,Four,d4@example.com,gift-buyers,2026-09-04,waitlist form",
            "E,Five,e5@example.com,daily-drinkers,2026-09-05,waitlist form",
            "F,Six,f6@example.com,daily-drinkers,2026-09-06,import",
        ]
    )
    csv_path = tmp_path / "six.csv"
    csv_path.write_text(sample, encoding="utf-8")

    result = count_subscribers(csv_path)
    assert result["total"] == 6
    assert result["groups"] == {
        "tea-curious": 2,
        "gift-buyers": 2,
        "daily-drinkers": 2,
    }
    assert result["consents"] == {"waitlist form": 5, "import": 1}


def test_since_days_30_includes_cutoff_boundary_and_excludes_day_31() -> None:
    result = count_subscribers(
        Path("data/subscribers.csv"),
        since_days=30,
        run_date=date(2026, 11, 20),
    )
    assert result["total"] == 7


def test_since_exact_date_counts_matching_subscribers() -> None:
    result = count_subscribers(
        Path("data/subscribers.csv"),
        since=date(2026, 10, 1),
        run_date=date(2026, 11, 20),
    )
    assert result["total"] == 12


def test_first_monday_of_next_month_across_month_and_year_boundaries() -> None:
    assert first_monday_of_next_month(date(2026, 11, 20)) == date(2026, 12, 7)
    assert first_monday_of_next_month(date(2026, 12, 7)) == date(2027, 1, 4)
    assert first_monday_of_next_month(date(2026, 12, 31)) == date(2027, 1, 4)


def test_subscriber_full_name() -> None:
    sub = Subscriber(
        first_name="Ayesha",
        last_name="Khan",
        email="ayesha.khan@example.com",
        group="tea-curious",
        joined_on=date(2026, 9, 14),
        consent="waitlist form",
    )
    assert sub.full_name == "Ayesha Khan"
