import io

# from tempfile import TemporaryDirectory
import tempfile
import numpy as np
import zlib
import tarfile
import os
import json
import base64


def attributes(data: bytes) -> dict:
    return json.loads(base64.b64decode(data).decode("utf-8"))


def dictionary(data: bytes) -> dict:
    return json.loads(data.decode("utf-8"))


def file(data: bytes, save_path: str):
    """
    file writes binary data to disk. File-based deserialization
    can be useful if a library doesn't present memory-level interface.

    Parameters
    ----------
    data (bytes): serialized data to write to a file
    save_path (str): path to write the file to.
    """
    with open(save_path, "wb") as f:
        f.write(data)


def compressed_file(data: bytes, save_path: str):
    """
    compressed_file decompresses binary data using zlib and saves
    it to disk.

    Parameters
    ----------
    data (bytes): serialized data to write to a file.
    save_path (str): path to write the file to.
    """
    data = zlib.decompress(data)
    with open(save_path, "wb") as f:
        f.write(data)


def compressed_memory_file(data: bytes):
    """
    compressed_memory_file decompresses binary data using zlib and
    saves it to memory as an io.BytesIO object.

    Parameters
    ----------
    data (bytes): serialized data to decompress and write to memory.

    Returns
    -------
    Decompressed,
    """
    return io.BytesIO(zlib.decompress(data))


def memory_file(data: bytes) -> io.BytesIO:
    """
    memory_file saves binary data to memory. BytesIO behaves like
    file, but exists in memory. This is more efficient and recommended
    if it works in your use case.

    Parameters
    ----------
    data (bytes): serialized data to write to memory.

    Returns
    -------
    BytesIO-encoded data.
    """
    return io.BytesIO(data)


def numpy(data: bytes) -> np.ndarray[float]:
    """
    numpy deserializes binary data to a numpy array.

    Parameters
    ----------
    data (bytes): serialized data to write to an array.

    Returns
    -------
    np.ndarray[float] object with deserialized data.
    """
    buff = io.BytesIO(data)
    return np.load(buff, allow_pickle=True)


def compressed_numpy(data: bytes):
    """
    compressed_numpy deserializes binary data to a numpy array.
    It is the same function as numpy, but we include it to maintain
    a consistent interface.

    Parameters
    ----------
    data (bytes): serialized data to write to an array.

    Returns
    -------
    np.ndarray[float] object with deserialized data.
    """
    buff = io.BytesIO(data)
    loaded = np.load(buff, allow_pickle=True)
    return loaded["array"]


# WARN: responsibility for cleanup falls to whoever uses 'str'; could fill up some disks
def directory(data: bytes) -> str:
    tmp = tempfile.mkdtemp()

    buff = io.BytesIO(data)
    with tarfile.open(None, "r:gz", fileobj=buff) as tar:
        tar.extractall(path=tmp, filter="data")

    return tmp


# NOTE: the agent context serialization deserialization may
# ultimately belong elsewhere.
def agent_context(data: bytes, dir_path: str):
    """
    Unpack context contained in 'data' into the specified directory
    dir_path. dir_path will be created if it does not exist.
    """
    packed_data = io.BytesIO(data)
    packed_data.seek(0, os.SEEK_SET)

    with tarfile.open(mode="r:gz", fileobj=packed_data) as f:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, mode=0o775, exist_ok=True)
        f.extractall(path=dir_path)
