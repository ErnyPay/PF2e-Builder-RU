#!/usr/bin/env python3
"""Primary RuneSheet transition build entrypoint.

This entrypoint is intentionally launch-safe. Runtime/Dex ownership experiments
must not run here unless they have passed device smoke-tests. Release hardening
is limited to manifest/resources and keeps executable DEX on the proven baseline.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts'))

import owned_shell_pass
import ownership_runtime_pass
from release_hardening import RELEASE_LAYOUT_PATHS, harden_release_manifest, patch_release_layout

_base_layout_patch = owned_shell_pass.patch_owned_shell_layout
_base_runtime_hardening = ownership_runtime_pass.harden_owned_runtime

# build.py only runs the owned-shell hook for paths listed here. Extend that
# pinned set to the small RC2 resource-hardening surface before importing build.
for _path in RELEASE_LAYOUT_PATHS:
    owned_shell_pass.LAYOUT_REPLACEMENTS.setdefault(_path, {})


def _release_layout_patch(path: str, blob: bytes) -> bytes:
    return patch_release_layout(path, _base_layout_patch(path, blob))


def _release_runtime_hardening(blob: bytes, *, application_id: str) -> bytes:
    return harden_release_manifest(
        _base_runtime_hardening(blob, application_id=application_id)
    )


owned_shell_pass.patch_owned_shell_layout = _release_layout_patch
ownership_runtime_pass.harden_owned_runtime = _release_runtime_hardening

# Import only after monkey-patching: build.py imports these functions by value.
import build


if __name__ == '__main__':
    build.main()
