from pathlib import Path

from mailroom import Issue, check_issue, check_subject


def test_subject_valid_issue_01() -> None:
    issue = Issue.from_file(Path("issues/issue-01.md"))
    assert check_subject(issue) == []


def test_subject_exact_50_chars_passes() -> None:
    subject = "a" * 50
    assert check_subject(Issue.from_text(f"Subject: {subject}\n")) == []


def test_subject_51_chars_fails() -> None:
    subject = "a" * 51
    problems = check_subject(Issue.from_text(f"Subject: {subject}\n"))
    assert len(problems) == 1
    assert "50" in problems[0]


def test_subject_empty_fails() -> None:
    problems = check_subject(Issue.from_text("Subject: \n"))
    assert len(problems) == 1


def test_subject_whitespace_only_fails() -> None:
    problems = check_subject(Issue.from_text("Subject:    \n"))
    assert len(problems) == 1


def test_subject_missing_line_1_fails() -> None:
    problems = check_subject(Issue.from_text("Preview: Hello\n"))
    assert len(problems) == 1


def test_issue_01_passes_all_rules() -> None:
    issue = Issue.from_file(Path("issues/issue-01.md"))
    assert check_issue(issue) == []
    assert issue.links == [("Join The Steep Club", "https://kettlebird.example/steep-club")]


def test_issue_personalize_replaces_first_name() -> None:
    issue = Issue.from_file(Path("issues/issue-01.md"))
    personalized = issue.personalize("Ayesha")
    assert "Hi Ayesha," in personalized
    assert "{{first_name}}" not in personalized


def test_issue_preview_over_90_chars_fails() -> None:
    text = Path("issues/issue-01.md").read_text(encoding="utf-8")
    bad = text.replace(
        "Preview: Your monthly tea box, chosen by our blenders. Founding members get the first box free.",
        "Preview: " + ("x" * 91),
    )
    problems = check_issue(Issue.from_text(bad))
    assert any("90" in p for p in problems)


def test_issue_missing_first_name_greeting_fails() -> None:
    text = Path("issues/issue-01.md").read_text(encoding="utf-8")
    bad = text.replace("Hi {{first_name}},", "Hi friend,")
    problems = check_issue(Issue.from_text(bad))
    assert any("{{first_name}}" in p for p in problems)


def test_issue_two_links_fails() -> None:
    text = Path("issues/issue-01.md").read_text(encoding="utf-8")
    bad = text.replace(
        "[Join The Steep Club](https://kettlebird.example/steep-club)",
        "[Join](https://kettlebird.example/steep-club) and [More](https://kettlebird.example/more)",
    )
    problems = check_issue(Issue.from_text(bad))
    assert any("link" in p.lower() for p in problems)


def test_issue_missing_footer_fails() -> None:
    text = Path("issues/issue-01.md").read_text(encoding="utf-8")
    bad = text.replace("Unsubscribe: {{unsubscribe_url}}", "Unsubscribe here")
    problems = check_issue(Issue.from_text(bad))
    assert any("unsubscribe" in p.lower() for p in problems)


def test_subject_emoji_uses_python_len() -> None:
    emoji_subject = "👍🏽 Thanks for joining"
    assert len(emoji_subject) == 21
    assert check_subject(Issue.from_text(f"Subject: {emoji_subject}\n")) == []

    boundary_51 = ("a" * 49) + "👍🏽"
    assert len(boundary_51) == 51
    assert len(check_subject(Issue.from_text(f"Subject: {boundary_51}\n"))) == 1
