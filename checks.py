from pathlib import Path
import tempfile

from mailroom import count_subscribers


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


if __name__ == "__main__":
    test_counts_default_subscribers()
    test_counts_external_six_row_copy()
    print("All Step 1 checks passed.")
