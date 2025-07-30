from typing import Iterable
from . import core
from . import filter

import asyncio
# Our default core agent


# Agents assume zero indexing.  It is the responsiblity
# of the specific *blackboard* implementation to handle any translation.
class Agent:
    def __init__(self, bb: core.Blackboard):
        self.last_read = -1
        self.bb = bb  # blackboard for the agent to talk to
        self.filters = filter.FilterBank()

    async def fetch_loop(self):
        while True:
            await asyncio.sleep(0.25)

            err = await self.fetch()
            if isinstance(err, Exception):
                return err

    def start(self) -> asyncio.Task:
        return asyncio.create_task(self.fetch_loop())

    # Fetch primes the filterbank with any new posts
    async def fetch(self) -> None | Exception:
        bb_len = await self.bb.len()
        if isinstance(bb_len, Exception):
            return bb_len

        if self.last_read + 1 == bb_len or bb_len == 0:
            return

        for i in range(self.last_read + 1, bb_len):
            post = await self.bb.read(i)

            if isinstance(post, Exception):
                return post

            await self.filters.filter(post)
            self.last_read = i

    async def listen_for(self, *tags) -> asyncio.Queue:
        tf = filter.TagFilter(*tags)
        await self.filters.insert(tf)
        return tf.outgoing()

    async def hello(self) -> None | Exception:
        post = self.bb.message_hello()
        return await self.bb.write(post)

    async def goodbye(self) -> None | Exception:
        post = self.bb.message_goodbye()
        return await self.bb.write(post)

    async def post(
        self, metadata: bytes | None, data: bytes | None, tags: Iterable[str]
    ) -> None | Exception:
        # Get a post structure from the underlying transit
        post = self.bb.new_post()

        if metadata is not None:
            post.set_metadata(metadata)
        if data is not None:
            post.set_data(data)

        post.set_tags(tags)
        return await self.bb.write(post)

    async def reply(
        self,
        posts: Iterable[core.Post],
        metadata: bytes | None,
        data: bytes | None,
        tags: Iterable[str],
    ) -> None | Exception:
        # Get a post structure from the underlying transit
        new_post = self.bb.new_post()

        reply_to = []
        for post in posts:
            reply_to.append(post.index())

        new_post.set_replying_to(reply_to)

        if metadata is not None:
            new_post.set_metadata(metadata)
        if data is not None:
            new_post.set_data(data)
        new_post.set_tags(tags)

        return await self.bb.write(new_post)
