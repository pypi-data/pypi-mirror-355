import logging
from collections.abc import AsyncIterator
from typing import Annotated
from unittest import mock

import fastapi

from fastapi_task_worker.event import Event
from fastapi_task_worker.task import TaskLauncher
from tests.util import QueueMessages

logger = logging.getLogger(__name__)

DBSession = object


@fastapi.Depends
async def DepDatabase() -> AsyncIterator[object]:  # noqa: N802
    yield object()


class ATestEvent(Event):
    internal_value: str


@ATestEvent.subscribe
async def a_test_event_listener(
    _event: ATestEvent,
    _session: Annotated[DBSession, DepDatabase],
) -> None:
    pass


async def test_event_listener():
    event = ATestEvent(internal_value="__EVENT_INTERNAL_VALUE__")
    channel = mock.AsyncMock()
    task_launcher = TaskLauncher(channel=channel)

    await task_launcher.launch_event(event)

    assert QueueMessages(channel=task_launcher.channel).messages == [
        {
            "queue": "fastapi_task_worker.task",
            "message": {
                "name": "a_test_event_listener",
                "module": "tests.test_event",
                "args": [{"internal_value": "__EVENT_INTERNAL_VALUE__"}],
                "kwargs": {},
            },
        },
    ]
