import io
import numpy as np
import time
import zlib
import tarfile
import glob
import os
import json
import base64


def attributes(attrs: dict) -> bytes:
    return base64.b64encode(json.dumps(attrs).encode("utf-8"))


def dictionary(input: dict) -> bytes:
    return json.dumps(input).encode("utf-8")


def file(path) -> bytes:
    """
    file serializes a file on disk to binary.

    Parameters
    ----------
    path (str): path to the file.

    Returns
    -------
    bytes object containing serialized data.
    """
    with open(path, "rb") as f:
        return f.read()


def compressed_file(path: str) -> bytes:
    """
    compressed_file compresses and serializes a file on disk to binary.

    Parameters
    ----------
    path (str): path to the file.

    Returns
    -------
    bytes object containing serialized data.
    """
    with open(path, "rb") as f:
        tic = time.perf_counter()
        data = f.read()
        compressed_data = zlib.compress(data)
        compression_factor = float(len(compressed_data)) / float(len(data))
        print(
            f"compressed size: {100 * compression_factor:2.0f}% of original in {1000 * (time.perf_counter() - tic):2.0f} ms"
        )
        return compressed_data


# Numpy array, no compression
def numpy(array):
    with io.BytesIO() as bytes_buffer:
        np.save(bytes_buffer, array, allow_pickle=True)
        bytes_buffer.seek(0)
        return bytes_buffer.read()


# Numpy array, with compression (use for segmentations/masks)
def compressed_numpy(array):
    with io.BytesIO() as bytes_buffer:
        np.savez_compressed(bytes_buffer, array=array)
        bytes_buffer.seek(0)
        return bytes_buffer.read()


# We have found the concept of a dicom dir or a dicom dicom_series
# to be a generally useful unit of operation.LL
def directory(dir_path):
    with io.BytesIO() as bytes_buffer:
        with tarfile.open(None, "w:gz", fileobj=bytes_buffer) as tar:
            tar.add(dir_path, arcname=os.path.basename(dir_path))

        bytes_buffer.seek(0)
        return bytes_buffer.read()


# NOTE: the agent context serialization deserialization may
# ultimately belong elsewhere.
def agent_context(dir_path: str) -> bytes:
    """
    Pack context contained in dir_path. Return
    as bytes.
    """
    packed_data = io.BytesIO()
    with tarfile.open(mode="w:gz", fileobj=packed_data) as f:
        for fp in glob.glob(dir_path + "/*"):
            arcname = os.path.relpath(fp, dir_path)
            f.add(fp, arcname=arcname)

    packed_data.seek(0, os.SEEK_SET)
    return packed_data.read()


# if __name__ == "__main__":
#     test_data = pack_agent_context("test-dir")
#     unpack_agent_context(test_data, "./output-unpack")
