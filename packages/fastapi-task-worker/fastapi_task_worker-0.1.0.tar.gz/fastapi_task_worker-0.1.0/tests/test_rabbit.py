import asyncio
import contextlib
import json
import uuid
from unittest import mock

import aio_pika
import pytest

import fastapi_task_worker.rabbit
from fastapi_task_worker.rabbit import MQPool, ResponseTimeoutError, rabbit_queue, send_message


async def test_send_message(monkeypatch):
    mock_uuid = uuid.UUID("4a2a58f2-8441-45f4-a716-49a6d003ff67")
    monkeypatch.setattr(
        "fastapi_task_worker.rabbit.uuid.uuid4",
        mock.Mock(return_value=mock_uuid),
    )
    channel = mock.AsyncMock()
    channel.declare_queue.return_value.iterator = mock.Mock(
        return_value=mock.AsyncMock(),
    )
    mock_response = mock.Mock(
        ack=mock.AsyncMock(),
        body=json.dumps(json.dumps({"body": 42})).encode(),
    )
    channel.declare_queue.return_value.iterator.return_value.__aenter__.return_value.__aiter__.return_value = [
        mock_response,
    ]
    queue_name = "__QUEUE_NAME__"
    message = {}

    result = await send_message(channel, queue_name, message=message)

    assert result == json.dumps({"body": 42})
    assert channel.queue_delete.call_args_list == [mock.call(mock_uuid.hex)]
    assert channel.declare_queue.call_args_list == [
        mock.call(mock_uuid.hex, exclusive=False, arguments={}),
    ]
    [(args, kwargs)] = channel.default_exchange.publish.call_args_list
    [sent_message, sent_to_queue] = args
    assert kwargs == {}
    assert sent_to_queue == queue_name
    assert sent_message.reply_to == mock_uuid.hex
    assert sent_message.expiration is None
    assert sent_message.body == json.dumps({"message": message}).encode()
    assert channel.declare_queue.return_value.iterator.call_args_list == [
        mock.call(timeout=None),
    ]
    assert mock_response.ack.call_count == 1


async def test_send_message_with_receive_false(monkeypatch):
    mock_uuid = uuid.UUID("4a2a58f2-8441-45f4-a716-49a6d003ff67")
    monkeypatch.setattr(
        "fastapi_task_worker.rabbit.uuid.uuid4",
        mock.Mock(return_value=mock_uuid),
    )
    channel = mock.Mock(spec=aio_pika.abc.AbstractChannel)
    channel.default_exchange = mock.Mock(spec=aio_pika.abc.AbstractExchange)
    channel.declare_queue.return_value.iterator = mock.Mock(
        return_value=mock.AsyncMock(),
    )
    queue_name = "__QUEUE_NAME__"
    message = {}

    await send_message(channel, queue_name, message=message, receive=False)

    assert channel.queue_delete.call_args_list == [mock.call(mock_uuid.hex)]
    assert channel.declare_queue.call_args_list == [
        mock.call(mock_uuid.hex, exclusive=False, arguments={}),
    ]
    [(args, kwargs)] = channel.default_exchange.publish.call_args_list
    [sent_message, sent_to_queue] = args
    assert kwargs == {}
    assert sent_to_queue == queue_name
    assert sent_message.reply_to is None
    assert sent_message.expiration is None
    assert sent_message.body == json.dumps({"message": message}).encode()
    assert channel.declare_queue.return_value.iterator.call_count == 0


async def test_send_message_no_response_received(monkeypatch):
    mock_uuid = uuid.UUID("4a2a58f2-8441-45f4-a716-49a6d003ff67")
    monkeypatch.setattr(
        "fastapi_task_worker.rabbit.uuid.uuid4",
        mock.Mock(return_value=mock_uuid),
    )
    channel = mock.Mock(spec=aio_pika.abc.AbstractChannel)
    channel.default_exchange = mock.Mock(spec=aio_pika.abc.AbstractExchange)
    channel.declare_queue.return_value.iterator = mock.Mock(
        return_value=mock.AsyncMock(),
    )
    channel.declare_queue.return_value.iterator.return_value.__aiter__.return_value = []
    queue_name = "__QUEUE_NAME__"
    message = {}

    with pytest.raises(RuntimeError):
        await send_message(channel, queue_name, message=message)

    assert channel.queue_delete.call_args_list == [mock.call(mock_uuid.hex)]
    assert channel.declare_queue.call_args_list == [
        mock.call(mock_uuid.hex, exclusive=False, arguments={}),
    ]
    [(args, kwargs)] = channel.default_exchange.publish.call_args_list
    [sent_message, sent_to_queue] = args
    assert kwargs == {}
    assert sent_to_queue == queue_name
    assert sent_message.reply_to == mock_uuid.hex
    assert sent_message.expiration is None
    assert sent_message.body == json.dumps({"message": message}).encode()
    assert channel.declare_queue.return_value.iterator.call_args_list == [
        mock.call(timeout=None),
    ]


