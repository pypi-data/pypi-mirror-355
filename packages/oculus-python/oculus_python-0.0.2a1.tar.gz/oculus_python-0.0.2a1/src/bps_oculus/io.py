from bps_oculus import oculus, core, helpers, logger, _version
from pathlib import Path
import cv2
import typing
import warnings
from enum import Enum
import subprocess
from netCDF4 import Dataset
import sqlite3
from rosbags import rosbag1
from rosbags.typesys import Stores, get_typestore
from rosbags.typesys import get_types_from_msg

def process_rosbag(bagfile: Path) -> typing.Tuple[core.ItemInfo, typing.Union[
    oculus.OculusSimplePingResult, oculus.OculusSimplePingResult2], oculus.OculusPolarImage, bytes]:
    bagfile.resolve(True)
    # Plain dictionary to hold message definitions.
    add_types = get_types_from_msg(helpers.ROS_RAW_MSG, 'apl_msgs/msg/RawData')
    # Create a typestore for the matching ROS release.
    typestore = get_typestore(Stores.ROS1_NOETIC)
    typestore.register(add_types)
    with rosbag1.Reader(bagfile) as reader:
        # Topic and msgtype information is available on .connections list.
        # Iterate over messages.
        for connection, timestamp, rawdata in reader.messages():
            if connection.msgtype == 'apl_msgs/msg/RawData':
                msg = typestore.deserialize_ros1(rawdata, connection.msgtype)
                if msg.direction == msg.DATA_IN:
                    data_entry = core.unpack_data_entry(msg.data.tobytes())
                    item_info = core.ItemInfo(msg.header.seq, msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9,
                                              logger.v1.eRecordTypes.rt_oculusSonar,
                                              data_entry[
                                                  0].fireMessage.head.srcDeviceId)  # Get useful info about the item
                    yield item_info, *data_entry
                else:
                    print(oculus.OculusMessageHeader.unpack(msg.data.tobytes()[:oculus.OculusMessageHeader.size()]))


def process_v1(oculusfile: Path) -> typing.Tuple[core.ItemInfo, typing.Union[
    oculus.OculusSimplePingResult, oculus.OculusSimplePingResult2], oculus.OculusPolarImage, bytes]:
    oculusfile.resolve(True)
    with open(oculusfile, "rb") as f:
        bytes = f.read(logger.v1.RmLogHeader.size())
        header = logger.v1.RmLogHeader.unpack(bytes)

        if logger.v1.RmLogHeader.size() != header.size():
            raise ValueError("Header is incorrect size.")

        if header.sizeHeader != header.size():
            raise ValueError(f"Header is incorrect size. Got {header.size()}, should be {header.sizeHeader}")

        if header.version != 1:
            warnings.warn("Log version != 1., trying to parse anyway.", UserWarning, stacklevel=2)

        if header.fileHeader != logger.v1.s_fileHeader:
            raise ValueError("File header identifier not 0x11223344")
        v = None
        while True:
            bytes = f.read(logger.v1.RmLogItem.size())
            if len(bytes) < logger.v1.RmLogItem.size():
                break
            item = logger.v1.RmLogItem.unpack(bytes)

            if item.itemHeader != logger.v1.s_itemHeader:
                raise ValueError("Item header ID is not 0xaabbccdd.")

            if item.sizeHeader != logger.v1.RmLogItem.size():
                raise ValueError("item_message size is not a log item_message size...")
            # Read the item_message payload
            item_payload = f.read(item.payloadSize)
            data_entry = core.unpack_data_entry(item_payload)
            item_info = core.ItemInfo(data_entry[0].pingId, item.time,
                                      logger.v1.eRecordTypes.rt_oculusSonar,
                                      data_entry[0].fireMessage.head.srcDeviceId)  # Get useful info about the item
            yield item_info, *data_entry


def process_v2(oculusfile: Path) -> typing.Tuple[core.ItemInfo,
typing.Union[oculus.OculusSimplePingResult, oculus.OculusSimplePingResult2], oculus.OculusPolarImage, bytes]:
    v2_parser = logger.v2.V2LogParser(oculusfile)
    for item in logger.v2.table_fetch_iter("data", v2_parser.data):
        item_payload = item[5]
        data_entry = core.unpack_data_entry(item_payload)
        item_info = core.ItemInfo(data_entry[0].pingId, item[1] / 1000.0,
                                  logger.v1.eRecordTypes.rt_oculusSonar,
                                  item[3])
        yield item_info, *data_entry


