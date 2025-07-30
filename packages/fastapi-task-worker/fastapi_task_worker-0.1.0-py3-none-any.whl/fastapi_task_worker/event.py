from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import ClassVar

import pydantic

EventListener = Callable[..., None | Coroutine[None, None, None]]


class Event(pydantic.BaseModel):
    subscribers: ClassVar[dict[type["Event"], list[EventListener]]] = defaultdict(list)

    @classmethod
    def subscribe(cls, task: EventListener) -> EventListener:
        cls.subscribers[cls].append(task)
        return task
