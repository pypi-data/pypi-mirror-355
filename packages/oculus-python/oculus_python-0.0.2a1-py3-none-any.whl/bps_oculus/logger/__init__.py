from enum import IntEnum
from pathlib import Path
from . import v1, v2


class LoggerVersion(IntEnum):
    ROS1 = 0
    BPSv1 = 1
    BPSv2 = 2


def check_oculus_log_version(file: Path) -> LoggerVersion:
    file.resolve(True)
    with open(file, "rb") as f:
        log_head = v1.RmLogHeader.unpack(f.read(v1.RmLogHeader.size()))
        if log_head.fileHeader == v1.s_fileHeader:
            return LoggerVersion.BPSv1
        f.seek(0)
        header = f.read(16)
        if header == b'SQLite format 3\x00':
            return LoggerVersion.BPSv2
        if header == b'#ROSBAG V2.0\nE\x00\x00':
            return LoggerVersion.ROS1
    raise TypeError(f"File {file} is not a rosbag, Oculus V1 or Oculus V2 log file.")