from . import core
from .hardcore_post import Post
import json
import asyncio
import aiohttp
import base64

# John: you have some clarifications to make around what the input to this
# layer is and whether or not we case use knowledge of the underlying
# post type here.  I think if we do, it kind of undermines the entire
# premise of breaking this into a separate layer, but there's also
# no way around it in something like the new_post method: the bb has
# to have some awareness of what it's talking to, but only minimally (I think
# why I'm having trouble answering this question in the first place).


class HTTPTransit(core.Blackboard):
    read_path = "/read/{0}"
    write_path = "/write"
    len_path = "/len"
    put_obj_path = "/obj"
    get_obj_path = "/obj/{0}"

    def __init__(self, bb_addr: str):
        self._name = "http-transit"
        self.addr = bb_addr
        self.session = aiohttp.ClientSession()

    def __del__(self):
        """
        Destructor for BlackboardHTTPClient class.
        """
        asyncio.create_task(self.session.close())

    # A little bit of future-proofing to allow for easily changed common url
    # components
    def _get_url(self, path: str):
        return "http://" + self.addr + path

    # Our transit layers need to be identifiable
    def name(self) -> str:
        return self._name

    def set_name(self, name: str):
        self._name = name

    # This is core-specific means of handling data and metadata.
    # The client/agent pushes data into the object store first
    # and then passes on the link in the final message to the BB.
    async def put_obj(self, data: bytes) -> str | Exception:
        url = self._get_url(self.put_obj_path)

        async with self.session.post(url, data=data) as response:
            if response.status != 200:
                return RuntimeError("object upload failed")

            # form the url other agents can use to retrieve the data
            oid = await response.text()
            get_url = self._get_url(self.get_obj_path.format(oid))
            return get_url

    # For an http blackboard, the id is a url on which we can call "get"
    async def get_obj(self, id: str) -> bytes | Exception:
        async with self.session.get(id) as response:
            if response.status != 200:
                return RuntimeError("object upload failed")

            return await response.content.read()

    # Fulfill the required NotImplementedError class methods
    async def read(self, idx: int) -> core.Post | Exception:
        url = self._get_url(self.read_path.format(idx))

        async with self.session.get(url) as response:
            if response.status != 200:
                # TODO: This exc probably not complete enough to be very useful
                msg = await response.text()
                status_message = f"{response.status} {msg}"
                return RuntimeError(f"read failed; status: {status_message}")

            body = await response.text()
            msg = json.loads(body)

            # Unwrap the json dictionary into a post instance
            # Data and metadata come to us as base64 encoded strings
            # p = self.new_post()

            p = Post.from_dict(msg)
            p.bb = self

            return p

    async def write(self, post: core.Post) -> None | Exception:
        # TODO: encryption should be enforced here
        url = self._get_url(self.write_path)

        post_dict = {}
        post_dict["index"] = post.index()
        post_dict["source"] = post.source()
        post_dict["timestamp"] = post.timestamp()
        post_dict["tags"] = post.tags()
        post_dict["replying_to"] = post.replying_to()
        # post_dict["metadata"] = base64.b64encode(metadata_url).decode()
        # post_dict["data"] = base64.b64encode(data).decode()
        post_dict["encryption"] = post.encryption()

        # Perform our data stripping on the client side
        data = await post.data()
        if isinstance(data, Exception):
            err = data
            return err

        if len(data) != 0:
            data_url = await self.put_obj(data)
            if isinstance(data_url, Exception):
                return data_url
            post_dict["data"] = base64.b64encode(data_url.encode()).decode()

        # Perform our data stripping on the client side
        m_data = await post.metadata()
        if isinstance(m_data, Exception):
            err = m_data
            return err

        if len(m_data) != 0:
            metadata_url = await self.put_obj(m_data)
            if isinstance(metadata_url, Exception):
                return metadata_url
            post_dict["metadata"] = base64.b64encode(
                metadata_url.encode()).decode()

        # sigh
        msg_json = json.dumps(post_dict)
        payload = msg_json.encode("utf-8")

        async with self.session.post(
            url,
            data=payload,
            headers={
                "content-type": "application/json",
                "content-length": str(len(payload)),
            },
        ) as response:
            if response.status != 201:
                msg = await response.text()
                status_message = f"{response.status} {msg}"
                return RuntimeError(f"write failed; status: {status_message}")

    async def len(self) -> int | Exception:
        url = self._get_url(self.len_path)

        async with self.session.get(url) as response:
            if response.status != 200:
                msg = await response.text()
                status_message = f"{response.status} {msg}"
                return RuntimeError(f"len failed; status: {status_message}")

            body = await response.text()
            len_str = body.strip()
            if not len_str.isdigit():
                return RuntimeError(f"non-numeric length response: {len_str}")

            return int(len_str)

    def new_post(self) -> core.Post:
        p = Post()
        p.bb = self
        p.set_source(self._name)
        return p
