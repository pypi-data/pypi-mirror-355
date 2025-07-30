import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Annotated
from unittest import mock

import fastapi
import pydantic
import pytest
from fastapi.encoders import jsonable_encoder
from freezegun import freeze_time

from fastapi_task_worker.event import Event
from fastapi_task_worker.task import ScheduledTasks
from fastapi_task_worker.task_worker import State, TaskBeat, TaskWorker
from tests.util import QueueMessages

logger = logging.getLogger(__name__)

class DBSession:
    async def fetchval(self, _query):
        return 42


@fastapi.Depends
async def DepDatabase() -> AsyncIterator[object]:  # noqa: N802
    yield DBSession()


async def with_no_arguments_test_task() -> None:
    logger.info("No arguments")


async def with_all_worker_dependencies(
    session: Annotated[DBSession, DepDatabase],
) -> None:
    result = await session.fetchval("SELECT 42")
    logger.info(f"Result from DB {result=}")


async def with_arguments_test_task(
    positional_1: int,
    positional_2: int,
    keyword_1: str,
    keyword_2: str,
    session: Annotated[DBSession, DepDatabase],
) -> None:
    logger.info(f"Arguments: {positional_1=} {positional_2=} {keyword_1=} {keyword_2=}")
    result = await session.fetchval("SELECT 42")
    logger.info(f"Result from DB {result=}")


async def parameter_default_test_task(
    session: DBSession = DepDatabase,
) -> None:
    result = await session.fetchval("SELECT 42")
    logger.info(f"Result from DB {result=}")


def sync_test_task(argument_1: int) -> None:
    logger.info(f"Arguments: {argument_1=}")


@fastapi.Depends
async def dep_test(
    session: Annotated[DBSession, DepDatabase],
) -> int:
    yield id(session)


async def with_indirect_dependencies_test_task(
    dep_test_value: Annotated[int, dep_test],
    session: Annotated[DBSession, DepDatabase],
) -> None:
    assert dep_test_value == id(session)
    result = await session.fetchval("SELECT 42")
    logger.info(f"Result from DB {result=}")


class AnEventForTesting(Event):
    argument_1: int
    argument_2: str


class APydanticModelForTesting(pydantic.BaseModel):
    argument_1: str
    argument_2: int


async def with_pydantic_model_argument_test_task(
    model: APydanticModelForTesting,
    session: Annotated[DBSession, DepDatabase],
) -> None:
    logger.info(f"Arguments: {model=}")
    result = await session.fetchval("SELECT 42")
    logger.info(f"Result from DB {result=}")


async def with_event_argument_test_task(
    model: AnEventForTesting,
    session: Annotated[DBSession, DepDatabase],
) -> None:
    logger.info(f"Arguments: {model=}")
    result = await session.fetchval("SELECT 42")
    logger.info(f"Result from DB {result=}")


async def with_annotated_arguments(  # noqa: PLR0913
    positional_1: int,
    positional_2: Annotated[int, "__SOME_METADATA__"],
    positional_3: list[int] | None,
    keyword_1: str,
    keyword_2: Annotated[str, "__MORE_METADATA__"],
    keyword_3: list[str] | None,
    session: Annotated[DBSession, DepDatabase],
) -> None:
    logger.info(f"Arguments: {positional_1=} {positional_2=} {positional_3=}")
    logger.info(f"Arguments: {keyword_1=} {keyword_2=} {keyword_3=}")
    result = await session.fetchval("SELECT 42")
    logger.info(f"Result from DB {result=}")


async def with_optional_arguments(
    *,
    keyword_requiered_1: list[int] | None,
    keyword_optional_1: list[int] | None = None,
    keyword_optional_2: list[int] | None = None,
    session: DBSession = DepDatabase,
) -> None:
    logger.info(f"Arguments: {keyword_requiered_1=} {keyword_optional_1=} {keyword_optional_2}")
    result = await session.fetchval("SELECT 42")
    logger.info(f"Result from DB {result=}")


@fastapi.Depends
async def dep_async_generator_test() -> str:
    yield "async gen"


@fastapi.Depends
def dep_sync_generator_test() -> str:
    yield "sync gen"


@fastapi.Depends
def dep_sync_non_generator_test() -> str:
    return "sync non gen"


@fastapi.Depends
async def dep_async_non_generator_test() -> str:
    return "async non gen"


async def with_async_gen_dependency(dep: Annotated[str, dep_async_generator_test]) -> None:
    logger.info(f"{dep=}")


