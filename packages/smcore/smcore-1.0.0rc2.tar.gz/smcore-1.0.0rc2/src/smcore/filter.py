import asyncio
from typing import Iterable
from . import core
from .tag_set import TagSet


class Filter:
    async def filter(self, post: core.Post) -> None | Exception:
        raise NotImplementedError

    def outgoing(self) -> asyncio.Queue:
        raise NotImplementedError


class TagFilter(Filter):
    def __init__(self, tags: Iterable[str]):
        self.tags = tags
        self.tag_set = TagSet(tags)
        self.outgoing_ch = asyncio.Queue()

    # In the go implementation we return an error if the filter
    # does NOT match the incoming post.  There's no similar
    # 1 to 1 code replacement here so we use the union trick that
    # is meh
    async def filter(self, post: core.Post) -> None | Exception:
        incoming_tags = TagSet(post.tags())

        if not self.tag_set.matches(incoming_tags):
            return Exception("message was filtered")

        await self.outgoing_ch.put(post)

    def outgoing(self) -> asyncio.Queue:
        return self.outgoing_ch


class FilterBank:
    def __init__(self, filters=None):
        self.lock = asyncio.Lock()
        self.filters = []
        if filters is not None:
            self.filters = filters

    async def len(self) -> int:
        async with self.lock:
            return len(self.filters)

    async def insert(self, filt: Filter):
        async with self.lock:
            self.filters.append(filt)

    # Run a post through the filter bank, populating
    # the outgoing channels that match
    async def filter(self, post: core.Post):
        async with self.lock:
            for filt in self.filters:
                await filt.filter(post)
