import importlib.metadata
import lzma
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from itertools import cycle
from operator import xor
from typing import List

from sfextract import blast

__version__ = importlib.metadata.version(__package__ or __name__)

SCRIPT_FILE_NAME = "irsetup.dat".encode()


class COMPRESSION(Enum):
    UNKNOWN = 1
    NONE = 2
    PKWARE = 3
    LZMA = 4
    LZMA2 = 5


@dataclass
class SFFileEntry:
    name: str
    local_path: str
    unpacked_size: int = 0
    packed_size: int = 0
    compression: COMPRESSION = COMPRESSION.UNKNOWN
    attributes: int = 0
    crc: int = 0
    last_write_time: int = 0
    creation_time: int = 0
    is_xored: bool = False


class SetupFactoryExtractor(ABC):

    version: tuple
    files: List[SFFileEntry]

    def __init__(self, version=(-1,)):
        self.version = version
        self.files = []

    @abstractmethod
    def extract_files(self, output_location):
        raise NotImplementedError()


def xor_two_bytes(a, b):
    short, long = sorted((a, b), key=len)
    return bytes(map(xor, long, cycle(short)))


def decompress(compression: COMPRESSION, data):
    if not data:
        return data

    match compression:
        case COMPRESSION.UNKNOWN:
            raise Exception("Unknown compresssion found")
        case COMPRESSION.NONE:
            return data
        case COMPRESSION.PKWARE:
            return blast.decompress(data)
        case COMPRESSION.LZMA:
            return lzma.decompress(data)
        case COMPRESSION.LZMA2:
            # First byte contain the prop for the filters
            filters = lzma._decode_filter_properties(lzma.FILTER_LZMA2, data[0:1])
            decompressor = lzma.LZMADecompressor(lzma.FORMAT_RAW, filters=[filters])
            # Next 8 bytes contain the expected decompressed size
            return decompressor.decompress(data[9:])
        case _:
            raise Exception("No valid compression found")


class TruncatedFileError(Exception):
    """Exception thrown when data can not be read as data was expected."""
