import asyncio
import json
import queue
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, AsyncIterator


PROGRESS_EVENT_TTL_SECONDS = 30
PROGRESS_EVENT_HEARTBEAT_SECONDS = 10


@dataclass
class ProgressEvent:
    conversation_id: str
    request_id: str
    event_type: str
    created_at: str
    turn_id: str | None = None
    stage: str | None = None
    route: str | None = None


class _ProgressEventStream:
    def __init__(self) -> None:
        self.events: list[ProgressEvent] = []
        self.subscribers: set[queue.Queue[ProgressEvent]] = set()
        self.completed = False
        self.expires_at: float | None = None


_event_streams: dict[tuple[str, str], _ProgressEventStream] = {}
_event_lock = threading.RLock()


def publish_progress_event(
    *,
    conversation_id: str | None,
    request_id: str | None,
    event_type: str,
    turn_id: str | None = None,
    stage: str | None = None,
    route: str | None = None,
) -> None:
    """Publish one progress event without allowing event failures to break flow."""

    if not conversation_id or not request_id:
        return

    try:
        _cleanup_expired_streams()
        event = ProgressEvent(
            conversation_id=conversation_id,
            request_id=request_id,
            event_type=event_type,
            turn_id=turn_id,
            stage=stage,
            route=route,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with _event_lock:
            stream = _event_streams.setdefault(
                (conversation_id, request_id),
                _ProgressEventStream(),
            )
            stream.events.append(event)
            for subscriber in list(stream.subscribers):
                try:
                    subscriber.put_nowait(event)
                except queue.Full:
                    stream.subscribers.discard(subscriber)

            if event_type in {"completed", "failed"}:
                stream.completed = True
                stream.expires_at = time.monotonic() + PROGRESS_EVENT_TTL_SECONDS
    except Exception:
        return


async def subscribe_progress_events(
    *,
    conversation_id: str,
    request_id: str,
) -> AsyncIterator[str]:
    """Yield SSE-formatted progress events for one conversation request."""

    subscriber: queue.Queue[ProgressEvent] = queue.Queue(maxsize=100)
    key = (conversation_id, request_id)

    with _event_lock:
        _cleanup_expired_streams_locked()
        stream = _event_streams.setdefault(key, _ProgressEventStream())
        replay_events = list(stream.events)
        stream.subscribers.add(subscriber)
        stream_completed = stream.completed

    try:
        for event in replay_events:
            yield _format_sse_event(event.event_type, asdict(event))

        if stream_completed:
            return

        while True:
            try:
                event = await asyncio.to_thread(
                    subscriber.get,
                    True,
                    PROGRESS_EVENT_HEARTBEAT_SECONDS,
                )
            except queue.Empty:
                yield _format_sse_event("ping", {})
                continue

            yield _format_sse_event(event.event_type, asdict(event))

            if event.event_type in {"completed", "failed"}:
                return
    finally:
        with _event_lock:
            stream = _event_streams.get(key)
            if stream is not None:
                stream.subscribers.discard(subscriber)


def clear_progress_events(conversation_id: str, request_id: str) -> None:
    with _event_lock:
        _event_streams.pop((conversation_id, request_id), None)


def _cleanup_expired_streams() -> None:
    with _event_lock:
        _cleanup_expired_streams_locked()


def _cleanup_expired_streams_locked() -> None:
    now = time.monotonic()
    expired_keys = [
        key
        for key, stream in _event_streams.items()
        if stream.expires_at is not None and stream.expires_at <= now
    ]
    for key in expired_keys:
        _event_streams.pop(key, None)


def _format_sse_event(event_name: str, data: dict[str, Any]) -> str:
    return f"event: {event_name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

