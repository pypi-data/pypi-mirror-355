from typing import Iterable
import hashlib
import binascii
import os


def quick_hash(data: bytes) -> str:
    hash = hashlib.sha256(data)
    return binascii.hexlify(hash.digest()).decode()


def random_id() -> str:
    uid = os.urandom(4)
    return quick_hash(uid)


# These are interface classes and should provide no implementation


class Post:
    # Access only (set by the server)
    def index(self) -> int:
        raise NotImplementedError

    def set_index(self, idx: int):
        raise NotImplementedError

    def timestamp(self) -> float:
        raise NotImplementedError

    # Read/Write
    def source(self) -> str:
        raise NotImplementedError

    def set_source(self, src: str):
        raise NotImplementedError

    def tags(self) -> Iterable[str]:
        raise NotImplementedError

    def set_tags(self, tags: Iterable[str]):
        raise NotImplementedError

    def replying_to(self) -> Iterable[int]:
        raise NotImplementedError

    def set_replying_to(self, replying_to: Iterable[int]):
        raise NotImplementedError

    async def metadata(self) -> bytes | Exception:
        raise NotImplementedError

    def set_metadata(self, meta: bytes):
        raise NotImplementedError

    async def data(self) -> bytes | Exception:
        raise NotImplementedError

    def set_data(self, data: bytes):
        raise NotImplementedError

    def encryption(self) -> str:
        raise NotImplementedError

    def set_encryption(self, enc: str):
        raise NotImplementedError


# "Abstract" classes that define our required
# behavior for a core python transit layer
#
# These are not true python abstract base classes, but they
# will let a user know that they haven't implemented something
# that was required for what they were trying to do.
#
# Core transit layers facilitate communication between the agent and the
# blackboard.  This includes providing some basic message types that
# are tagged appropriately to represent the basics of our core multi-agent
# communication.  These are things like a "hello" "goodbye" "post", etc.
#
# NOTE: we don't bother with the interface granularity used in
# the Go implementation. this api is to solely enable *core* agents
# If a looser base class is desired, we'll need to open a issue.


class Blackboard:
    # read, write, len are the backend blackboard interface
    # these methods carry Posts to the remotely connected
    # blackboard.
    async def read(self, idx: int) -> Post | Exception:
        raise NotImplementedError

    async def write(self, post: Post) -> None | Exception:
        raise NotImplementedError

    async def len(self) -> int | Exception:
        raise NotImplementedError

    # objects are not reeeally part of the required API, but they're
    # actually probably pretty critical to effective agent environments.
    async def put_obj(self, data: bytes) -> str | Exception:
        raise NotImplementedError

    async def get_obj(self, id: str) -> bytes | Exception:
        raise NotImplementedError

    # name and set name are "required" for a CoreBlackboard
    # this is more behavioral than anything; we want connected
    # agents to self-identify as *something*
    def name(self) -> str:
        raise NotImplementedError

    def set_name(self, name: str):
        raise NotImplementedError

    # CoreBlackboards facilitate core-style multi-agent communication
    # these methods provide the basic core message types
    def message_hello(self) -> Post:
        raise NotImplementedError

    def message_goodbye(self) -> Post:
        raise NotImplementedError

    def new_post(self) -> Post:
        raise NotImplementedError
