import struct
import typing
import ast
from abc import ABC, abstractmethod


class BaseStruct(ABC):
    FORMAT = ''

    @abstractmethod
    def pack(self):
        # Return packed data using the class-specific format
        raise NotImplementedError

    @classmethod
    def size(cls):
        return struct.calcsize(cls.FORMAT)

    @classmethod
    def unpack(cls, data):
        unpacked = struct.unpack(cls.FORMAT, data)
        return cls(*unpacked)


class Importer(ABC):

    def __init__(self):
        self._file = None
        self._metadata = None

    @property
    def metadata(self):
        return self._metadata

    @abstractmethod
    def generate(self):
        raise NotImplementedError("Override with subclass.")


def uint8_to_bits_little_endian(byte_val: int) -> typing.List[int]:
    return [(byte_val >> i) & 1 for i in range(8)]


def bits_to_uint8_little_endian(bits: typing.List[int]) -> int:
    byte_val = 0
    for i, bit in enumerate(bits):
        byte_val |= bit << i
    return byte_val


def count_struct_items(format_string: str) -> int:
    size = struct.calcsize(format_string)
    buff = b'\x01'*size
    return len(struct.unpack(format_string, buff))


def infer_type(value):
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value  # Return the original string if evaluation fails


def process_kv_pairs(kv_list: typing.Tuple[str]) -> dict:
    """Convert key=value list into dictionary with inferred types for values."""
    return {k: infer_type(v) for k, v in (item.split('=') for item in kv_list)}

ROS_RAW_MSG = """# Directly inspired by WHOI's ds_core_msgs/RawData.msg
# https://bitbucket.org/whoidsl/ds_msgs/src/master/ds_core_msgs/msg/RawData.msg
#
# Used for logging raw bytes sent to/from hardware.

std_msgs/Header header

int8 DATA_OUT=0  # Data published by the driver
int8 DATA_IN=1  # Data received by the driver

int8 direction

uint8[] data
"""
