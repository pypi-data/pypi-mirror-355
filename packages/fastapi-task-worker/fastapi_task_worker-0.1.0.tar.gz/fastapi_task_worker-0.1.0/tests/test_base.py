import asyncio
from unittest import mock

import pytest

import fastapi_task_worker.base
import fastapi_task_worker.rabbit
from fastapi_task_worker.base import AbstractRunner, BaseConsumer


class BaseRunner(AbstractRunner):
    async def process(self, _message):
        await asyncio.sleep(0.0001)

    async def run(self):
        while self.running():
            await self.process("message")

    async def setup(self): ...


class TestAbstractRunner:
    def test_init(self):
        r = BaseRunner()

        assert r.stop_flag is False

    async def test_teardown(self):
        r = BaseRunner()

        await r.teardown()

        assert r.stop_flag is True

    @pytest.mark.parametrize(
        ("stop_flag", "expected"),
        [
            (False, True),
            (True, False),
        ],
    )
    def test_running(self, stop_flag, expected):
        r = BaseRunner()
        r.stop_flag = stop_flag

        result = r.running()

        assert result == expected

    async def test_run_processs_until_stopped(self, monkeypatch):
        r = BaseRunner()
        monkeypatch.setattr(r, "running", mock.Mock(side_effect=[True, True, False]))
        monkeypatch.setattr(asyncio, "sleep", mock.AsyncMock(return_value=None))

        await r.run()

        assert asyncio.sleep.call_args_list == [
            mock.call(0.0001),
            mock.call(0.0001),
        ]


class Consumer(BaseConsumer):
    def __init__(self, mq_pool: fastapi_task_worker.rabbit.MQPool) -> None:
        super().__init__()

        self._mq_pool = mq_pool

    async def process(self, message):
        await super().process(message)

        self.stop_flag = True

        if isinstance(message, Exception):
            raise message

    async def process_item(self, message):
        pass

    @property
    def queue_name(self) -> str:
        return "__QUEUE_NAME__"

    @property
    def mq_pool(self) -> fastapi_task_worker.rabbit.MQPool:
        return self._mq_pool


class TestBaseConsumer:
    def test_init(self, mock_pool):
        r = Consumer(mq_pool=mock_pool)

        assert r._mq_pool is mock_pool

    async def test_setup(self, mock_pool):
        r = Consumer(mq_pool=mock_pool)

        await r.setup()

        assert r.stop_flag is False

    async def test_teardown(self, mock_pool):
        r = Consumer(mq_pool=mock_pool)

        await r.teardown()

        assert r.stop_flag is True

    async def test_teardown_with_connected_mt5(self, mock_pool):
        r = Consumer(mq_pool=mock_pool)

        await r.teardown()

        assert r.stop_flag is True

    async def test_run_declares_queue(self, mock_pool):
        r = Consumer(mq_pool=mock_pool)

        await r.run()

        assert mock_pool.channel.declare_queue.call_args_list == [
            mock.call("__QUEUE_NAME__"),
        ]

    async def test_run_acknowledges_processed_message(self, caplog, mock_pool):
        r = Consumer(mq_pool=mock_pool)

        await r.run()

        mock_process = mock_pool.queue.msg.process
        assert caplog.messages == []
        assert mock_process.call_args_list == [mock.call(requeue=True)]
        assert mock_process.return_value.__aenter__.call_args_list == [mock.call()]
        assert mock_process.return_value.__aexit__.call_args_list == [
            # No exception raised, async context manager exit called
            # with no exception.
            mock.call(None, None, None),
        ]

    async def test_run_rejects_message_on_error(
        self,
        monkeypatch,
        caplog,
        mock_pool,
    ):
        r = Consumer(mq_pool=mock_pool)
        monkeypatch.setattr(r, "process", mock.AsyncMock(side_effect=ValueError("Oops!")))

        with pytest.raises(ValueError, match="Oops!"):
            await r.run()

        mock_process = mock_pool.queue.msg.process
        assert caplog.messages == ["Error processing 'Consumer' message."]
        assert mock_process.call_args_list == [mock.call(requeue=True)]
        assert mock_process.return_value.__aenter__.call_args_list == [mock.call()]
        assert mock_process.return_value.__aexit__.call_args_list == [
            # Exception raised, async context manager exit called with
            # type, value and trace-back.
            mock.call(ValueError, mock.ANY, mock.ANY),
        ]

    async def test_run_queue_iterator_stops(self, caplog, mock_pool):
        r = Consumer(mq_pool=mock_pool)
        mock_pool.acquire = mock.Mock()
        acquired_pool = mock_pool.acquire.return_value
        acquired_pool.__aenter__ = mock.AsyncMock(return_value=mock.Mock())
        acquired_pool.__aexit__ = mock.AsyncMock(return_value=mock.Mock())
        queue = mock.Mock()
        queue_iterator = queue.iterator.return_value
        acquired_pool.__aenter__.return_value.declare_queue = mock.AsyncMock(return_value=queue)
        queue_iterator.__aenter__ = mock.AsyncMock(return_value=mock.Mock())
        queue_iterator.__aexit__ = mock.AsyncMock(return_value=mock.Mock())
        queue_iterator.__aenter__.return_value = mock.AsyncMock()

        await r.run()

        mock_process = mock_pool.queue.msg.process
        assert caplog.messages == []
        assert mock_process.call_args_list == []
