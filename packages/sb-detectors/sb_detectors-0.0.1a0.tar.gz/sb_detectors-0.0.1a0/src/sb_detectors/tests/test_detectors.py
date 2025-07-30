from .. import detectors

import pytest


def test_detector_from_name():
    detector = detectors.detector_from_name("Dectris PILATUS4 Si 4M", "ID30A1")
    assert detector is detectors.PILATUS4_4M_Si_ID30A1


def test_unknown_detector_from_name():
    with pytest.raises(
        ValueError,
        match="No detector 'Dectris PILATUS4 Si 4M' at beamline 'ID00' found.",
    ):
        _ = detectors.detector_from_name("Dectris PILATUS4 Si 4M", "ID00")