class ExportType(Enum):
    BPSv1 = "bpsv1"
    BPSv2 = "bpsv2"
    netCDF4 = "netcdf4"
    HEVC = "hevc"
    lossless = "lossless"


class ImporterV1(helpers.Importer):
    def __init__(self, file: Path):
        super().__init__()
        self._file = file.resolve(True)
        with open(self._file, "rb") as f:
            header = logger.v1.RmLogHeader.unpack(f.read(logger.v1.RmLogHeader.size()))
        self._metadata = {"createdDateTime": header.time, "logVersion": header.version}

    def generate(self):
        yield from process_v1(self._file)


class ImporterV2(helpers.Importer):
    def __init__(self, file: Path):
        super().__init__()
        self._file = file.resolve(True)
        self._db = logger.v2.V2LogParser(file)
        self._metadata = self._db.metadata
        self._db.close()

    def generate(self):
        yield from process_v2(self._file)


class ImporterROS(helpers.Importer):
    def __init__(self, file: Path):
        super().__init__()
        self._file = file.resolve(True)
        with rosbag1.Reader(file) as bag:
            self._metadata = {"time": bag.start_time}

    def generate(self):
        yield from process_rosbag(self._file)


def convert_hevc_to_mp4(input_file: Path, output_file: Path) -> subprocess.CompletedProcess:
    cmd = [
        "ffmpeg",
        "-i", str(input_file),
        "-c", "copy",
        str(output_file)
    ]
    return subprocess.run(cmd)


def to_bpsv1(importer: helpers.Importer, oculusfile: Path, **kwargs) -> typing.Iterator[bool]:
    """
    Here we create the log message and export
    :param importer:
    :param oculusfile:
    :return:
    """
    output_file = oculusfile.with_suffix(".v1.oculus")
    with open(output_file, "wb") as f:
        for i, (item_info, item_message, item_data, new_message) in enumerate(importer.generate()):
            if i == 0:
                f.write(logger.v1.RmLogHeader(logger.v1.s_fileHeader, logger.v1.RmLogHeader.size(),
                                              'Oculus', 2, 0, 0, item_info.timestamp).pack())
            item = logger.v1.RmLogItem(logger.v1.s_itemHeader, logger.v1.RmLogItem.size(),
                                       logger.v1.eRecordTypes.rt_oculusSonar, 2, item_info.timestamp, 0,
                                       len(new_message), len(new_message))
            f.write(item.pack())
            f.write(new_message)
            yield True


