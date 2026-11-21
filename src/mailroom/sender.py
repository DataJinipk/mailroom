import asyncio
import hashlib
from urllib.parse import urlparse

import httpx

from mailroom.issues import check_issue
from mailroom.models import Issue, PlannedEmail, SendPlan, Subscriber
from mailroom.subscribers import ALLOWED_PRACTICE_DOMAINS


class SendError(Exception):
    """Raised when sending fails validation or receives an unrecoverable HTTP error."""


class SentReceipt:
    """Result of a single delivered practice email."""

    def __init__(self, *, to: str, message_id: str, status: int) -> None:
        self.to = to
        self.message_id = message_id
        self.status = status


def _extract_subject(issue: Issue) -> str:
    lines = issue.text.splitlines()
    if lines and lines[0].startswith("Subject:"):
        return lines[0][len("Subject:") :].strip()
    return ""


def _render_body(
    issue: Issue,
    *,
    subscriber: Subscriber,
    company_address: str,
    unsubscribe_base_url: str,
) -> str:
    personalized = issue.personalize(subscriber.first_name)
    unsubscribe_url = f"{unsubscribe_base_url.rstrip('/')}?email={subscriber.email}"
    return personalized.replace("{{company_address}}", company_address).replace(
        "{{unsubscribe_url}}", unsubscribe_url
    )


def build_send_plan(
    *,
    issue: Issue,
    subscribers: list[Subscriber],
    sender: str,
    company_address: str,
    unsubscribe_base_url: str,
) -> SendPlan:
    """Validate an issue and build a deterministic SendPlan for all subscribers."""
    problems = check_issue(issue)
    if problems:
        raise SendError("; ".join(problems))

    subject = _extract_subject(issue)
    digest = hashlib.sha256(issue.text.encode("utf-8")).hexdigest()[:12]

    planned: list[PlannedEmail] = []
    for sub in subscribers:
        body = _render_body(
            issue,
            subscriber=sub,
            company_address=company_address,
            unsubscribe_base_url=unsubscribe_base_url,
        )
        planned.append(
            PlannedEmail(
                to=sub.email,
                sender=sender,
                subject=subject,
                text=body,
                idempotency_key=f"{digest}:{sub.email}",
            )
        )
    return SendPlan(emails=planned)


def _ensure_localhost_url(api_url: str) -> None:
    parsed = urlparse(api_url)
    if parsed.scheme not in ("http", "https") or parsed.hostname not in (
        "localhost",
        "127.0.0.1",
    ):
        raise SendError(
            f"Refusing non-localhost RESEND_API_URL ({api_url}); sending works only against localhost."
        )


def _ensure_practice_recipient(email: str) -> None:
    if not email.lower().endswith(ALLOWED_PRACTICE_DOMAINS):
        raise SendError(
            f"Refusing non-practice recipient ({email}); only @example.com and @resend.dev are allowed."
        )


async def _send_one(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    email: PlannedEmail,
    *,
    api_key: str,
    max_retries: int,
) -> SentReceipt:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Idempotency-Key": email.idempotency_key,
    }
    payload = {
        "from": email.sender,
        "to": [email.to],
        "subject": email.subject,
        "text": email.text,
    }

    async with semaphore:
        last_error: str = "unknown error"
        for attempt in range(1, max_retries + 1):
            try:
                response = await client.post("/emails", json=payload, headers=headers)
            except httpx.RequestError as exc:
                last_error = f"connection error for {email.to}: {exc}"
                if attempt < max_retries:
                    await asyncio.sleep(0.05 * attempt)
                    continue
                raise SendError(last_error) from exc

            if 400 <= response.status_code < 500:
                raise SendError(
                    f"HTTP {response.status_code} for {email.to}: {response.text}"
                )
            if response.status_code >= 500:
                last_error = f"HTTP {response.status_code} for {email.to}"
                if attempt < max_retries:
                    await asyncio.sleep(0.05 * attempt)
                    continue
                raise SendError(last_error)

            data = response.json()
            msg_id = str(data.get("id") or "")
            return SentReceipt(to=email.to, message_id=msg_id, status=response.status_code)

        raise SendError(last_error)


async def send_plan(
    plan: SendPlan,
    *,
    api_url: str,
    api_key: str,
    at_once: int = 5,
    max_retries: int = 3,
    transport: httpx.AsyncBaseTransport | None = None,
) -> list[SentReceipt]:
    """Send all emails in a SendPlan concurrently with localhost and recipient guards."""
    _ensure_localhost_url(api_url)
    for email in plan.emails:
        _ensure_practice_recipient(email.to)

    if at_once < 1:
        raise ValueError("at_once must be >= 1")

    semaphore = asyncio.Semaphore(at_once)
    async with httpx.AsyncClient(
        base_url=api_url,
        transport=transport,
        timeout=10.0,
    ) as client:
        tasks = [
            _send_one(
                client,
                semaphore,
                email,
                api_key=api_key,
                max_retries=max_retries,
            )
            for email in plan.emails
        ]
        return list(await asyncio.gather(*tasks))
