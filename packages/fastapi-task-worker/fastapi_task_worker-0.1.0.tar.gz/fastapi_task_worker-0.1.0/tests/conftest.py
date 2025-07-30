import contextlib
import json
from unittest import mock

import pytest


class MockMessageQueue:
    def __init__(self):
        self.i = 0
        self.set_message({"messages": []}, number_of_messages=None)

    def set_message(self, message, *, number_of_messages=None):
        self._number_of_messages = number_of_messages

        body = json.dumps({"message": json.dumps(message)}).encode()
        self.msg = mock.Mock(body=body)
        self.msg.process.return_value = mock.MagicMock()

    def __aiter__(self):
        return self

    async def __anext__(self):
        self.i += 1
        if self._number_of_messages is not None and self.i > self._number_of_messages:
            raise StopAsyncIteration

        return self.msg

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        pass

    def iterator(self):
        return self


@pytest.fixture
def mock_pool():
    class MockPool:
        def __init__(self):
            self.queue = MockMessageQueue()
            self.channel = mock.Mock()
            self.channel.declare_queue = mock.AsyncMock(return_value=self.queue)
            self.channel.queue_delete = mock.AsyncMock(return_value=None)
            self.channel.default_exchange.publish = mock.AsyncMock(return_value=None)

        def set_message(self, message, *, number_of_messages=None):
            self.queue.set_message(message, number_of_messages=number_of_messages)

        @contextlib.asynccontextmanager
        async def acquire(self):
            yield self.channel

        close = mock.AsyncMock()

    return MockPool()
