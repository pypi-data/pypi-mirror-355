import json
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime, timedelta
from typing import ClassVar

import aio_pika
from fastapi.encoders import jsonable_encoder

import fastapi_task_worker.event
from fastapi_task_worker import constant, rabbit

Task = Callable[..., None | Coroutine[None, None, None]]


class TaskLauncher:
    def __init__(self, channel: aio_pika.abc.AbstractChannel) -> None:
        self.channel = channel

    async def launch_task(
        self,
        task: Task,
        *args: object,
        **kwargs: object,
    ) -> None:
        message = {
            "module": task.__module__,
            "name": task.__name__,
            "args": args,
            "kwargs": kwargs,
        }

        await rabbit.send_message(
            channel=self.channel,
            exclusive_queue_name=constant.QUEUE_BACKGROUND_TASKS,
            message=json.dumps(jsonable_encoder(message)),
            receive=False,
            expiration=None,
        )

    async def launch_event(
        self,
        event: fastapi_task_worker.event.Event,
    ) -> None:
        for subscriber_task in fastapi_task_worker.event.Event.subscribers[type(event)]:
            await self.launch_task(
                subscriber_task,
                event,
            )


ScheduledHandler = Callable[..., None | Coroutine[None, None, None]]


class ScheduledTasks:
    scheduled_tasks: ClassVar[dict[ScheduledHandler, timedelta]] = {}
    last_runs: ClassVar[dict[ScheduledHandler, datetime]] = {}

    @classmethod
    def schedule(cls, frequency: timedelta) -> Callable[[ScheduledHandler], ScheduledHandler]:
        def inner(task: ScheduledHandler) -> ScheduledHandler:
            cls.scheduled_tasks[task] = frequency
            cls.last_runs[task] = datetime.min.replace(tzinfo=UTC)
            return task

        return inner
