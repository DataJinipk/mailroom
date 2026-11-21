from datetime import date
from pathlib import Path

import pytest

from mailroom import import_signups
from mailroom.commands import main


def test_import_shape_only_accepts_four_and_rejects_four() -> None:
    result = import_signups(
        Path("data/new-signups.csv"),
        run_date=date(2026, 11, 20),
        apply_domain_rules=False,
    )
    assert [s.first_name for s in result.accepted] == ["Maria", "Sara", "Tom", "Ines"]
    assert len(result.problems) == 4
    assert [p.row_number for p in result.problems] == [2, 3, 4, 5]


def test_import_with_domain_rules_accepts_two_and_reports_all_six_problems() -> None:
    result = import_signups(
        Path("data/new-signups.csv"),
        run_date=date(2026, 11, 20),
        apply_domain_rules=True,
    )
    assert [s.first_name for s in result.accepted] == ["Maria", "Ines"]
    assert len(result.problems) == 6
    assert [p.row_number for p in result.problems] == [2, 3, 4, 5, 6, 7]


def test_cli_missing_file_returns_exit_code_2_without_traceback(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(["import", "data/does-not-exist.csv", "--run-date", "2026-11-20"])
    captured = capsys.readouterr()
    assert code == 2
    assert "Traceback" not in captured.err
    assert "Traceback" not in captured.out
    assert "not found" in captured.err.lower() or "does not exist" in captured.err.lower()


def test_cli_import_bad_rows_returns_exit_code_1_with_all_problems(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(["import", "data/new-signups.csv", "--run-date", "2026-11-20"])
    captured = capsys.readouterr()
    assert code == 1
    assert "Accepted: 2" in captured.out
    assert "Rejected: 6" in captured.out
    assert "Row 6" in captured.out
    assert "Row 7" in captured.out
