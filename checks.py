from datetime import date
from pathlib import Path
import tempfile

from mailroom import count_subscribers, first_monday_of_next_month


def test_counts_default_subscribers():
    result = count_subscribers(Path("data/subscribers.csv"))
    assert result["total"] == 24, f"expected 24, got {result['total']}"
    assert result["groups"] == {
        "tea-curious": 8,
        "gift-buyers": 8,
        "daily-drinkers": 8,
    }, f"unexpected groups: {result['groups']}"
    assert result["consents"] == {"waitlist form": 24}, (
        f"unexpected consents: {result['consents']}"
    )


def test_counts_external_six_row_copy():
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
    with tempfile.TemporaryDirectory() as tmp:
        csv_path = Path(tmp) / "six.csv"
        csv_path.write_text(sample, encoding="utf-8")
        result = count_subscribers(csv_path)
        assert result["total"] == 6
        assert result["groups"] == {
            "tea-curious": 2,
            "gift-buyers": 2,
            "daily-drinkers": 2,
        }
        assert result["consents"] == {"waitlist form": 5, "import": 1}


def test_since_days_30_edge_date():
    result = count_subscribers(
        Path("data/subscribers.csv"),
        since_days=30,
        run_date=date(2026, 11, 20),
    )
    assert result["total"] == 7, f"expected 7, got {result['total']}"


def test_since_exact_date():
    result = count_subscribers(
        Path("data/subscribers.csv"),
        since=date(2026, 10, 1),
        run_date=date(2026, 11, 20),
    )
    assert result["total"] == 12, f"expected 12, got {result['total']}"


def test_first_monday_of_next_month():
    assert first_monday_of_next_month(date(2026, 11, 20)) == date(2026, 12, 7)
    assert first_monday_of_next_month(date(2026, 12, 7)) == date(2027, 1, 4)
    assert first_monday_of_next_month(date(2026, 12, 31)) == date(2027, 1, 4)


if __name__ == "__main__":
    test_counts_default_subscribers()
    test_counts_external_six_row_copy()
    test_since_days_30_edge_date()
    test_since_exact_date()
    test_first_monday_of_next_month()
    print("All Step 2 checks passed.")
