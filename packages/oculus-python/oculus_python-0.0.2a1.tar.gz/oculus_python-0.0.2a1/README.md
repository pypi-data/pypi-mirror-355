# README

`oculus-python`, a python library for importing and exporting [Blueprint Subsea Oculus imaging sonar](https://www.blueprintsubsea.com/oculus/) log files.

## Supported log import/export types

| Type          | Import | Export |
|---------------|--------|--------|
| v1 .oculus    | X | X      |
| v2 .oculus    | X | X\*    |
| [APL ROS1](https://github.com/apl-ocean-engineering/sonar_image_proc.git)  | X | -      |
| netCDF4       | - | X      |
| HEVC .mp4     | - | X      |
| Lossless .avi | - | X      |

\* Experimental.

## Installation

`pip install oculus-python`

## CLI Usage

For these examples, assume you have a .oculus log file called "test.oculus"

Convert to NETCDF4:

`bps_oculus_io test.oculus --output netcdf4`

Convert to lossy video:

`bps_oculus_io test.oculus --output hevc --param color=True`

Convert to lossless video:

`bps_oculus_io test.oculus --output lossless --param color=True`

## Python Usage

See the [examples](https://gitlab.gbar.dtu.dk/fletho/oculus-python/-/tree/main/examples) folder for some simple usages.
