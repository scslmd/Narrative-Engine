#!/usr/bin/env python3
"""Compatibility wrapper for the portable quality-check CLI implementation."""

from __future__ import annotations

from scripts.qc import *  # noqa: F401,F403
from scripts.qc import main


if __name__ == "__main__":
    main()
