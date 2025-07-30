from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Annotated
from unittest import mock

import fastapi

from fastapi_task_worker.event import Event
from fastapi_task_worker.task import ScheduledTasks, TaskLauncher
from tests.util import QueueMessages

DBSession = object


@fastapi.Depends
async def DepDatabase() -> AsyncIterator[object]:  # noqa: N802
    yield object()


async def a_test_task(
    argument_1: int,
    _session: Annotated[DBSession, DepDatabase],
) -> None:
    pass


async def test_launch_task():
    channel = mock.AsyncMock()
    launcher = TaskLauncher(channel=channel)

    await launcher.launch_task(
        a_test_task,
        argument_1="__ARGUMENT_1_VALUE__",
    )

    assert QueueMessages(channel=channel).messages == [
        {
            "queue": "fastapi_task_worker.task",
            "message": {
                "name": "a_test_task",
                "module": "tests.test_task",
                "args": [],
                "kwargs": {"argument_1": "__ARGUMENT_1_VALUE__"},
            },
        },
    ]


class ATestEvent(Event):
    internal_value: str


@ATestEvent.subscribe
async def a_test_event_listener(
    event: ATestEvent,
    _session: Annotated[DBSession, DepDatabase],
) -> None:
    pass


async def test_launch_event():
    event = ATestEvent(internal_value="__EVENT_INTERNAL_VALUE__")
    channel = mock.AsyncMock()
    launcher = TaskLauncher(channel=channel)

    await launcher.launch_event(
        event,
    )

    assert QueueMessages(channel=channel).messages == [
        {
            "queue": "fastapi_task_worker.task",
            "message": {
                "name": "a_test_event_listener",
                "module": "tests.test_task",
                "args": [{"internal_value": "__EVENT_INTERNAL_VALUE__"}],
                "kwargs": {},
            },
        },
    ]


async def test_scheduled_tasks_schedule():
    def task() -> None:
        pass

    result = ScheduledTasks.schedule(timedelta(minutes=15))(task)

    assert task in ScheduledTasks.scheduled_tasks
    assert ScheduledTasks.scheduled_tasks[task] == timedelta(minutes=15)
    assert task in ScheduledTasks.last_runs
    assert ScheduledTasks.last_runs[task] == datetime.min.replace(tzinfo=UTC)
    assert result == task
    assert result is task
