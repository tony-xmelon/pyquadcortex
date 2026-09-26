"""Read-only hardware coverage for preset screenshots."""

import struct

import pytest


@pytest.mark.verifies("preset_screenshot")
def test_current_preset_screenshot_has_the_observed_png_dimensions(qc, profile):
    """The request is addressed from live state and does not change that state."""
    if "preset_screenshot" not in profile.VERIFIED:
        pytest.skip(f"preset_screenshot is not VERIFIED on {profile.__name__}")
    before = qc.loaded_position()
    folders = qc.list_folders(seconds=20.0)
    folder = next((item for item in folders
                   if item.key.rstrip("/") == before.folder_key.rstrip("/")), None)
    assert folder is not None, f"listing omitted loaded folder {before.folder_key!r}"
    assert folder.name, f"loaded folder {before.folder_key!r} has no display name"

    # An empty user slot has no stored preset to render and the unit does not
    # answer Screenshot{READ} for it. Prefer the loaded slot when occupied; if
    # the owner has an empty slot loaded, use an existing saved slot in the same
    # setlist without recalling it or changing the grid.
    entries = qc.list_presets(folder.key, timeout=25.0)
    address = next((item.index for item in entries
                    if item.index == before.position), None)
    if address is None:
        address = next((item.index for item in entries if item.name), None)
    if address is None:
        pytest.skip("the loaded setlist has no saved preset to screenshot")

    png = qc.preset_screenshot(folder.name, address, before.is_factory)

    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", png[16:24]) == (800, 384)
    assert png.endswith(b"IEND\xaeB\x60\x82")
    after = qc.loaded_position()
    assert after.folder_key == before.folder_key
    assert after.position == before.position
    assert after.is_factory == before.is_factory
