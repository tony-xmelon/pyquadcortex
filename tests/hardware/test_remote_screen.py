"""Read-only hardware coverage for the CorOS 4.1 remote screen."""

import struct

import pytest


@pytest.mark.verifies("capture_screen")
def test_capture_screen_returns_the_observed_complete_framebuffer(qc, profile):
    """Capture does not tap or otherwise mutate the device UI."""
    if "4.1.0" not in profile.MEASURED_ON or "capture_screen" not in profile.VERIFIED:
        pytest.skip(f"capture_screen is not VERIFIED on {profile.__name__}")
    png = qc.capture_screen()

    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert png[12:16] == b"IHDR"
    assert struct.unpack(">II", png[16:24]) == profile.HARDWARE.display_size
    assert png[-12:] == b"\x00\x00\x00\x00IEND\xaeB`\x82"