def to_bpsv2(importer: helpers.Importer, oculusfile: Path, **kwargs) -> typing.Iterator[bool]:
    """
    Here we create the log message and export
    :param importer:
    :param oculusfile:
    :return:
    """
    output_file = oculusfile.with_suffix(".v2.oculus")
    # Connect to SQLite Database
    conn = sqlite3.connect(str(output_file))
    cursor = conn.cursor()

    # Create Tables
    cursor.execute('''
        CREATE TABLE metadata (
            key TEXT NOT NULL,
            value ANY NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE dataSources (
            dataSourceId INT PRIMARY KEY,
            dataSourceType INT NOT NULL,
            dataSourceName TEXT NOT NULL
        )
    ''')
    # DataSourceProperties Table
    cursor.execute('''
        CREATE TABLE dataSourceProperties (
            dataSourceId INT,
            key TEXT NOT NULL,
            value ANY NOT NULL,
            FOREIGN KEY (dataSourceId) REFERENCES dataSources (dataSourceId) 
        )
    ''')

    # Data Table
    cursor.execute('''
        CREATE TABLE data (
            entryId INTEGER PRIMARY KEY,
            timestamp INT NOT NULL,
            type INT NOT NULL,
            dataSourceId INT,
            length INT NOT NULL,
            payload BLOB NOT NULL,
            FOREIGN KEY (dataSourceId) REFERENCES dataSources (dataSourceId)
        )
    ''')

    # Resources Table
    cursor.execute('''
        CREATE TABLE resources (
            name TEXT NOT NULL,
            payload BLOB NOT NULL
        )
    ''')

    # Bookmarks Table
    cursor.execute('''
        CREATE TABLE bookmarks (
            bookmarkId INT,
            title TEXT NOT NULL,
            comments TEXT,
            FOREIGN KEY (bookmarkId) REFERENCES data (entryId)
        )
    ''')

    cursor.execute("INSERT INTO Metadata (key, value) VALUES (?, ?)", ('createdDateTime', importer.metadata['createdDateTime']))
    cursor.execute("INSERT INTO Metadata (key, value) VALUES (?, ?)", ('currentTimeZone', 'UTC'))
    cursor.execute("INSERT INTO Metadata (key, value) VALUES (?, ?)", ('applicationName', 'oculus-python'))
    cursor.execute("INSERT INTO Metadata (key, value) VALUES (?, ?)", ('applicationVersion', _version.__version__))
    cursor.execute("INSERT INTO Metadata (key, value) VALUES (?, ?)", ('logVersion', 1))
    cursor.execute("INSERT INTO Metadata (key, value) VALUES (?, ?)", ('compressionLevel', 0))
    cursor.execute("INSERT INTO DataSources (dataSourceId, dataSourceType, dataSourceName) VALUES (?, ?, ?)", (0, logger.v2.dataSourceProperties.Oculus, "Oculus"))
    conn.commit()
    for i, (item_info, item_message, item_data, new_message) in enumerate(importer.generate()):
        payload_size = core.process_raw(new_message).fireMessage.head.payloadSize
        cursor.execute("INSERT INTO Data (entryId, timestamp, type, dataSourceId, length, payload) VALUES (?, ?, ?, ?, ?, ?)",
                       (i, item_info.timestamp, 1, 0, payload_size, new_message))
        conn.commit()
        yield True
    conn.close()


def to_netcdf4(importer: helpers.Importer, oculusfile: Path, zlib: bool = False, complevel: int = 1, shuffle: bool = False, **kwargs) -> typing.Iterator[bool]:
    rootgrp = Dataset(oculusfile.with_suffix(".nc"), "w", format="NETCDF4")
    ping_dim = rootgrp.createDimension("ping", None)
    beam_dim = rootgrp.createDimension("beam", None)
    sample_dim = rootgrp.createDimension("sample", None)

    ping_var = rootgrp.createVariable("ping_number", "u8", ("ping",), zlib=zlib, complevel=complevel, shuffle=shuffle)
    time_var = rootgrp.createVariable("time", "f8", ("ping",), zlib=zlib, complevel=complevel, shuffle=shuffle)
    gain_var = rootgrp.createVariable("gain", "f4", ("ping",), zlib=zlib, complevel=complevel, shuffle=shuffle)
    gamma_var = rootgrp.createVariable("gamma", "u1", ("ping",), zlib=zlib, complevel=complevel, shuffle=shuffle)
    frequency_var = rootgrp.createVariable("frequency", "f4", ("ping",), zlib=zlib, complevel=complevel, shuffle=shuffle)
    backscatter_var = rootgrp.createVariable("backscatter", "u1", ("ping", "sample", "beam"), zlib=zlib, complevel=complevel, shuffle=shuffle)
    nbeams_var = rootgrp.createVariable("nbeams", "u2", ("ping",), zlib=zlib, complevel=complevel, shuffle=shuffle)
    azimuth_range_var = rootgrp.createVariable("azimuth_range", "f8", ("ping",), zlib=zlib, complevel=complevel, shuffle=shuffle)
    nsamples_var = rootgrp.createVariable("nsamples", "u2", ("ping",), zlib=zlib, complevel=complevel, shuffle=shuffle)
    sample_size_var = rootgrp.createVariable("sample_size", "f8", ("ping",), zlib=zlib, complevel=complevel, shuffle=shuffle)
    for i, (item_info, item_message, item_data, _) in enumerate(importer.generate()):
        ping_var[i] = item_message.pingId
        time_var[i] = item_info.timestamp
        gain_var[i] = item_message.fireMessage.gainPercent
        gamma_var[i] = item_message.fireMessage.gammaCorrection
        frequency_var[i] = item_message.frequency
        backscatter_var[i] = item_data.polar_image
        nbeams_var[i] = item_message.nBeams
        azimuth_range_var[i] = item_data.bearing_table.max() - item_data.bearing_table.min()
        nsamples_var[i] = item_message.nRanges
        sample_size_var[i] = item_message.rangeResolution
        yield True
    rootgrp.close()


