"""Deterministic random helpers."""

from __future__ import annotations

import random


def create_rng(seed: int) -> random.Random:
    """Create a local deterministic random generator."""

    return random.Random(seed)
