import io
import json
from pathlib import Path

import pytest

from mailroom.commands import main
from mailroom.guard import evaluate_hook_payload


def test_guard_blocks_non_practice_recipient() -> None:
    payload = {
        "tool_name": "mcp__resend__send-email",
        "tool_input": {
            "to": ["sara.ali@gmail.com"],
            "subject": "Hi",
            "text": "Hello",
        },
    }
    decision = evaluate_hook_payload(payload, my_email=None)
    assert decision.exit_code == 2
    assert "sara.ali@gmail.com" in decision.message


def test_guard_allows_resend_dev_recipient() -> None:
    payload = {
        "tool_name": "mcp__resend__send-email",
        "tool_input": {
            "to": ["delivered@resend.dev"],
            "subject": "Hi",
            "text": "Hello",
        },
    }
    decision = evaluate_hook_payload(payload, my_email=None)
    assert decision.exit_code == 0


def test_guard_allows_my_email_recipient() -> None:
    payload = {
        "tool_name": "mcp__resend__send-email",
        "tool_input": {
            "to": "amir@example.org",
            "subject": "Hi",
            "text": "Hello",
        },
    }
    decision = evaluate_hook_payload(payload, my_email="amir@example.org")
    assert decision.exit_code == 0


def test_guard_blocks_broadcast_tools() -> None:
    payload = {
        "tool_name": "mcp__resend__send-broadcast",
        "tool_input": {},
    }
    decision = evaluate_hook_payload(payload, my_email=None)
    assert decision.exit_code == 2


def test_guard_blocks_56_char_subject_in_campaign_email(tmp_path: Path) -> None:
    email_file = tmp_path / "campaigns" / "steep-club-launch" / "emails" / "01.md"
    email_file.parent.mkdir(parents=True, exist_ok=True)
    bad_text = Path("issues/issue-01.md").read_text(encoding="utf-8").replace(
        "Subject: The Steep Club opens Monday",
        "Subject: " + ("x" * 56),
    )
    email_file.write_text(bad_text, encoding="utf-8")

    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": str(email_file), "content": bad_text},
    }
    decision = evaluate_hook_payload(payload, my_email=None)
    assert decision.exit_code == 2
    assert "56" in decision.message


def test_guard_cli_reads_stdin_and_returns_exit_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    raw = json.dumps(
        {
            "tool_name": "mcp__resend__send-email",
            "tool_input": {"to": ["sara.ali@gmail.com"]},
        }
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(raw))
    code = main(["guard"])
    captured = capsys.readouterr()
    assert code == 2
    assert "sara.ali@gmail.com" in captured.err
