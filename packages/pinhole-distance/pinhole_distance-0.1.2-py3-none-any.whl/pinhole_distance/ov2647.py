# ov2647.py - Submodule for OV2647 sensor parameters and utilities

from pinhole_distance.classes import Lens, Sensor, Package, DistortionTable

DISTORTION_TABLE = DistortionTable(
    {
        0.00: 0.000,
        0.05: 0.114,
        0.10: 0.227,
        0.15: 0.341,
        0.20: 0.454,
        0.25: 0.568,
        0.30: 0.681,
        0.35: 0.795,
        0.40: 0.908,
        0.45: 1.022,
        0.50: 1.135,
        0.55: 1.249,
        0.60: 1.362,
        0.65: 1.476,
        0.70: 1.589,
        0.75: 1.703,
        0.80: 1.816,
        0.85: 1.930,
        0.90: 2.043,
        0.95: 2.157,
        1.00: 2.270,
    },
    rounding_precision=0.05
)

LENS = Lens(
    focal_length_mm=9.5,
    distortion_table=DISTORTION_TABLE
)