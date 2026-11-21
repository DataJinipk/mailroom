import pytest

from mailroom.commands import main


def test_report_command_summarizes_subscribers_next_send_and_issue_status(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(["report", "--run-date", "2026-11-20"])
    captured = capsys.readouterr()
    assert code == 0
    assert "Subscribers: 24" in captured.out
    assert "Next send: 2026-12-07" in captured.out
    assert "issues/issue-01.md: OK" in captured.out
