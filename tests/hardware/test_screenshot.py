"""Read-only hardware coverage for preset screenshots."""

import struct

import pytest


@pytest.mark.verifies("preset_screenshot")
def test_current_preset_screenshot_has_the_observed_png_dimensions(qc, profile):
    """The request is addressed from live state and does not change that state."""
    if ("4.1.0" not in profile.MEASURED_ON
            or "preset_screenshot" not in profile.VERIFIED):
        pytest.skip(f"preset_screenshot is not VERIFIED on {profile.__name__}")
    before = qc.loaded_position()
    # Do not list the setlist to decide whether the slot is empty: setlist
    # listings can be lazy and time out. The profile handles an empty currently
    # loaded slot by capturing the live display, without requesting a stored
    # preset screenshot or recalling anything.
    folder_name = before.folder_key.rstrip("/").rsplit("/", 1)[-1]
    png = qc.preset_screenshot(folder_name, before.position, before.is_factory)

    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", png[16:24]) == (800, 480), (
        "the currently loaded slot must use the live physical-screen capture, "
        "including when the slot is empty")
    assert png.endswith(b"IEND\xaeB\x60\x82")
    after = qc.loaded_position()
    assert after.folder_key == before.folder_key
    assert after.position == before.position
    assert after.is_factory == before.is_factory


@pytest.mark.verifies("preset_screenshot")
def test_other_saved_slot_screenshot_uses_the_preset_rendering(qc, profile):
    """A distinct occupied slot still uses Screenshot, not the live display."""
    if ("4.1.0" not in profile.MEASURED_ON
            or "preset_screenshot" not in profile.VERIFIED):
        pytest.skip(f"preset_screenshot is not VERIFIED on {profile.__name__}")

    before = qc.loaded_position()
    entries = qc.list_presets(before.folder_key, timeout=30.0)
    other = next((entry for entry in entries
                  if entry.index != before.position and entry.name), None)
    if other is None:
        pytest.skip("the loaded setlist has no other occupied slot to screenshot")

    folder_name = before.folder_key.rstrip("/").rsplit("/", 1)[-1]
    png = qc.preset_screenshot(folder_name, other.index, before.is_factory)

    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", png[16:24]) == (800, 384)
    assert png.endswith(b"IEND\xaeB\x60\x82")
    after = qc.loaded_position()
    assert after.folder_key == before.folder_key
    assert after.position == before.position
    assert after.is_factory == before.is_factory
