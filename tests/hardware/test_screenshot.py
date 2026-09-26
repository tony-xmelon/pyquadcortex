"""Read-only hardware coverage for preset screenshots."""

import struct

import pytest


@pytest.mark.verifies("preset_screenshot")
def test_current_preset_screenshot_has_the_observed_png_dimensions(qc, profile):
    """The request is addressed from live state and does not change that state."""
    if "preset_screenshot" not in profile.VERIFIED:
        pytest.skip(f"preset_screenshot is not VERIFIED on {profile.__name__}")
    before = qc.loaded_position()
    # Do not list the setlist to decide whether the slot is empty: setlist
    # listings can be lazy and time out. The profile handles an empty currently
    # loaded slot by capturing the live display, without requesting a stored
    # preset screenshot or recalling anything.
    folder_name = before.folder_key.rstrip("/").rsplit("/", 1)[-1]
    png = qc.preset_screenshot(folder_name, before.position, before.is_factory)

    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", png[16:24]) in {(800, 384), (800, 480)}
    assert png.endswith(b"IEND\xaeB\x60\x82")
    after = qc.loaded_position()
    assert after.folder_key == before.folder_key
    assert after.position == before.position
    assert after.is_factory == before.is_factory
