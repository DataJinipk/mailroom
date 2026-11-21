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
