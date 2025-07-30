from bps_oculus.helpers import BaseStruct
from dataclasses import dataclass

import struct
from enum import IntEnum

s_fileHeader = 0x11223344
s_itemHeader = 0xaabbccdd
s_source = 'Oculus'


class eRecordTypes(IntEnum):
    rt_settings = 1
    rt_serialPort = 2
    rt_oculusSonar = 10
    rt_blueviewSonar = 11
    rt_rawVideo = 12
    rt_h264Video = 13
    rt_apBattery = 14
    rt_apMissionProgress = 15
    rt_nortekDVL = 16
    rt_apNavData = 17
    rt_apDvlData = 18
    rt_apAhrsData = 19
    rt_apSonarHeader = 20
    rt_rawSonarImage = 21
    rt_ahrsMtData2 = 22
    rt_apVehicleInfo = 23
    rt_apMarker = 24
    rt_apGeoImageHeader = 25
    rt_apGeoImageData = 26
    rt_sbgData = 30
    rt_ocViewInfo = 500


@dataclass
class RmLogHeader(BaseStruct):
    fileHeader: int
    sizeHeader: int
    source: str
    version: int
    encryption: int
    key: int
    time: float

    FORMAT = '<2I16s2H4xqd'

    def pack(self):
        return struct.pack(self.FORMAT, self.fileHeader, self.sizeHeader, self.source.encode(), self.version, self.encryption, self.key, self.time)


@dataclass
class RmLogItem(BaseStruct):
    itemHeader: int
    sizeHeader: int
    type: int
    version: int
    time: float
    compression: int
    originalSize: int
    payloadSize: int

    FORMAT = '<2I2H4xdH2x2I4x'  # Format string for struct (need the byte padding)
    #FORMAT = '<2I2HdH2I'

    def pack(self):
        return struct.pack(self.FORMAT, self.itemHeader, self.sizeHeader, self.type, self.version, self.time, self.compression, self.originalSize, self.payloadSize)
