#!/usr/bin/env python3
"""Primary RuneSheet transition build entrypoint.

This entrypoint is intentionally launch-safe. Runtime/Dex ownership experiments
must not run here unless they have passed device smoke-tests. The current main
product build therefore delegates to the proven build.py transformation engine.
"""
from __future__ import annotations

import build


if __name__ == '__main__':
    build.main()
