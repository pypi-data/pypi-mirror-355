#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["numpy", "numba"]
# ///
# this_file: src/imgcolorshine/falloff.py

"""
Falloff functions for color attraction.

Provides various mathematical curves for controlling how color attraction
strength decreases with distance. The raised cosine is the default and
recommended function for smooth, natural transitions.
"""

from collections.abc import Callable
from enum import Enum

import numba
import numpy as np


class FalloffType(Enum):
    """Available falloff curve types.

    Different mathematical functions for controlling attraction falloff.
    Used for customizing the behavior of color transformations.

    Used in:
    - old/imgcolorshine/test_imgcolorshine.py
    - src/imgcolorshine/__init__.py
    """

    COSINE = "cosine"  # Smooth raised cosine (default)
    LINEAR = "linear"  # Simple linear falloff
    QUADRATIC = "quadratic"  # Quadratic ease-out
    GAUSSIAN = "gaussian"  # Gaussian bell curve
    CUBIC = "cubic"  # Cubic ease-out


@numba.njit
def falloff_cosine(d_norm: float) -> float:
    """
    Raised cosine falloff (smooth and natural).

    This is the default and recommended falloff function,
    providing smooth transitions without harsh edges.

    """
    return 0.5 * (np.cos(d_norm * np.pi) + 1.0)


@numba.njit
def falloff_linear(d_norm: float) -> float:
    """Simple linear falloff."""
    return 1.0 - d_norm


@numba.njit
def falloff_quadratic(d_norm: float) -> float:
    """Quadratic ease-out falloff."""
    return 1.0 - d_norm * d_norm


@numba.njit
def falloff_gaussian(d_norm: float) -> float:
    """
    Gaussian falloff with sigma=0.4.

    Provides a bell curve with most influence near the center.

    """
    sigma = 0.4
    return np.exp(-(d_norm * d_norm) / (2 * sigma * sigma))


@numba.njit
def falloff_cubic(d_norm: float) -> float:
    """Cubic ease-out falloff."""
    inv = 1.0 - d_norm
    return inv * inv * inv


@numba.njit
def calculate_falloff(d_norm: float, falloff_type: int = 0) -> float:
    """
    Calculate falloff value based on normalized distance.

    Args:
        d_norm: Normalized distance (0 to 1)
        falloff_type: Type of falloff curve (0=cosine, 1=linear, etc.)

    Returns:
        Falloff value (0 to 1)

    """
    if falloff_type == 0:  # COSINE
        return falloff_cosine(d_norm)
    if falloff_type == 1:  # LINEAR
        return falloff_linear(d_norm)
    if falloff_type == 2:  # QUADRATIC
        return falloff_quadratic(d_norm)
    if falloff_type == 3:  # GAUSSIAN
        return falloff_gaussian(d_norm)
    if falloff_type == 4:  # CUBIC
        return falloff_cubic(d_norm)
    # Default to cosine
    return falloff_cosine(d_norm)


def get_falloff_function(falloff_type: FalloffType) -> Callable[[float], float]:
    """
    Get the appropriate falloff function.

    Args:
        falloff_type: Type of falloff curve

    Returns:
        Falloff function

    Used in:
    - src/imgcolorshine/__init__.py
    """
    mapping = {
        FalloffType.COSINE: falloff_cosine,
        FalloffType.LINEAR: falloff_linear,
        FalloffType.QUADRATIC: falloff_quadratic,
        FalloffType.GAUSSIAN: falloff_gaussian,
        FalloffType.CUBIC: falloff_cubic,
    }

    return mapping.get(falloff_type, falloff_cosine)


def visualize_falloff(falloff_type: FalloffType, samples: int = 100) -> np.ndarray:
    """
    Generate data for visualizing a falloff curve.

    Args:
        falloff_type: Type of falloff curve
        samples: Number of samples to generate

    Returns:
        Array of shape (samples, 2) with [distance, falloff] pairs

    Used for testing and visualization purposes.

    Used in:
    - old/imgcolorshine/test_imgcolorshine.py
    """
    distances = np.linspace(0, 1, samples)
    falloff_func = get_falloff_function(falloff_type)

    values = np.array([falloff_func(d) for d in distances])

    return np.column_stack([distances, values])


def precompute_falloff_lut(
    falloff_type: FalloffType = FalloffType.COSINE, resolution: int = 1024
) -> np.ndarray:
    """
    Precompute a lookup table for fast falloff calculations.

    Args:
        falloff_type: Type of falloff curve
        resolution: Number of entries in the lookup table

    Returns:
        Lookup table array

    """
    lut = np.zeros(resolution, dtype=np.float32)
    falloff_func = get_falloff_function(falloff_type)

    for i in range(resolution):
        d_norm = i / (resolution - 1)
        lut[i] = falloff_func(d_norm)

    return lut


@numba.njit
def apply_falloff_lut(d_norm: float, lut: np.ndarray) -> float:
    """
    Apply falloff using a precomputed lookup table.

    Args:
        d_norm: Normalized distance (0 to 1)
        lut: Precomputed lookup table

    Returns:
        Interpolated falloff value

    """
    # Get LUT index
    idx_float = d_norm * (len(lut) - 1)
    idx = int(idx_float)

    # Handle edge cases
    if idx >= len(lut) - 1:
        return lut[-1]
    if idx < 0:
        return lut[0]

    # Linear interpolation between LUT entries
    frac = idx_float - idx
    return lut[idx] * (1 - frac) + lut[idx + 1] * frac
