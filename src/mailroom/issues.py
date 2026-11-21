from mailroom.models import Issue


def check_subject(issue: Issue) -> list[str]:
    """Validate line 1 Subject: rule (present, non-empty, <= 50 chars via len())."""
    lines = issue.text.splitlines()
    if not lines or not lines[0].startswith("Subject:"):
        return ["Line 1: missing 'Subject: ...' line."]
    subject = lines[0][len("Subject:") :].strip()
    if not subject:
        return ["Line 1: Subject is empty."]
    if len(subject) > 50:
        return [f"Line 1: Subject is {len(subject)} characters (limit is 50)."]
    return []


def check_issue(issue: Issue) -> list[str]:
    """Validate an Issue object against docs/email-rules.md."""
    problems = check_subject(issue)
    lines = issue.text.splitlines()

    if len(lines) < 2 or not lines[1].startswith("Preview:"):
        problems.append("Line 2: missing 'Preview: ...' line.")
    else:
        preview = lines[1][len("Preview:") :].strip()
        if not preview:
            problems.append("Line 2: Preview is empty.")
        elif len(preview) > 90:
            problems.append(
                f"Line 2: Preview is {len(preview)} characters (limit is 90)."
            )

    if "{{first_name}}" not in issue.text:
        problems.append("Missing '{{first_name}}' greeting.")

    links = issue.links
    if len(links) != 1:
        problems.append(f"Expected exactly 1 main link, found {len(links)}.")
    elif not links[0][1].startswith("https://"):
        problems.append(f"Main link must use https:// (found {links[0][1]}).")

    in_code_block = False
    has_getting_line = False
    has_unsub_line = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if not in_code_block:
            if line.startswith("You're getting this because"):
                has_getting_line = True
            if "Unsubscribe: {{unsubscribe_url}}" in line:
                has_unsub_line = True

    if not has_getting_line:
        problems.append(
            "Missing plain-text footer line starting with \"You're getting this because\"."
        )
    if not has_unsub_line:
        problems.append(
            "Missing plain-text footer line containing 'Unsubscribe: {{unsubscribe_url}}'."
        )

    return problems
