import asyncio
import contextlib
import inspect
import logging
import pkgutil
import types
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Coroutine, Generator, Iterator, Mapping
from datetime import UTC, datetime
from typing import Any, ParamSpec, Self, cast

import fastapi.params
import pydantic
import starlette.requests

import fastapi_task_worker.task
from fastapi_task_worker import constant, rabbit
from fastapi_task_worker.base import AbstractRunner, BaseConsumer
from fastapi_task_worker.task import ScheduledTasks

logger = logging.getLogger(__name__)


class InvalidStateError(NotImplementedError):
    pass


class State(dict[str, object]):
    def __getattr__(self, name: str) -> object:
        return self[name]

    def __setattr__(self, name: str, value: object) -> None:
        self[name] = value


async def async_noop(state: State) -> None:
    pass


class TaskWorker(BaseConsumer):
    def __init__(
        self,
        rabbit_url: str,
        connection_pool_max_size: int = 10,
        channel_pool_max_size: int = 50,
        setup: Callable[[State], Coroutine[None, None, None]] | None = None,
        teardown: Callable[[State], Coroutine[None, None, None]] | None = None,
    ) -> None:
        super().__init__()
        self._mq_pool = rabbit.MQPool(
            rabbit_url,
            connection_pool_max_size=connection_pool_max_size,
            channel_pool_max_size=channel_pool_max_size,
        )

        self.state = State()
        self.setup_state = setup or async_noop
        self.teardown_state = teardown or async_noop

    async def teardown(self) -> None:
        await super().teardown()
        await self.teardown_state(self.state)
        await self._mq_pool.close()

    @property
    def queue_name(self) -> str:
        return constant.QUEUE_BACKGROUND_TASKS

    @property
    def mq_pool(self) -> rabbit.MQPool:
        return self._mq_pool

    async def setup(self) -> None:
        await super().setup()
        await self.setup_state(self.state)

    async def process(self, data: dict[str, Any]) -> None:
        logger.info("%s processing message", type(self).__name__)

        module = data["module"]
        name = data["name"]
        args = data["args"]
        kwargs = data["kwargs"]

        if args is None:
            args = ()

        if kwargs is None:
            kwargs = {}

        task = pkgutil.resolve_name(f"{module}:{name}")

        async with TaskRequest(worker=self, task=task) as task_request:
            await task_request.call(*args, **kwargs)


class TaskBeat(AbstractRunner):
    def __init__(
        self,
        rabbit_url: str,
        connection_pool_max_size: int = 10,
        channel_pool_max_size: int = 50,
    ) -> None:
        super().__init__()
        self.mq_pool = rabbit.MQPool(
            rabbit_url,
            connection_pool_max_size=connection_pool_max_size,
            channel_pool_max_size=channel_pool_max_size,
        )

    async def setup(self) -> None:
        pass

    async def teardown(self) -> None:
        await self.mq_pool.close()
        await super().teardown()

    async def run(self) -> None:
        while self.running():
            await self.tick()

            minimum_delay = self.calculate_minimum_delay()
            await asyncio.sleep(minimum_delay)

    def calculate_minimum_delay(self) -> float:
        tasks = ScheduledTasks.scheduled_tasks
        last_runs = ScheduledTasks.last_runs
        now = datetime.now(UTC)

        return min(last_runs[task] + frequency - now for task, frequency in tasks.items()).total_seconds()

    async def tick(self) -> None:
        tasks = ScheduledTasks.scheduled_tasks
        last_runs = ScheduledTasks.last_runs

        for task, frequency in tasks.items():
            if datetime.now(UTC) >= last_runs[task] + frequency:
                async with self.mq_pool.acquire() as channel:
                    launcher = fastapi_task_worker.task.TaskLauncher(channel=channel)
                    await launcher.launch_task(task)
                last_runs[task] = datetime.now(UTC)


P = ParamSpec("P")


