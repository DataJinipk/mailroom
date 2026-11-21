from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re

ALLOWED_GROUPS: frozenset[str] = frozenset(
    {"tea-curious", "gift-buyers", "daily-drinkers"}
)
EMAIL_SHAPE_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


@dataclass(frozen=True)
class Subscriber:
    """Validated newsletter subscriber."""

    first_name: str
    last_name: str
    email: str
    group: str
    joined_on: date
    consent: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "Subscriber":
        """Validate shape of a CSV row and construct a Subscriber."""
        first_name = (row.get("first_name") or "").strip()
        last_name = (row.get("last_name") or "").strip()
        email = (row.get("email") or "").strip()
        group = (row.get("group") or "").strip()
        joined_raw = (row.get("joined_on") or "").strip()
        consent = (row.get("consent") or "").strip()

        if not first_name:
            raise ValueError("first_name is required")
        if not last_name:
            raise ValueError("last_name is required")
        if not EMAIL_SHAPE_PATTERN.match(email):
            raise ValueError(f"invalid email shape: {email!r}")
        if group not in ALLOWED_GROUPS:
            raise ValueError(f"invalid group: {group!r}")
        try:
            joined_on = date.fromisoformat(joined_raw)
        except ValueError as exc:
            raise ValueError(f"invalid joined_on date: {joined_raw!r}") from exc
        if not consent:
            raise ValueError("consent is required")

        return cls(
            first_name=first_name,
            last_name=last_name,
            email=email,
            group=group,
            joined_on=joined_on,
            consent=consent,
        )


@dataclass(frozen=True)
class Issue:
    """Newsletter issue markdown document."""

    text: str

    @classmethod
    def from_text(cls, text: str) -> "Issue":
        return cls(text=text)

    @classmethod
    def from_file(cls, path: Path) -> "Issue":
        return cls(text=path.read_text(encoding="utf-8"))

    @property
    def links(self) -> list[tuple[str, str]]:
        return LINK_PATTERN.findall(self.text)

    def personalize(self, first_name: str) -> str:
        return self.text.replace("{{first_name}}", first_name)


@dataclass(frozen=True)
class ImportProblem:
    """Single validation problem for an imported CSV row."""

    row_number: int
    field: str
    message: str


@dataclass(frozen=True)
class ImportResult:
    """Result of importing and validating subscriber signups."""

    accepted: list[Subscriber]
    problems: list[ImportProblem]


@dataclass(frozen=True)
class PlannedEmail:
    """Validated outbound email entry in a dry-run send plan."""

    to: str
    sender: str
    subject: str
    text: str
    idempotency_key: str

    @classmethod
    def from_dict(cls, data: object) -> "PlannedEmail":
        if not isinstance(data, dict):
            raise ValueError("planned email entry must be a JSON object")
        to = str(data.get("to") or "").strip()
        sender = str(data.get("sender") or "").strip()
        subject = str(data.get("subject") or "").strip()
        text = str(data.get("text") or "").strip()
        idempotency_key = str(data.get("idempotency_key") or "").strip()
        if not EMAIL_SHAPE_PATTERN.match(to):
            raise ValueError(f"invalid planned recipient email: {to!r}")
        if not EMAIL_SHAPE_PATTERN.match(sender):
            raise ValueError(f"invalid planned sender email: {sender!r}")
        if not subject or len(subject) > 50:
            raise ValueError(f"invalid planned subject: {subject!r}")
        if not text:
            raise ValueError("planned email text is required")
        if not idempotency_key:
            raise ValueError("planned email idempotency_key is required")
        return cls(
            to=to,
            sender=sender,
            subject=subject,
            text=text,
            idempotency_key=idempotency_key,
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "to": self.to,
            "sender": self.sender,
            "subject": self.subject,
            "text": self.text,
            "idempotency_key": self.idempotency_key,
        }


@dataclass(frozen=True)
class SendPlan:
    """Validated collection of planned emails."""

    emails: list[PlannedEmail]

    @classmethod
    def from_file(cls, path: Path) -> "SendPlan":
        import json

        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or not isinstance(raw.get("emails"), list):
            raise ValueError("send plan JSON must contain an 'emails' list")
        emails = [PlannedEmail.from_dict(item) for item in raw["emails"]]
        return cls(emails=emails)

    def save(self, path: Path) -> None:
        import json

        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"emails": [email.to_dict() for email in self.emails]}
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
