from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mailroom import check_issue, check_subject


def test_subject_valid_issue_01() -> None:
    text = Path("issues/issue-01.md").read_text(encoding="utf-8")
    assert check_subject(text) == []


def test_subject_exact_50_chars_passes() -> None:
    subject = "a" * 50
    assert check_subject(f"Subject: {subject}\n") == []


def test_subject_51_chars_fails() -> None:
    subject = "a" * 51
    problems = check_subject(f"Subject: {subject}\n")
    assert len(problems) == 1
    assert "50" in problems[0]


def test_subject_empty_fails() -> None:
    problems = check_subject("Subject: \n")
    assert len(problems) == 1


def test_subject_whitespace_only_fails() -> None:
    problems = check_subject("Subject:    \n")
    assert len(problems) == 1


def test_subject_missing_line_1_fails() -> None:
    problems = check_subject("Preview: Hello\n")
    assert len(problems) == 1


def test_issue_01_passes_all_rules() -> None:
    text = Path("issues/issue-01.md").read_text(encoding="utf-8")
    assert check_issue(text) == []


def test_issue_preview_over_90_chars_fails() -> None:
    text = Path("issues/issue-01.md").read_text(encoding="utf-8")
    bad = text.replace(
        "Preview: Your monthly tea box, chosen by our blenders. Founding members get the first box free.",
        "Preview: " + ("x" * 91),
    )
    problems = check_issue(bad)
    assert any("90" in p for p in problems)


def test_issue_missing_first_name_greeting_fails() -> None:
    text = Path("issues/issue-01.md").read_text(encoding="utf-8")
    bad = text.replace("Hi {{first_name}},", "Hi friend,")
    problems = check_issue(bad)
    assert any("{{first_name}}" in p for p in problems)


def test_issue_two_links_fails() -> None:
    text = Path("issues/issue-01.md").read_text(encoding="utf-8")
    bad = text.replace(
        "[Join The Steep Club](https://kettlebird.example/steep-club)",
        "[Join](https://kettlebird.example/steep-club) and [More](https://kettlebird.example/more)",
    )
    problems = check_issue(bad)
    assert any("link" in p.lower() for p in problems)


def test_issue_missing_footer_fails() -> None:
    text = Path("issues/issue-01.md").read_text(encoding="utf-8")
    bad = text.replace("Unsubscribe: {{unsubscribe_url}}", "Unsubscribe here")
    problems = check_issue(bad)
    assert any("unsubscribe" in p.lower() for p in problems)


def test_subject_emoji_uses_python_len() -> None:
    emoji_subject = "👍🏽 Thanks for joining"
    assert len(emoji_subject) == 21
    assert check_subject(f"Subject: {emoji_subject}\n") == []

    boundary_51 = ("a" * 49) + "👍🏽"
    assert len(boundary_51) == 51
    assert len(check_subject(f"Subject: {boundary_51}\n")) == 1
