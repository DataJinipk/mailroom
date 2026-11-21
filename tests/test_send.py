import asyncio
import json
from pathlib import Path

import httpx
import pytest

from mailroom import (
    Issue,
    PlannedEmail,
    SendPlan,
    build_send_plan,
    load_subscribers,
    send_plan,
)
from mailroom.sender import SendError


def test_build_send_plan_writes_24_personalized_emails_and_roundtrips(
    tmp_path: Path,
) -> None:
    issue = Issue.from_file(Path("issues/issue-01.md"))
    subscribers = load_subscribers(Path("data/subscribers.csv"))
    plan_path = tmp_path / "outbox" / "plan.json"

    plan = build_send_plan(
        issue=issue,
        subscribers=subscribers,
        sender="onboarding@resend.dev",
        company_address="12 Tea Lane, Portland, OR",
        unsubscribe_base_url="https://kettlebird.example/unsubscribe",
    )
    plan.save(plan_path)

    loaded = SendPlan.from_file(plan_path)
    assert len(loaded.emails) == 24
    first = loaded.emails[0]
    assert first.to == "ayesha.khan@example.com"
    assert first.subject == "The Steep Club opens Monday"
    assert "Hi Ayesha," in first.text
    assert "{{company_address}}" not in first.text
    assert "{{unsubscribe_url}}" not in first.text


def test_from_file_rejects_malformed_json_plan(tmp_path: Path) -> None:
    bad_path = tmp_path / "bad_plan.json"
    bad_path.write_text(json.dumps({"emails": [{"to": ""}]}), encoding="utf-8")
    with pytest.raises(ValueError):
        SendPlan.from_file(bad_path)


def test_refuses_non_localhost_api_url_before_request() -> None:
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, json={"id": "msg_1"})

    plan = SendPlan(
        emails=[
            PlannedEmail(
                to="delivered@resend.dev",
                sender="onboarding@resend.dev",
                subject="Hello",
                text="Hi there",
                idempotency_key="k1",
            )
        ]
    )
    with pytest.raises(SendError, match="localhost"):
        asyncio.run(
            send_plan(
                plan,
                api_url="https://api.resend.com",
                api_key="re_practice",
                transport=httpx.MockTransport(handler),
            )
        )
    assert not called


def test_refuses_non_practice_recipient_before_request() -> None:
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, json={"id": "msg_1"})

    plan = SendPlan(
        emails=[
            PlannedEmail(
                to="sara.ali@gmail.com",
                sender="onboarding@resend.dev",
                subject="Hello",
                text="Hi Sara",
                idempotency_key="k1",
            )
        ]
    )
    with pytest.raises(SendError, match="sara.ali@gmail.com"):
        asyncio.run(
            send_plan(
                plan,
                api_url="http://localhost:4000",
                api_key="re_practice",
                transport=httpx.MockTransport(handler),
            )
        )
    assert not called


def test_4xx_is_never_retried() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(422, json={"message": "validation error"})

    plan = SendPlan(
        emails=[
            PlannedEmail(
                to="delivered@resend.dev",
                sender="onboarding@resend.dev",
                subject="Hello",
                text="Hi there",
                idempotency_key="k1",
            )
        ]
    )
    with pytest.raises(SendError, match="422"):
        asyncio.run(
            send_plan(
                plan,
                api_url="http://localhost:4000",
                api_key="re_practice",
                max_retries=3,
                transport=httpx.MockTransport(handler),
            )
        )
    assert attempts == 1


def test_5xx_retries_with_same_idempotency_key() -> None:
    seen_keys: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_keys.append(request.headers.get("Idempotency-Key", ""))
        if len(seen_keys) < 3:
            return httpx.Response(503, json={"message": "temporary error"})
        return httpx.Response(200, json={"id": "msg_ok"})

    plan = SendPlan(
        emails=[
            PlannedEmail(
                to="delivered@resend.dev",
                sender="onboarding@resend.dev",
                subject="Hello",
                text="Hi there",
                idempotency_key="issue-01:delivered@resend.dev",
            )
        ]
    )
    results = asyncio.run(
        send_plan(
            plan,
            api_url="http://localhost:4000",
            api_key="re_practice",
            max_retries=3,
            transport=httpx.MockTransport(handler),
        )
    )
    assert len(results) == 1
    assert results[0].message_id == "msg_ok"
    assert seen_keys == [
        "issue-01:delivered@resend.dev",
        "issue-01:delivered@resend.dev",
        "issue-01:delivered@resend.dev",
    ]


def test_async_send_respects_at_once_limit_and_preserves_order() -> None:
    active = 0
    max_active = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.01)
        active -= 1
        payload = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json={"id": f"id:{payload['to'][0]}"})

    issue = Issue.from_file(Path("issues/issue-01.md"))
    subscribers = load_subscribers(Path("data/subscribers.csv"))
    plan = build_send_plan(
        issue=issue,
        subscribers=subscribers,
        sender="onboarding@resend.dev",
        company_address="12 Tea Lane, Portland, OR",
        unsubscribe_base_url="https://kettlebird.example/unsubscribe",
    )
    results = asyncio.run(
        send_plan(
            plan,
            api_url="http://localhost:4000",
            api_key="re_practice",
            at_once=5,
            transport=httpx.MockTransport(handler),
        )
    )
    assert len(results) == 24
    assert max_active <= 5
    assert results[0].to == "ayesha.khan@example.com"
    assert results[-1].to == "jonas.berg@example.com"