async def with_sync_gen_dependency(dep: Annotated[str, dep_sync_generator_test]) -> None:
    logger.info(f"{dep=}")


async def with_sync_non_gen_dependency(dep: Annotated[str, dep_sync_non_generator_test]) -> None:
    logger.info(f"{dep=}")


async def with_async_non_gen_dependency(dep: Annotated[str, dep_async_non_generator_test]) -> None:
    logger.info(f"{dep=}")


@pytest.fixture
async def task_worker(monkeypatch, mock_pool):
    monkeypatch.setattr("fastapi_task_worker.rabbit.MQPool", mock.Mock(return_value=mock_pool))
    worker = TaskWorker(
        rabbit_url="__RABBIT_URL__",
        connection_pool_max_size=10,
        channel_pool_max_size=50,
    )
    await worker.setup()

    try:
        yield worker
    finally:
        await worker.teardown()


@pytest.fixture
async def task_beat(monkeypatch, mock_pool):
    monkeypatch.setattr("fastapi_task_worker.rabbit.MQPool", mock.Mock(return_value=mock_pool))

    return TaskBeat(
        rabbit_url="__RABBIT_URL__",
        connection_pool_max_size=10,
        channel_pool_max_size=50,
    )


class TestTaskWorker:
    def test_init(self, monkeypatch):
        mock_pool = mock.Mock()
        monkeypatch.setattr("fastapi_task_worker.rabbit.MQPool", mock_pool)

        task_worker = TaskWorker(
            rabbit_url="__RABBIT_URL__",
            connection_pool_max_size=10,
            channel_pool_max_size=50,
        )

        assert isinstance(task_worker.state, State)
        assert task_worker.mq_pool == mock_pool.return_value
        assert mock_pool.call_args_list == [
            mock.call(
                "__RABBIT_URL__",
                connection_pool_max_size=10,
                channel_pool_max_size=50,
            ),
        ]

    async def test_setup(self, monkeypatch):
        mock_pool = mock.Mock()
        monkeypatch.setattr("fastapi_task_worker.rabbit.MQPool", mock_pool)
        setup_mock = mock.AsyncMock()
        worker = TaskWorker(
            rabbit_url="__RABBIT_URL__",
            connection_pool_max_size=10,
            channel_pool_max_size=50,
            setup=setup_mock,
        )

        await worker.setup()

        assert setup_mock.call_args_list == [mock.call(worker.state)]

    async def test_teardown(self, monkeypatch, mock_pool):
        monkeypatch.setattr("fastapi_task_worker.rabbit.MQPool", mock.Mock(return_value=mock_pool))
        teardown_mock = mock.AsyncMock()
        worker = TaskWorker(
            rabbit_url="__RABBIT_URL__",
            connection_pool_max_size=10,
            channel_pool_max_size=50,
            teardown=teardown_mock,
        )

        await worker.teardown()

        assert mock_pool.close.call_args_list == [mock.call()]
        assert teardown_mock.call_args_list == [mock.call(worker.state)]

    async def test_run_declares_queue(self, task_worker, mock_pool):
        mock_pool.set_message(
            {
                "module": with_no_arguments_test_task.__module__,
                "name": with_no_arguments_test_task.__name__,
                "args": None,
                "kwargs": None,
            },
            number_of_messages=1,
        )

        await task_worker.run()

        assert mock_pool.channel.declare_queue.call_args_list == [
            mock.call("fastapi_task_worker.task"),
        ]

    async def test_process_with_no_arguments(self, caplog, task_worker):
        caplog.set_level(logging.DEBUG)
        data = {
            "module": with_no_arguments_test_task.__module__,
            "name": with_no_arguments_test_task.__name__,
            "args": None,
            "kwargs": None,
        }

        await task_worker.process(data)

        assert caplog.messages == [
            "TaskWorker processing message",
            "No arguments",
        ]

    async def test_process_with_all_worker_dependencies(self, caplog, task_worker):
        caplog.set_level(logging.DEBUG)
        data = {
            "module": with_all_worker_dependencies.__module__,
            "name": with_all_worker_dependencies.__name__,
            "args": None,
            "kwargs": None,
        }

        await task_worker.process(data)

        assert caplog.messages == [
            "TaskWorker processing message",
            "Result from DB result=42",
        ]

    async def test_process_with_all_worker_dependencies_and_mailchimp_disabled(
        self,
        caplog,
        task_worker,
    ):
        caplog.set_level(logging.DEBUG)
        await task_worker.teardown()
        await task_worker.setup()
        data = {
            "module": with_all_worker_dependencies.__module__,
            "name": with_all_worker_dependencies.__name__,
            "args": None,
            "kwargs": None,
        }

        await task_worker.process(data)

        assert caplog.messages == [
            "TaskWorker processing message",
            "Result from DB result=42",
        ]

    async def test_process_with_arguments(self, caplog, task_worker):
        caplog.set_level(logging.DEBUG)
        data = {
            "module": with_arguments_test_task.__module__,
            "name": with_arguments_test_task.__name__,
            "args": (42, 53),
            "kwargs": {
                "keyword_1": "__KEYWORD_1_VALUE__",
                "keyword_2": "__KEYWORD_2_VALUE__",
            },
        }

        await task_worker.process(data)

        assert caplog.messages == [
            "TaskWorker processing message",
            "Arguments: positional_1=42 positional_2=53 "
            "keyword_1='__KEYWORD_1_VALUE__' keyword_2='__KEYWORD_2_VALUE__'",
            "Result from DB result=42",
        ]

    async def test_process_with_dependency_as_parameter_default(self, caplog, task_worker):
        caplog.set_level(logging.DEBUG)
        data = {
            "module": parameter_default_test_task.__module__,
            "name": parameter_default_test_task.__name__,
            "args": None,
            "kwargs": None,
        }

        await task_worker.process(data)

        assert caplog.messages == [
            "TaskWorker processing message",
            "Result from DB result=42",
        ]

    async def test_process_sync_task(self, caplog, task_worker):
        caplog.set_level(logging.DEBUG)
        data = {
            "module": sync_test_task.__module__,
            "name": sync_test_task.__name__,
            "args": (42,),
            "kwargs": None,
        }

        await task_worker.process(data)

        assert caplog.messages == [
            "TaskWorker processing message",
            "Arguments: argument_1=42",
        ]

    async def test_process_with_indirect_dependencies(self, caplog, task_worker):
        caplog.set_level(logging.DEBUG)
        data = {
            "module": with_indirect_dependencies_test_task.__module__,
            "name": with_indirect_dependencies_test_task.__name__,
            "args": None,
            "kwargs": None,
        }

        await task_worker.process(data)

        assert caplog.messages == [
            "TaskWorker processing message",
            "Result from DB result=42",
        ]

    async def test_process_with_pydantic_model_argument(self, caplog, task_worker):
        caplog.set_level(logging.DEBUG)
        model = APydanticModelForTesting(argument_1="__STR_VALUE__", argument_2=42)
        model_str = jsonable_encoder(model)
        data = {
            "module": with_pydantic_model_argument_test_task.__module__,
            "name": with_pydantic_model_argument_test_task.__name__,
            "args": (model_str,),
            "kwargs": None,
        }

        await task_worker.process(data)

        assert caplog.messages == [
            "TaskWorker processing message",
            "Arguments: model=APydanticModelForTesting(argument_1='__STR_VALUE__', argument_2=42)",
            "Result from DB result=42",
        ]

    async def test_process_with_event_argument(self, caplog, task_worker):
        caplog.set_level(logging.DEBUG)
        event = AnEventForTesting(argument_1=42, argument_2="__STR_VALUE__")
        event_str = jsonable_encoder(event)
        data = {
            "module": with_event_argument_test_task.__module__,
            "name": with_event_argument_test_task.__name__,
            "args": (event_str,),
            "kwargs": None,
        }

        await task_worker.process(data)

        assert caplog.messages == [
            "TaskWorker processing message",
            "Arguments: model=AnEventForTesting(argument_1=42, argument_2='__STR_VALUE__')",
            "Result from DB result=42",
        ]

    async def test_process_with_unexpected_argument_type(self, caplog, task_worker):
        caplog.set_level(logging.DEBUG)
        data = {
            "module": with_arguments_test_task.__module__,
            "name": with_arguments_test_task.__name__,
            "args": (42, "__UNEXPECTED__"),
            "kwargs": {
                "keyword_1": "__KEYWORD_1_VALUE__",
                "keyword_2": "__KEYWORD_2_VALUE__",
            },
        }

        with pytest.raises(RuntimeError) as exc:
            await task_worker.process(data)

        assert str(exc.value) == "Unexpected type and value: expeted_type=<class 'int'> value='__UNEXPECTED__'"
        assert caplog.messages == [
            "TaskWorker processing message",
        ]

    async def test_process_with_annotated_arguments(self, caplog, task_worker):
        caplog.set_level(logging.DEBUG)
        data = {
            "module": with_annotated_arguments.__module__,
            "name": with_annotated_arguments.__name__,
            "args": (42, 53, [68]),
            "kwargs": {
                "keyword_1": "__KEYWORD_1_VALUE__",
                "keyword_2": "__KEYWORD_2_VALUE__",
                "keyword_3": ["__KEYWORD_3_VALUE__"],
            },
        }

        await task_worker.process(data)

        assert caplog.messages == [
            "TaskWorker processing message",
            "Arguments: positional_1=42 positional_2=53 positional_3=[68]",
            "Arguments: keyword_1='__KEYWORD_1_VALUE__' "
            "keyword_2='__KEYWORD_2_VALUE__' keyword_3=['__KEYWORD_3_VALUE__']",
            "Result from DB result=42",
        ]

    async def test_process_with_optional_arguments(self, caplog, task_worker):
        caplog.set_level(logging.DEBUG)
        data = {
            "module": with_optional_arguments.__module__,
            "name": with_optional_arguments.__name__,
            "args": None,
            "kwargs": {
                "keyword_requiered_1": [42],
                "keyword_optional_1": [53],
            },
        }

        await task_worker.process(data)

        assert caplog.messages == [
            "TaskWorker processing message",
            "Arguments: keyword_requiered_1=[42] keyword_optional_1=[53] None",
            "Result from DB result=42",
        ]

    async def test_process_with_async_gen_dependency(self, caplog, task_worker):
        caplog.set_level(logging.DEBUG)
        data = {
            "module": with_async_gen_dependency.__module__,
            "name": with_async_gen_dependency.__name__,
            "args": None,
            "kwargs": None,
        }

        await task_worker.process(data)

        assert caplog.messages == [
            "TaskWorker processing message",
            "dep='async gen'",
        ]

    async def test_process_with_sync_gen_dependency(self, caplog, task_worker):
        caplog.set_level(logging.DEBUG)
        data = {
            "module": with_sync_gen_dependency.__module__,
            "name": with_sync_gen_dependency.__name__,
            "args": None,
            "kwargs": None,
        }

        await task_worker.process(data)

        assert caplog.messages == [
            "TaskWorker processing message",
            "dep='sync gen'",
        ]

    async def test_process_with_sync_non_gen_dependency(self, caplog, task_worker):
        caplog.set_level(logging.DEBUG)
        data = {
            "module": with_sync_non_gen_dependency.__module__,
            "name": with_sync_non_gen_dependency.__name__,
            "args": None,
            "kwargs": None,
        }

        await task_worker.process(data)

        assert caplog.messages == [
            "TaskWorker processing message",
            "dep='sync non gen'",
        ]

    async def test_process_with_async_non_gen_dependency(self, caplog, task_worker):
        caplog.set_level(logging.DEBUG)
        data = {
            "module": with_async_non_gen_dependency.__module__,
            "name": with_async_non_gen_dependency.__name__,
            "args": None,
            "kwargs": None,
        }

        await task_worker.process(data)

        assert caplog.messages == [
            "TaskWorker processing message",
            "dep='async non gen'",
        ]


