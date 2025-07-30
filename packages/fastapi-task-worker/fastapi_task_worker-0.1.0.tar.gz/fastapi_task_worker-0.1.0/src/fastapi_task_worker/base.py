import abc
import json
import logging
import textwrap
from typing import Any

from fastapi_task_worker import rabbit

logger = logging.getLogger(__name__)


class AbstractRunner(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        self.stop_flag = False

    def running(self) -> bool:
        return not self.stop_flag

    @abc.abstractmethod
    async def setup(self) -> None:
        pass

    async def teardown(self) -> None:
        self.stop_flag = True

    @abc.abstractmethod
    async def run(self) -> None:
        while self.running():
            pass


class BaseConsumer(AbstractRunner):
    """Runner consuming trade updates and storing in the database."""

    def __init__(self) -> None:
        super().__init__()

    async def setup(self) -> None:
        pass

    @property
    @abc.abstractmethod
    def queue_name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def mq_pool(self) -> rabbit.MQPool:
        pass

    @abc.abstractmethod
    async def process(self, data: dict[str, Any]) -> None:
        pass

    async def run(self) -> None:
        logger.info("%s running", type(self).__name__)

        try:
            async with self.mq_pool.acquire() as channel:
                queue = await channel.declare_queue(self.queue_name)

                async with queue.iterator() as queue_iterator:
                    async for _message in queue_iterator:
                        if not self.running():
                            logger.info("%s no longer running", type(self).__name__)
                            break

                        async with _message.process(requeue=True):
                            message_str = _message.body.decode()
                            data = json.loads(json.loads(message_str)["message"])

                            data_repr = textwrap.shorten(repr(data), 1000)
                            logger.debug("%s received message %s", type(self).__name__, data_repr)
                            await self.process(data)
                            logger.debug("Message processed.")

        except Exception:
            logger.exception("Error processing '%s' message.", type(self).__name__)
            raise

        logger.info("%s left message loop", type(self).__name__)