def export_lossless(importer: helpers.Importer, oculusfile: Path, color: bool = False, **kwargs) -> typing.Iterator[bool]:
    lossless_file = oculusfile.with_suffix(".avi")
    v = None
    for item_info, item_message, item_data, _ in importer.generate():
        if color:
            item_data.polar_image = cv2.applyColorMap(item_data.polar_image, cv2.COLORMAP_JET)
        # Convert to cartesian coordinates
        cart_image_data = core.polar_to_cart(item_data)
        if v is None:
            height, width = cart_image_data.cart_image.shape[:2]
            v = cv2.VideoWriter(str(lossless_file),
                                cv2.VideoWriter.fourcc(*'FFV1'),
                                10.0,
                                (width, height),
                                isColor=color)
        if cart_image_data.cart_image is not None:
            v.write(cart_image_data.cart_image)
        yield True
    v.release()


def export_hevc(importer: helpers.Importer, oculusfile: Path, color: bool = False, **kwargs) -> typing.Iterator[bool]:
    hevc_file = oculusfile.with_suffix(".hevc")
    use_cuda = hasattr(cv2, "cudacodec")
    if not use_cuda:
        warnings.warn("OpenCV built without cuda, defaulting to mp4v export.", UserWarning, stacklevel=2)
    else:
        color_format = cv2.cudacodec.ColorFormat_BGR if color else cv2.cudacodec.ColorFormat_GRAY
        codec = cv2.cudacodec.HEVC
    v = None
    for item_info, item_message, item_data, _ in importer.generate():
        if color:
            item_data.polar_image = cv2.applyColorMap(item_data.polar_image, cv2.COLORMAP_JET)
        # Convert to cartesian coordinates
        cart_image_data = core.polar_to_cart(item_data)
        if v is None:
            height, width = cart_image_data.cart_image.shape[:2]
            if use_cuda:
                v = cv2.cudacodec.createVideoWriter(fileName=str(hevc_file),
                                                    frameSize=(width, height),
                                                    codec=codec,
                                                    fps=10.0,
                                                    colorFormat=color_format)
            else:
                v = cv2.VideoWriter(filename=str(hevc_file.with_suffix(".mp4")),
                                    fourcc=cv2.VideoWriter.fourcc(*"mp4v"),
                                    fps=10.0,
                                    frameSize=(width, height),
                                    isColor=color)
        if cart_image_data.cart_image is not None:
            v.write(cart_image_data.cart_image)
        yield True
    v.release()
    if use_cuda:
        convert_hevc_to_mp4(hevc_file, hevc_file.with_suffix(".mp4"))


importer = {logger.LoggerVersion.ROS1: ImporterROS,
            logger.LoggerVersion.BPSv1: ImporterV1,
            logger.LoggerVersion.BPSv2: ImporterV2}

exporter = {ExportType.BPSv1: to_bpsv1,
            ExportType.BPSv2: to_bpsv2,
            ExportType.HEVC: export_hevc,
            ExportType.netCDF4: to_netcdf4,
            ExportType.lossless: export_lossless}


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path, help="List of all files to process.")
    parser.add_argument("--output", type=str, required=True, choices=[e.value for e in ExportType],
                        help="Choose a filetype to export to.")
    parser.add_argument("--param", action="append", type=str, help="Arbitrary key-value pairs in 'key=value' format")
    args = parser.parse_args(argv)

    if args.param:
        kwargs = helpers.process_kv_pairs(args.param)
        print(kwargs)
    else:
        kwargs = {}

    for file in args.files:
        try:
            file.resolve(True)
            input_version = logger.check_oculus_log_version(file)
            output = ExportType(args.output)
        except FileNotFoundError:
            warnings.warn(f"File not found {file}, moving on.", UserWarning, stacklevel=2)
            continue
        except TypeError as e:
            warnings.warn("File is not a member of logger.LoggerVersion. Moving on.", UserWarning, stacklevel=2)
            continue
        I = importer[input_version](file)
        E = exporter[output]
        for i, _ in enumerate(E(I, file, **kwargs)):
            print(f"Processing message: {i + 1}")


if __name__ == "__main__":
    main()
