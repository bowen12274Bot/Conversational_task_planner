import asyncio
import json

import pytest

from app.services.progress_events import (
    clear_progress_events,
    publish_progress_event,
    subscribe_progress_events,
)


def test_subscribe_progress_events_replays_existing_events() -> None:
    asyncio.run(_run_subscribe_progress_events_replay_test())


async def _run_subscribe_progress_events_replay_test() -> None:
    conversation_id = "conv-progress-service"
    request_id = "req-progress-service"
    clear_progress_events(conversation_id, request_id)

    publish_progress_event(
        conversation_id=conversation_id,
        request_id=request_id,
        event_type="request_received",
        stage="F001",
    )
    publish_progress_event(
        conversation_id=conversation_id,
        request_id=request_id,
        event_type="completed",
        stage="F012",
    )

    stream = subscribe_progress_events(
        conversation_id=conversation_id,
        request_id=request_id,
    )
    first_event = await anext(stream)
    second_event = await anext(stream)

    assert _parse_sse_event(first_event)["event_type"] == "request_received"
    assert _parse_sse_event(second_event)["event_type"] == "completed"

    with pytest.raises(StopAsyncIteration):
        await anext(stream)

    clear_progress_events(conversation_id, request_id)


def _parse_sse_event(raw_event: str) -> dict[str, object]:
    data_line = next(line for line in raw_event.splitlines() if line.startswith("data: "))
    return json.loads(data_line.removeprefix("data: "))
