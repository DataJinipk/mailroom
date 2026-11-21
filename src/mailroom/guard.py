from dataclasses import dataclass
from pathlib import Path

from mailroom.issues import check_issue
from mailroom.models import Issue

BLOCKED_RESEND_TOOLS: frozenset[str] = frozenset(
    {
        "send-broadcast",
        "create-automation",
        "send-inbox-draft",
        "send-new-inbox-email",
    }
)
SEND_RESEND_TOOLS: frozenset[str] = frozenset({"send-email", "send-batch-emails"})


@dataclass(frozen=True)
class GuardDecision:
    """Result of evaluating a Claude Code hook payload."""

    exit_code: int
    message: str = ""


def _extract_addresses(value: object) -> list[str]:
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(value, list):
        addresses: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                addresses.append(item.strip())
        return addresses
    return []


def _collect_recipients(tool_input: dict[str, object]) -> list[str]:
    recipients: list[str] = []
    for key in ("to", "cc", "bcc"):
        recipients.extend(_extract_addresses(tool_input.get(key)))
    batch = tool_input.get("emails")
    if isinstance(batch, list):
        for entry in batch:
            if isinstance(entry, dict):
                for key in ("to", "cc", "bcc"):
                    recipients.extend(_extract_addresses(entry.get(key)))
    return recipients


def _is_allowed_recipient(address: str, *, my_email: str | None) -> bool:
    lowered = address.lower()
    if lowered.endswith("@resend.dev"):
        return True
    if my_email and lowered == my_email.strip().lower():
        return True
    return False


def _is_campaign_email_path(file_path: str) -> bool:
    normalized = file_path.replace("\\", "/").lower()
    parts = [part for part in normalized.split("/") if part]
    return (
        "campaigns" in parts
        and "emails" in parts
        and normalized.endswith(".md")
    )


def evaluate_hook_payload(
    payload: object,
    *,
    my_email: str | None = None,
) -> GuardDecision:
    """Evaluate a Claude Code PreToolUse/PostToolUse JSON payload."""
    if not isinstance(payload, dict):
        return GuardDecision(exit_code=0)

    tool_name = str(payload.get("tool_name") or "")
    raw_input = payload.get("tool_input")
    tool_input: dict[str, object] = (
        {str(k): v for k, v in raw_input.items()}
        if isinstance(raw_input, dict)
        else {}
    )

    short_name = tool_name.removeprefix("mcp__resend__")
    if tool_name.startswith("mcp__resend__") or short_name in (
        BLOCKED_RESEND_TOOLS | SEND_RESEND_TOOLS
    ):
        if short_name in BLOCKED_RESEND_TOOLS:
            return GuardDecision(
                exit_code=2,
                message=f"Blocked {tool_name}: bulk/broadcast tools are disabled by Mailroom guard.",
            )
        if short_name in SEND_RESEND_TOOLS:
            recipients = _collect_recipients(tool_input)
            for addr in recipients:
                if not _is_allowed_recipient(addr, my_email=my_email):
                    return GuardDecision(
                        exit_code=2,
                        message=(
                            f"Blocked send to {addr}: only @resend.dev or MY_EMAIL is allowed."
                        ),
                    )
        return GuardDecision(exit_code=0)

    if tool_name in ("Write", "Edit", "MultiEdit"):
        file_path = str(tool_input.get("file_path") or "")
        if not file_path or not _is_campaign_email_path(file_path):
            return GuardDecision(exit_code=0)

        content_obj = tool_input.get("content")
        path = Path(file_path)
        if path.exists():
            text = path.read_text(encoding="utf-8")
        elif isinstance(content_obj, str):
            text = content_obj
        else:
            return GuardDecision(exit_code=0)

        problems = check_issue(Issue.from_text(text))
        if problems:
            return GuardDecision(
                exit_code=2,
                message=f"Mailroom issue check failed for {file_path}:\n"
                + "\n".join(f"- {p}" for p in problems),
            )

    return GuardDecision(exit_code=0)
