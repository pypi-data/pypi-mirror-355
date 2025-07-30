import struct
from enum import IntEnum
from dataclasses import dataclass, field, astuple
from bps_oculus.helpers import BaseStruct, count_struct_items
import numpy as np


OCULUS_CHECK_ID = 0x4f53


class OculusMessageType(IntEnum):
    messageSimpleFire = 0x15
    messagePingResult = 0x22
    messageSimplePingResult = 0x23
    messageUserConfig = 0x55
    messageDummy = 0xff


class PingRateType(IntEnum):
    pingRateNormal = 0x00
    pingRateHigh = 0x01
    pingRateHighest = 0x02
    pingRateLow = 0x03
    pingRateLowest = 0x04
    pingRateStandby = 0x05
    ## TODO At the moment unpacking PingRateType byte breaks, since it usually is 165 for some reason (possibly unknown?)
    ##  in this case I will simply make a pingRateUnknown = 0xa5 enum until this is resolved.
    pingRateUnknown = 0xa5


class DataSizeType(IntEnum):
    dataSize8Bit = 0x00
    dataSize16Bit = 0x01
    dataSize24Bit = 0x02
    dataSize32Bit = 0x03


@dataclass
class OculusMessageHeader(BaseStruct):
    oculusId: int
    srcDeviceId: int
    dstDeviceId: int
    msgId: int
    msgVersion: int
    payloadSize: int
    spare2: int

    FORMAT = '<5HIH'  # Format string for struct (16 bytes)

    def pack(self):
        return struct.pack(self.FORMAT, *astuple(self))


@dataclass
class OculusSimpleFireMessage(BaseStruct):
    head: OculusMessageHeader
    masterMode: int
    pingRate: PingRateType
    networkSpeed: int
    gammaCorrection: int
    flags: int
    range: float
    gainPercent: float
    speedOfSound: float
    salinity: float

    FORMAT = OculusMessageHeader.FORMAT + '5B4d'  # 53 Bytes

    @classmethod
    def unpack(cls, data: bytes):
        unpacked = struct.unpack(cls.FORMAT, data)
        header = OculusMessageHeader(*unpacked[:7])
        unpacked = (header,) + unpacked[7:]
        unpacked = unpacked[:2] + (PingRateType(unpacked[2]), ) + unpacked[3:]
        return cls(*unpacked)


@dataclass
class OculusSimpleFireMessage2(BaseStruct):
    head: OculusMessageHeader
    masterMode: int
    pingRate: PingRateType
    networkSpeed: int
    gammaCorrection: int
    flags: int
    rangePercent: float
    gainPercent: float
    speedOfSound: float
    salinity: float
    extFlags: int
    reserved: tuple = field(default_factory=tuple)

    FORMAT = OculusMessageHeader.FORMAT + '5B4d9I'  # 89 Bytes

    def pack(self):
        items = astuple(self)[1:]
        items = items[:-1] + (*items[-1],)
        return self.head.pack() + struct.pack("<"+self.FORMAT[len(self.head.FORMAT):], *items)

    # Add custom unpack (due to enum type conversion)
    @classmethod
    def unpack(cls, data: bytes):
        unpacked = struct.unpack(cls.FORMAT, data)
        header = OculusMessageHeader(*unpacked[:7])
        unpacked = (header,) + unpacked[7:]
        unpacked = unpacked[:2] + (PingRateType(unpacked[2]), ) + unpacked[3:]
        unpacked = unpacked[:-8] + (unpacked[-8:],)
        return cls(*unpacked)


@dataclass
class OculusSimplePingResult(BaseStruct):
    fireMessage: OculusSimpleFireMessage
    pingId: int
    status: int
    frequency: float
    temperature: float
    pressure: float
    speedOfSoundUsed: float
    pingStartTime: float
    dataSize: DataSizeType
    rangeResolution: float
    nRanges: int
    nBeams: int
    imageOffset: int
    imageSize: int
    messageSize: int

    FORMAT = OculusSimpleFireMessage.FORMAT + '2I4dIBd2H3I'  # 122 bytes

    @classmethod
    def unpack(cls, data):
        firemessage = OculusSimpleFireMessage.unpack(data[:OculusSimpleFireMessage.size()])
        idx = count_struct_items(firemessage.FORMAT)
        unpacked = (firemessage,) + struct.unpack(cls.FORMAT, data)[idx:]
        unpacked = unpacked[:8] + (DataSizeType(unpacked[8]),) + unpacked[9:]
        return cls(*unpacked)


@dataclass
class OculusSimplePingResult2(BaseStruct):
    fireMessage: OculusSimpleFireMessage2
    pingId: int
    status: int
    frequency: float
    temperature: float
    pressure: float
    heading: float
    pitch: float
    roll: float
    speedOfSoundUsed: float
    pingStartTime: float
    dataSize: DataSizeType
    rangeResolution: float
    nRanges: int
    nBeams: int
    spare0: int
    spare1: int
    spare2: int
    spare3: int
    imageOffset: int
    imageSize: int
    messageSize: int

    FORMAT = OculusSimpleFireMessage2.FORMAT + 'II8dBd2H7I'  # 202 bytes

    # Add custom unpack (due to enum type conversion)
    @classmethod
    def unpack(cls, data):
        firemessage = OculusSimpleFireMessage2.unpack(data[:OculusSimpleFireMessage2.size()])
        idx = count_struct_items(firemessage.FORMAT)
        unpacked = (firemessage, ) + struct.unpack(cls.FORMAT, data)[idx:]
        unpacked = unpacked[:11] + (DataSizeType(unpacked[11]), ) + unpacked[12:]
        return cls(*unpacked)

    def pack(self):
        return self.fireMessage.pack() + struct.pack("<"+self.FORMAT[len(self.fireMessage.FORMAT):], *astuple(self)[1:])


@dataclass
class PingConfig(BaseStruct):
    b0: int
    d0: float
    range: float
    d2: float
    d3: float
    d4: float
    d5: float
    d6: float
    nBeams: int
    d7: float
    b1: int
    b2: int
    b3: int
    b4: int
    b5: int
    b6: int
    u0: int
    b7: int
    b8: int
    b9: int
    b10: int
    b11: int
    b12: int
    b13: int
    b14: int
    b15: int
    b16: int
    u1: int

    FORMAT="<B7dHd6BH10BH"


@dataclass
class OculusReturnFireMessage(BaseStruct):

    def __init__(cls, *args, **kwargs):
        raise NotImplementedError("OculusReturnFireMessage not available in this version.")

    @classmethod
    def unpack(cls, data):
        raise NotImplementedError("OculusReturnFireMessage not available in this version.")


@dataclass
class OculusPolarImage:
    polar_image: np.ndarray
    bearing_table: np.ndarray
    ranging_table: np.ndarray
    gain_table: np.ndarray


@dataclass
class OculusCartImage:
    cart_image: np.ndarray
    x_table: np.ndarray
    y_table: np.ndarray


def enum_DataSizeType_to_size(value: DataSizeType) -> int:
    return value.value + 1


def enum_DataSizeType_to_np(value: DataSizeType) -> np.dtype:
    if value == DataSizeType.dataSize8Bit:
        return np.uint8
    elif value == DataSizeType.dataSize16Bit:
        return np.uint16
    elif value == DataSizeType.dataSize24Bit:
        raise NotImplementedError("Dunno how to convert to 24 bit integer / float in numpy.")
    elif value == DataSizeType.dataSize32Bit:
        return np.uint32
    raise ValueError(f"value not a member of DataSizeType")

