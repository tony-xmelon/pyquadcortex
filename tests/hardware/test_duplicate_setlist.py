"""Read/write hardware coverage for firmware-native setlist duplication."""

import time
import uuid

import pytest


FOLDER_LIST_TIMEOUT = 20.0


def _folder(qc, key):
    return next((item for item in qc.list_folders(seconds=FOLDER_LIST_TIMEOUT)
                 if item.key.rstrip("/") == key.rstrip("/")), None)


def _wait_for_folder(qc, key, *, present, timeout=90.0):
    deadline = time.monotonic() + timeout
    while True:
        result = _folder(qc, key)
        if (result is not None) is present:
            return result
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            state = "appear" if present else "disappear"
            raise AssertionError(
                f"test-owned setlist {key!r} did not {state} within {timeout}s")
        time.sleep(min(2.0, remaining))


@pytest.mark.verifies("duplicate_setlist")
def test_duplicate_setlist_copies_a_disposable_empty_setlist(qc, profile):
    """Exercise one native COPY without exposing any user preset to deletion.

    The source is a fresh empty setlist. Cleanup is limited to its exact key and
    a returned or uniquely token-named destination, and only while each still
    reads empty. The COPY is sent once by the library; this test never retries
    it after an uncertain result.
    """
    from pyquadcortex.protocol.client import (
        QuadCortex, USER_SETLIST_ROOT, _is_user_setlist_key,
    )

    if profile.duplicate_setlist is QuadCortex.duplicate_setlist:
        pytest.skip(
            f"native duplicate_setlist is unavailable on {profile.__name__}")

    token = uuid.uuid4().hex[:12]
    source_name = f"QCdup-{token}"
    source_key = f"{USER_SETLIST_ROOT}/{source_name}"
    assert _folder(qc, source_key) is None, (
        f"random disposable source already exists; refusing to touch {source_key!r}")

    create_attempted = False
    copy_attempted = False
    destination = None
    copy_baseline: set[str] = set()
    try:
        # CREATE may have committed before a reply/readback problem, so cleanup
        # owns the exact generated name from immediately before the call.
        create_attempted = True
        assert qc.create_setlist(source_name) == source_key
        source = _wait_for_folder(qc, source_key, present=True)
        assert source is not None and source.name == source_name
        assert source.occupied == 0, (
            f"new disposable source unexpectedly contains presets: {source!r}; "
            "refusing to duplicate or delete it")

        copy_baseline = {
            item.key for item in qc.list_folders(seconds=FOLDER_LIST_TIMEOUT)
        }
        assert source_key in copy_baseline, (
            "source disappeared before COPY preflight; refusing to send")

        copy_attempted = True
        destination = qc.duplicate_setlist(
            source_name, timeout=180.0, interval=1.0)
        assert destination.key not in copy_baseline
        assert not destination.is_factory
        assert destination.occupied == 0, (
            f"duplicate of an empty source is unexpectedly occupied: {destination!r}")
    finally:
        if create_attempted:
            folders = qc.list_folders(seconds=FOLDER_LIST_TIMEOUT)
            source_key_normalized = source_key.rstrip("/")
            destination_key = (destination.key.rstrip("/")
                               if destination is not None else None)
            owned = [item for item in folders
                     if item.key.rstrip("/") == source_key_normalized
                     or (destination_key is not None
                         and item.key.rstrip("/") == destination_key)
                     or (copy_attempted and token in (item.name + item.key)
                         and not item.is_factory
                         and _is_user_setlist_key(item.key)
                         and item.key not in copy_baseline)]
            unidentified = [item for item in folders
                            if copy_attempted
                            and item.key not in copy_baseline
                            and item.key.rstrip("/") != source_key_normalized
                            and (destination_key is None
                                 or item.key.rstrip("/") != destination_key)
                            and token not in (item.name + item.key)
                            and _is_user_setlist_key(item.key)
                            and not item.is_factory]

            for item in reversed(owned):
                if item.occupied != 0:
                    pytest.fail(
                        f"test-owned setlist {item.key!r} unexpectedly contains "
                        f"{item.occupied} presets; left untouched for manual review")
                # Do not replay DELETE if read-back is uncertain; report the
                # exact empty test folder still present instead.
                qc.delete_setlist(item.name)
                if _folder(qc, item.key) is not None:
                    pytest.fail(
                        f"DELETE was not confirmed for disposable test folder "
                        f"{item.key!r}; it was not sent a second time")
            if unidentified:
                names = ", ".join(
                    f"{item.name!r} ({item.key!r})" for item in unidentified)
                pytest.fail(
                    "COPY may have created a folder without the unique source "
                    f"token, so it was left untouched for manual review: {names}")
