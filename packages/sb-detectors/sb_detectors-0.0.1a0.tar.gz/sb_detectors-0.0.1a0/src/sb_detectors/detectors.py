import re
from dataclasses import dataclass


@dataclass
class Detector:
    beamline: str
    array_width: int  # pixels
    array_height: int  # pixels
    pixel_width: float  # mm
    pixel_height: float  # mm
    sensor_material: str
    sensor_thickness: float  # mm

    @property
    def array_radius(self) -> float:  # mm
        return (self.array_width**2 + self.array_height**2) ** 0.5 / 2


PILATUS_2M_ID30A1 = Detector(
    beamline="id30a1",
    array_width=1475,
    array_height=1679,
    pixel_width=0.172,
    pixel_height=0.172,
    sensor_material="Si",
    sensor_thickness=0.320,
)


PILATUS_6M_ID23EH1 = Detector(
    beamline="id23eh1",
    array_width=2463,
    array_height=2527,
    pixel_width=0.172,
    pixel_height=0.172,
    sensor_material="Si",
    sensor_thickness=0.320,
)

EIGER_4M_ID30A3 = Detector(
    beamline="id30a3",
    array_width=2070,
    array_height=2167,
    pixel_width=0.075,
    pixel_height=0.075,
    sensor_material="Si",
    sensor_thickness=0.320,
)

PILATUS4_4M_Si_ID30A1 = Detector(
    beamline="id30a1",
    array_width=2073,
    array_height=2180,
    pixel_width=0.150,
    pixel_height=0.150,
    sensor_material="Si",
    sensor_thickness=0.450,
)


def detector_from_name(name: str, beamline: str) -> Detector:
    _name = name.lower()
    _beamline = re.sub(r"[^A-Za-z0-9]", "", beamline.lower())
    if _beamline == "id30a1" and "pilatus" in _name and "2m" in _name:
        return PILATUS_2M_ID30A1
    if _beamline == "id23eh1" and "pilatus" in _name and "6m" in _name:
        return PILATUS_6M_ID23EH1
    if _beamline == "id30a3" and "eiger" in _name and "4m" in _name:
        return EIGER_4M_ID30A3
    if _beamline == "id30a1" and "pilatus4" in _name and "4m" in _name:
        return PILATUS4_4M_Si_ID30A1
    raise ValueError(f"No detector {name!r} at beamline {beamline!r} found.")
