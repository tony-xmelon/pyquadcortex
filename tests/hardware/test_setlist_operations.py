"""Disposable-folder hardware checks for the profile-owned setlist shapes."""

import time
import uuid

import pytest


def _folder_named(qc, key, *, seconds=10.0):
    return next((folder for folder in qc.list_folders(seconds=seconds)
                 if folder.key.rstrip("/") == key.rstrip("/")), None)


def _wait_for_folder(qc, key, *, present, timeout=60.0):
    deadline = time.monotonic() + timeout
    while True:
        folder = _folder_named(qc, key, seconds=min(10.0, max(
            1.0, deadline - time.monotonic())))
        if (folder is not None) is present:
            return folder
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            state = "appear" if present else "disappear"
            raise AssertionError(
                f"disposable setlist {key!r} did not {state} within {timeout}s")
        time.sleep(min(2.0, remaining))


@pytest.mark.verifies("create_setlist", "delete_setlist")
def test_create_and_delete_an_empty_disposable_setlist(qc, profile):
    """Exercise both exact profile builders without touching user content.

    The only folder this test may delete is a unique, preflight-absent name
    that it just created and read back as empty. It never saves, recalls, moves,
    or deletes a preset. If DELETE has an uncertain result, it reads the folder
    state and does not replay the persistent write.
    """
    operations = ("create_setlist", "delete_setlist")
    if any(name not in profile.VERIFIED for name in operations):
        pytest.skip(f"setlist writes are not VERIFIED on {profile.__name__}")

    from pyquadcortex.protocol.client import USER_SETLIST_ROOT

    name = f"QC disposable {uuid.uuid4().hex[:12]}"
    key = f"{USER_SETLIST_ROOT}/{name}"
    assert _folder_named(qc, key) is None, (
        f"random disposable name already exists; refusing to touch {key!r}")

    create_attempted = False
    delete_attempted = False
    deleted = False
    try:
        # Set before invoking CREATE because a transport timeout can happen
        # after the device has accepted the persistent write.
        create_attempted = True
        assert qc.create_setlist(name) == key
        folder = _wait_for_folder(qc, key, present=True)
        assert folder.name == name
        assert folder.occupied == 0, (
            f"new disposable folder unexpectedly contains presets: {folder!r}; "
            "refusing to delete its contents")

        # Do not retry this write if it errors or times out. The test makes a
        # fresh listing check below and reports the exact folder if it remains.
        delete_attempted = True
        qc.delete_setlist(name)
        _wait_for_folder(qc, key, present=False)
        deleted = True
    finally:
        if create_attempted and not delete_attempted:
            # CREATE may have committed before an error. Cleanup is allowed only
            # after a fresh listing confirms this exact unique folder is empty.
            folder = _folder_named(qc, key, seconds=20.0)
            if folder is not None:
                if folder.occupied != 0:
                    pytest.fail(
                        f"created disposable folder {key!r} now contains "
                        f"{folder.occupied} presets; left untouched for manual review")
                qc.delete_setlist(name)
                _wait_for_folder(qc, key, present=False)
                deleted = True
        if delete_attempted and not deleted:
            # An uncertain DELETE is never replayed: tell the operator exactly
            # which empty test folder may need manual cleanup.
            folder = _folder_named(qc, key, seconds=10.0)
            if folder is not None:
                pytest.fail(
                    f"DELETE result was not confirmed; disposable folder "
                    f"{key!r} still appears in the fresh listing and was not "
                    "deleted a second time")
