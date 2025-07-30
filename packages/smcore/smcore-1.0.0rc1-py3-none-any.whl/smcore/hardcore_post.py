import base64
from . import core
from typing import Iterable


class Post(core.Post):
    def __init__(self):
        self._index = 0
        self._source = ""
        self._timestamp = 0.0
        self._replying_to = []
        self._tags = []
        self._m_retrieved = False
        self._metadata = b""
        self._d_retrieved = False
        self._data = b""
        self._encryption = "aes-gcm"
        self.bb = core.Blackboard()

    # TODO: This may need to do error handling
    # also, how to return a concrete Post with type hints?
    @classmethod
    def from_dict(cls, d: dict):
        p = Post()
        p._index = d["index"]
        p._source = d["source"]
        p._timestamp = d["timestamp"]
        p._replying_to = d["replying_to"]
        p._tags = d["tags"]
        if d["metadata"] is not None:
            p._metadata = base64.b64decode(d["metadata"])
        if d["data"] is not None:
            p._data = base64.b64decode(d["data"])
        p._encryption = d["encryption"]
        return p

    # Access only (set by the server)
    def index(self) -> int:
        return self._index

    def set_index(self, idx: int):
        self._index = idx

    def timestamp(self) -> float:
        return self._timestamp

    # Read/Write
    def source(self) -> str:
        return self._source

    def set_source(self, src: str):
        self._source = src

    def tags(self) -> Iterable[str]:
        return self._tags

    def set_tags(self, tags: Iterable[str]):
        self._tags = tags

    def replying_to(self) -> Iterable[int]:
        return self._replying_to

    def set_replying_to(self, replying_to: Iterable[int]):
        self._replying_to = replying_to

    async def metadata(self) -> bytes | Exception:
        if len(self._metadata) == 0 or self._m_retrieved:
            return self._metadata

        # Retrieve the underlying data using the embedded transit
        obj_id = self._metadata.decode()
        metadata_or_err = await self.bb.get_obj(obj_id)
        if isinstance(metadata_or_err, Exception):
            return metadata_or_err

        self._metadata = metadata_or_err
        self._m_retrieved = True

        return self._metadata

    def set_metadata(self, meta: bytes):
        self._metadata = meta
        self._m_retrieved = True

    async def data(self) -> bytes | Exception:
        if len(self._data) == 0 or self._d_retrieved:
            return self._data
        #
        # Retrieve the underlying data using the embedded transit
        obj_id = self._data.decode()
        data_or_err = await self.bb.get_obj(obj_id)
        if isinstance(data_or_err, Exception):
            return data_or_err

        self._data = data_or_err
        self._d_retrieved = True

        return self._data

    def set_data(self, data: bytes):
        self._data = data
        self._d_retrieved = True

    def encryption(self) -> str:
        return self._encryption

    def set_encryption(self, enc: str):
        self._encryption = enc