async def test_send_message_timeout_waiting_for_response(monkeypatch):
    mock_uuid = uuid.UUID("4a2a58f2-8441-45f4-a716-49a6d003ff67")
    monkeypatch.setattr(
        "fastapi_task_worker.rabbit.uuid.uuid4",
        mock.Mock(return_value=mock_uuid),
    )
    channel = mock.Mock(spec=aio_pika.abc.AbstractChannel)
    channel.default_exchange = mock.Mock(spec=aio_pika.abc.AbstractExchange)
    channel.declare_queue.return_value.iterator = mock.Mock(
        return_value=mock.AsyncMock(),
    )
    channel.declare_queue.return_value.iterator.return_value.__aenter__.return_value.__aiter__.side_effect = (
        asyncio.exceptions.TimeoutError
    )
    channel.declare_queue.return_value.name = "__DECLARED_QUEUE_NAME__"
    queue_name = "__QUEUE_NAME__"
    message = {}

    with pytest.raises(ResponseTimeoutError) as exc:
        await send_message(channel, queue_name, message=message, expiration=42.53)

    assert exc.value.timeout == 42.53
    assert exc.value.message == "__DECLARED_QUEUE_NAME__ response not received within timeout (42.53)"
    assert str(exc.value) == "__DECLARED_QUEUE_NAME__ response not received within timeout (42.53)"
    assert repr(exc.value) == (
        "ResponseTimeoutError("
        "message='__DECLARED_QUEUE_NAME__ response not received within timeout (42.53)', "
        "timeout=42.53, user_friendly_message='Timeout error')"
    )
    assert channel.queue_delete.call_args_list == [mock.call(mock_uuid.hex)]
    assert channel.declare_queue.call_args_list == [
        mock.call(mock_uuid.hex, exclusive=False, arguments={}),
    ]
    [(args, kwargs)] = channel.default_exchange.publish.call_args_list
    [sent_message, sent_to_queue] = args
    assert kwargs == {}
    assert sent_to_queue == queue_name
    assert sent_message.reply_to == mock_uuid.hex
    assert sent_message.expiration == 42.53
    assert sent_message.body == json.dumps({"message": message}).encode()
    assert channel.declare_queue.return_value.iterator.call_args_list == [
        mock.call(timeout=42.53),
    ]


async def test_rabbit_queue_optional_arguments():
    channel = mock.AsyncMock()
    queue_name = "__QUEUE_NAME__"
    dlq = "__DEAD_LETTER_ROUTING_KEY__"

    result = await rabbit_queue(
        channel=channel,
        queue_name=queue_name,
        ttl=42,
        dlq=dlq,
        exclusive=True,
    )

    assert result == channel.declare_queue.return_value
    assert channel.declare_queue.call_args_list == [
        mock.call(
            queue_name,
            exclusive=True,
            arguments={
                "x-message-ttl": 42,
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": dlq,
            },
        ),
    ]


class TestMQPool:
    def test_init_creates_pools(self, monkeypatch):
        mock_pool = mock.Mock()
        monkeypatch.setattr(fastapi_task_worker.rabbit, "Pool", mock_pool)

        pool = MQPool("rabbit_url")

        assert pool.rabbit_url == "rabbit_url"
        assert pool.connection_pool == mock_pool.return_value
        assert pool.channel_pool == mock_pool.return_value
        assert mock_pool.call_args_list == [
            mock.call(pool.get_connection, max_size=2),
            mock.call(pool.get_channel, max_size=10),
        ]

    def test_init_creates_pools_with_custom_pool_sizes(self, monkeypatch):
        mock_pool = mock.Mock()
        monkeypatch.setattr(fastapi_task_worker.rabbit, "Pool", mock_pool)

        pool = MQPool(
            "rabbit_url",
            connection_pool_max_size=7,
            channel_pool_max_size=13,
        )

        assert pool.rabbit_url == "rabbit_url"
        assert pool.connection_pool == mock_pool.return_value
        assert pool.channel_pool == mock_pool.return_value
        assert mock_pool.call_args_list == [
            mock.call(pool.get_connection, max_size=7),
            mock.call(pool.get_channel, max_size=13),
        ]

    async def test_get_connection(self, monkeypatch):
        mock_connect_robust = mock.AsyncMock(return_value=mock.Mock())
        monkeypatch.setattr(
            "fastapi_task_worker.rabbit.aio_pika.connect_robust",
            mock_connect_robust,
        )
        pool = MQPool("rabbit_url")

        channel = await pool.get_connection()

        assert channel == mock_connect_robust.return_value
        assert mock_connect_robust.call_args_list == [
            mock.call(
                pool.rabbit_url,
            ),
        ]

    async def test_get_channel(self, monkeypatch):
        pool = MQPool("rabbit_url")
        mock_channel = mock.Mock(spec=aio_pika.abc.AbstractChannel)

        class MockPool:
            @contextlib.asynccontextmanager
            async def acquire(self):
                yield mock.AsyncMock(channel=mock.AsyncMock(return_value=mock_channel))

        monkeypatch.setattr(pool, "connection_pool", MockPool())

        channel = await pool.get_channel()

        assert channel is mock_channel

    async def test_acquire(self, monkeypatch):
        pool = MQPool("rabbit_url")
        mock_channel = mock.Mock(spec=aio_pika.abc.AbstractChannel)

        class MockPool:
            @contextlib.asynccontextmanager
            async def acquire(self):
                yield mock.AsyncMock(channel=mock.AsyncMock(return_value=mock_channel))

        monkeypatch.setattr(pool, "connection_pool", MockPool())

        async with pool.acquire() as channel:
            assert channel is mock_channel

    async def test_close(self, monkeypatch):
        mock_pool = mock.Mock()
        mock_pool.return_value.close = mock.AsyncMock()
        monkeypatch.setattr(fastapi_task_worker.rabbit, "Pool", mock_pool)
        pool = MQPool("rabbit_url")

        await pool.close()

        assert mock_pool.return_value.close.call_args_list == [mock.call(), mock.call()]