@pytest.fixture(autouse=True)
def _reset_scheduled_tasks(monkeypatch):
    monkeypatch.setattr(ScheduledTasks, "scheduled_tasks", {})
    monkeypatch.setattr(ScheduledTasks, "last_runs", {})


class TestTaskBeat:
    def test_init(self, monkeypatch):
        mock_pool = mock.Mock()
        monkeypatch.setattr("fastapi_task_worker.rabbit.MQPool", mock_pool)

        task_beat = TaskBeat(
            rabbit_url="__RABBIT_URL__",
            connection_pool_max_size=10,
            channel_pool_max_size=50,
        )

        assert task_beat.stop_flag is False
        assert task_beat.mq_pool == mock_pool.return_value
        assert mock_pool.call_args_list == [
            mock.call(
                "__RABBIT_URL__",
                connection_pool_max_size=10,
                channel_pool_max_size=50,
            ),
        ]

    async def test_teardown(self, task_beat, mock_pool):
        await task_beat.teardown()

        assert task_beat.stop_flag is True
        assert mock_pool.close.call_args_list == [mock.call()]

    async def test_setup(self, monkeypatch, task_beat):
        mock_pool = mock.Mock()
        monkeypatch.setattr("fastapi_task_worker.rabbit.MQPool", mock_pool)

        await task_beat.setup()

    @pytest.mark.parametrize(
        ("scheduled_tasks", "last_runs", "expected"),
        [
            (
                [timedelta(minutes=15), timedelta(hours=1)],
                [datetime(2023, 1, 1, tzinfo=UTC), datetime.min.replace(tzinfo=UTC)],
                -63808124400.0,
            ),
            (
                [timedelta(minutes=15), timedelta(hours=1)],
                [datetime.min.replace(tzinfo=UTC), datetime.min.replace(tzinfo=UTC)],
                -63808127100.0,
            ),
            (
                [timedelta(minutes=15), timedelta(hours=1)],
                [datetime(2023, 1, 1, tzinfo=UTC), datetime(2023, 1, 1, tzinfo=UTC)],
                900.0,
            ),
            (
                [timedelta(minutes=15), timedelta(hours=1)],
                [datetime(2022, 12, 31, 23, 45, tzinfo=UTC), datetime(2023, 1, 1, tzinfo=UTC)],
                0.0,
            ),
            (
                [timedelta(minutes=15), timedelta(hours=1)],
                [datetime(2023, 1, 1, tzinfo=UTC), datetime(2022, 12, 31, 23, 0, tzinfo=UTC)],
                0.0,
            ),
        ],
    )
    @freeze_time("2023-01-01T00:00:00.0000000000+00:00")
    async def test_calculate_minimum_delay(self, scheduled_tasks, last_runs, expected, task_beat):
        for frequency, last_run in zip(scheduled_tasks, last_runs, strict=True):
            task = mock.Mock()
            ScheduledTasks.scheduled_tasks[task] = frequency
            ScheduledTasks.last_runs[task] = last_run

        result = task_beat.calculate_minimum_delay()

        assert result == expected

    @freeze_time("2023-01-01T00:00:00.0000000000+00:00")
    async def test_run_until_stopped(self, monkeypatch, task_beat):
        monkeypatch.setattr(task_beat, "running", mock.Mock(side_effect=[True, True, False]))
        monkeypatch.setattr(task_beat, "tick", mock.AsyncMock())
        monkeypatch.setattr(asyncio, "sleep", mock.AsyncMock(return_value=None))
        task = mock.Mock()
        ScheduledTasks.scheduled_tasks[task] = timedelta(seconds=0.0001)
        ScheduledTasks.last_runs[task] = datetime(2023, 1, 1, tzinfo=UTC)

        await task_beat.run()

        assert task_beat.tick.call_args_list == [mock.call()] * 2
        assert asyncio.sleep.call_args_list == [mock.call(0.0001)] * 2

    @pytest.mark.parametrize(
        ("stop_flag", "expected"),
        [
            (False, True),
            (True, False),
        ],
    )
    async def test_running(self, stop_flag, expected, task_beat):
        task_beat.stop_flag = stop_flag

        result = task_beat.running()

        assert result == expected

    @freeze_time("2023-01-01T00:00:00.0000000000+00:00")
    async def test_tick_launches_task(self, mock_pool, task_beat):
        task = mock.Mock(__name__="__TASK__")
        ScheduledTasks.scheduled_tasks[task] = timedelta(hours=42)
        ScheduledTasks.last_runs[task] = datetime(1985, 1, 1, tzinfo=UTC)

        await task_beat.tick()

        assert ScheduledTasks.scheduled_tasks[task] == timedelta(hours=42)
        assert ScheduledTasks.last_runs[task] == datetime(2023, 1, 1, tzinfo=UTC)
        assert QueueMessages(channel=mock_pool.channel).messages == [
            {
                "queue": "fastapi_task_worker.task",
                "message": {
                    "name": "__TASK__",
                    "module": "unittest.mock",
                    "args": [],
                    "kwargs": {},
                },
            },
        ]

    @freeze_time("2023-01-01T00:00:00.0000000000+00:00")
    async def test_tick_skips_recently_executed_task(self, monkeypatch, mock_pool, task_beat):
        monkeypatch.setattr("fastapi_task_worker.rabbit.MQPool", mock.Mock(return_value=mock_pool))
        task = mock.Mock(__name__="__TASK__")
        ScheduledTasks.scheduled_tasks[task] = timedelta(hours=42)
        ScheduledTasks.last_runs[task] = datetime(2023, 1, 1, tzinfo=UTC)

        await task_beat.tick()

        assert ScheduledTasks.scheduled_tasks[task] == timedelta(hours=42)
        assert ScheduledTasks.last_runs[task] == datetime(2023, 1, 1, tzinfo=UTC)
        assert QueueMessages(channel=mock_pool.channel).messages == []