class TaskRequest:
    def __init__(
        self,
        worker: TaskWorker,
        task: fastapi_task_worker.task.Task,
    ) -> None:
        self.task = task
        self.injectables: dict[Any, Any] = {}
        self.exit_stack: list[AsyncIterator[Any] | Iterator[Any]] = []
        self.app = worker
        self.state = State()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:
        for dependency_generator in reversed(self.exit_stack):
            if isinstance(dependency_generator, AsyncGenerator):
                with contextlib.suppress(StopAsyncIteration):
                    await anext(dependency_generator)
            elif isinstance(dependency_generator, Generator):
                with contextlib.suppress(StopIteration):
                    next(dependency_generator)
            else:
                raise InvalidStateError

    async def get_injectable(self, dependency: fastapi.params.Depends) -> object:
        if dependency in self.injectables:
            return self.injectables[dependency]

        dependency_result = await self.call_dependency(dependency)

        if isinstance(dependency_result, AsyncGenerator):
            async_dependency_generator = dependency_result
            dependency_value = await anext(async_dependency_generator)
            self.exit_stack.append(async_dependency_generator)
            self.injectables[dependency] = dependency_value
        elif isinstance(dependency_result, Generator):
            sync_dependency_generator = dependency_result
            dependency_value = next(sync_dependency_generator)
            self.exit_stack.append(sync_dependency_generator)
            self.injectables[dependency] = dependency_value
        elif inspect.iscoroutine(dependency_result):
            dependency_value = await dependency_result
            self.injectables[dependency] = dependency_value
        else:
            dependency_value = dependency_result
            self.injectables[dependency] = dependency_value

        return dependency_value

    async def get_dependencies_as_kwargs(
        self,
        parameters: Mapping[str, inspect.Parameter],
    ) -> dict[str, object]:
        kwargs: dict[str, object] = {}

        for param_name in parameters:
            param_value = parameters[param_name]
            if isinstance(param_value.annotation, type) and issubclass(
                param_value.annotation,
                starlette.requests.Request,
            ):
                kwargs[param_name] = self
                continue

            if param_value.default is not inspect.Signature.empty:
                dependency = param_value.default
            else:
                dependency = param_value.annotation.__metadata__[0]

            kwargs[param_name] = await self.get_injectable(dependency)

        return kwargs

    async def call_dependency(
        self,
        dependency: fastapi.params.Depends,
    ) -> AsyncIterator[Any]:
        if dependency.dependency is None:
            raise InvalidStateError

        signature = inspect.signature(dependency.dependency)
        kwargs = await self.get_dependencies_as_kwargs(signature.parameters)

        dependency_value = dependency.dependency(**kwargs)
        return cast("AsyncIterator[Any]", dependency_value)

    async def get_call_arguments(
        self,
        *args: object,
        **kwargs: object,
    ) -> tuple[tuple[Any, ...], dict[str, Any]]:
        signature = inspect.signature(self.task)

        # Transform kwarg values to their expected types.
        _kwargs = {key: self.transform_value(signature.parameters[key], value) for key, value in kwargs.items()}

        # Remove received kwargs from task signature parameters.
        # We can't use set operations because we must preserve the
        # parameters order.
        filtered_param_keys = [key for key in signature.parameters if key not in _kwargs]

        # Transform positional argument values too.
        _args = tuple(
            self.transform_value(signature.parameters[key], args[i])
            for i, key in enumerate(filtered_param_keys[: len(args)])
        )

        # And remove received args too
        filtered_param_keys = filtered_param_keys[len(_args) :]
        filtered_params = {key: signature.parameters[key] for key in filtered_param_keys}

        # And remove keyword arguments that have a default and are not
        # dependencies
        filtered_params = {
            key: value
            for key, value in filtered_params.items()
            if value.default is inspect.Signature.empty or isinstance(value.default, fastapi.params.Depends)
        }

        # Any remaining parameters from the task signature are assumed
        # to be dependencies that we need to inject.
        dependencies_as_kwargs = await self.get_dependencies_as_kwargs(filtered_params)
        _kwargs.update(dependencies_as_kwargs)

        return _args, _kwargs

    async def call(self, *args: object, **kwargs: object) -> None:
        _args, _kwargs = await self.get_call_arguments(*args, **kwargs)

        result = self.task(*_args, **_kwargs)

        if result is not None and inspect.iscoroutinefunction(self.task):
            await result

    def transform_value(self, parameter: inspect.Parameter, value: object) -> object:
        expeted_type = parameter.annotation

        temporal_model = pydantic.create_model(
            "TemporalModel",
            temporal_field=(expeted_type, ...),
        )
        try:
            temporal_model_instance = temporal_model(temporal_field=value)
        except pydantic.ValidationError:
            pass
        else:
            return temporal_model_instance.temporal_field  # type: ignore[attr-defined]

        msg = f"Unexpected type and value: {expeted_type=} {value=}"
        raise RuntimeError(msg)
