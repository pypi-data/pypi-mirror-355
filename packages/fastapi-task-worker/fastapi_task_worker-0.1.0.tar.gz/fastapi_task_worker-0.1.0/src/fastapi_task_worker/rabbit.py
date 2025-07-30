import asyncio
import contextlib
import json
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Any, Literal, cast, overload

import aio_pika
import aio_pika.abc
import aiormq
from aio_pika.pool import Pool
from pamqp.common import FieldTable

logger = logging.getLogger(__name__)


class MQPool:
    def __init__(
        self,
        rabbit_url: str,
        connection_pool_max_size: int = 2,
        channel_pool_max_size: int = 10,
    ) -> None:
        self.rabbit_url = rabbit_url
        self.connection_pool: Pool[aio_pika.abc.AbstractConnection] = Pool(
            self.get_connection,
            max_size=connection_pool_max_size,
        )
        self.channel_pool: Pool[aio_pika.abc.AbstractChannel] = Pool(
            self.get_channel,
            max_size=channel_pool_max_size,
        )

    async def get_connection(self) -> aio_pika.abc.AbstractConnection:
        return await aio_pika.connect_robust(self.rabbit_url)

    async def get_channel(self) -> aio_pika.abc.AbstractChannel:
        async with self.connection_pool.acquire() as connection:
            return await connection.channel()

    def acquire(
        self,
    ) -> aio_pika.pool.PoolItemContextManager[aio_pika.abc.AbstractChannel]:
        return self.channel_pool.acquire()

    async def close(self) -> None:
        await self.connection_pool.close()
        await self.channel_pool.close()


@overload
async def send_message(
    channel: aio_pika.abc.AbstractChannel,
    exclusive_queue_name: str,
    *,
    message: str,
    receive: Literal[True] = ...,
    expiration: float | None = None,
) -> str:
    pass


@overload
async def send_message(
    channel: aio_pika.abc.AbstractChannel,
    exclusive_queue_name: str,
    *,
    message: str,
    receive: Literal[False],
    expiration: float | None = None,
) -> None:
    pass


async def send_message(
    channel: aio_pika.abc.AbstractChannel,
    exclusive_queue_name: str,
    *,
    message: str,
    receive: bool = True,
    expiration: float | None = None,
) -> str | None:
    async with rabbit_response_queue(channel) as (queue, response_queue_name):
        # send a request
        rabbit_message = {"message": message}

        if receive:
            await rabbit_send(
                channel,
                exclusive_queue_name,
                rabbit_message,
                reply_to=response_queue_name,
                expiration=expiration,
            )

            logger.debug("Waiting for response on %s", response_queue_name)
            return await rabbit_recv(queue, timeout=expiration)

        await rabbit_send(
            channel,
            exclusive_queue_name,
            rabbit_message,
            expiration=expiration,
        )
        return None


@contextlib.asynccontextmanager
async def rabbit_response_queue(
    channel: aio_pika.abc.AbstractChannel,
) -> AsyncIterator[tuple[aio_pika.abc.AbstractQueue, str]]:
    queue_name = uuid.uuid4().hex

    try:
        queue = await rabbit_queue(channel, queue_name)
        yield queue, queue_name

    finally:
        await channel.queue_delete(queue_name)


async def rabbit_send(
    channel: aio_pika.abc.AbstractChannel,
    queue_name: str,
    message: dict[str, Any],
    *,
    reply_to: str | None = None,
    expiration: float | None = None,
) -> aiormq.abc.ConfirmationFrameType | None:
    rabbit_message = aio_pika.Message(
        body=json.dumps(message).encode(),
        reply_to=reply_to,
        expiration=expiration,
    )

    return await channel.default_exchange.publish(rabbit_message, queue_name)


class ResponseTimeoutError(Exception):
    def __init__(
        self,
        *,
        message: str,
        timeout: float | None,
        user_friendly_message: str,
    ) -> None:
        self.message = message
        self.timeout = timeout
        self.user_friendly_message = user_friendly_message

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        message = self.message
        timeout = self.timeout
        user_friendly_message = self.user_friendly_message
        return f"{type(self).__name__}({message=}, {timeout=}, {user_friendly_message=})"


async def rabbit_recv(
    queue: aio_pika.abc.AbstractQueue,
    timeout: float | None = None,  # noqa: ASYNC109
) -> str:
    try:
        async with queue.iterator(timeout=timeout) as iterator:
            async for message in iterator:
                await message.ack()
                result = json.loads(message.body.decode())
                return cast("str", result)
    except asyncio.exceptions.TimeoutError as exc:
        msg = f"{queue.name} response not received within timeout ({timeout})"
        user_friendly_message = "Timeout error"
        raise ResponseTimeoutError(
            message=msg,
            user_friendly_message=user_friendly_message,
            timeout=timeout,
        ) from exc

    raise RuntimeError


async def rabbit_queue(
    channel: aio_pika.abc.AbstractChannel,
    queue_name: str,
    *,
    ttl: int | None = None,
    dlq: str | None = None,
    exclusive: bool = False,
) -> aio_pika.abc.AbstractQueue:
    arguments: FieldTable = {}
    if ttl:
        # only allow messages to live this long (milliseconds)
        arguments["x-message-ttl"] = ttl

    if dlq:
        # configure a dead-letter-queue
        # use default exchange for the DLQ
        arguments["x-dead-letter-exchange"] = ""
        arguments["x-dead-letter-routing-key"] = dlq

    return await channel.declare_queue(
        queue_name,
        exclusive=exclusive,
        arguments=arguments,
    )
