#!/usr/bin/env python3
"""Primary RuneSheet transition build entrypoint.

The historical build.py remains the proven APK transformation engine.  This
wrapper composes RuneSheet-owned runtime slices around it without rewriting that
large stable file in-place.  New ownership passes graduate here one by one.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))

import dex_patch
import verify_apk
from storage_save_pass import patch_owned_local_save, verify_owned_local_save

_base_dex_patch = dex_patch.patch_exact_strings
_base_verify = verify_apk.verify


def _owned_dex_patch(dex: bytes, replacements: dict[str, str]) -> bytes:
    # Keep build.py's proven identity/data-path replacements, then apply the
    # first RuneSheet-owned runtime slice: local-only save policy + storage seam.
    return patch_owned_local_save(_base_dex_patch(dex, replacements))


def _owned_verify(apk: Path, *args, **kwargs):
    result = _base_verify(apk, *args, **kwargs)
    with zipfile.ZipFile(apk) as archive:
        result['owned_local_save'] = verify_owned_local_save(archive.read('classes2.dex'))
    return result


dex_patch.patch_exact_strings = _owned_dex_patch
verify_apk.verify = _owned_verify

# build.py imports these functions by value.  Import only after monkey-patching
# the modules so its local aliases point at the RuneSheet-owned wrappers.
import build


if __name__ == '__main__':
    build.main()
