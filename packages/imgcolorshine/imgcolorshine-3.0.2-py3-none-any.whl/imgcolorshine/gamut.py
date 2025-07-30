#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["numpy", "coloraide", "loguru"]
# ///
# this_file: src/imgcolorshine/gamut.py

"""
CSS Color Module 4 compliant gamut mapping.

Implements the standard algorithm for mapping out-of-gamut colors back
to the displayable range while preserving perceptual attributes. Uses
binary search to find the maximum chroma that fits within gamut.

"""

from typing import TypedDict

import numba
import numpy as np
from coloraide import Color
from loguru import logger

# Import Numba-optimized functions from trans_numba
from imgcolorshine.trans_numba import (
    is_in_gamut_srgb,
    oklab_to_srgb_single,
    oklch_to_oklab_single,
)


@numba.njit(cache=True)
def binary_search_chroma(
    l: float, c: float, h: float, epsilon: float = 0.0001
) -> float:
    """
    Numba-optimized binary search for maximum in-gamut chroma.

    Finds the maximum chroma value that keeps the color within sRGB gamut
    using binary search. This is the core of the CSS Color Module 4 gamut
    mapping algorithm.

    Args:
        l: Lightness (0-1)
        c: Initial chroma value
        h: Hue in degrees (0-360)
        epsilon: Convergence threshold

    Returns:
        Maximum chroma that fits within gamut
    """
    if l == 0.0 or l == 1.0:  # For pure black or white, max chroma is 0
        return 0.0

    # Quick check if already in gamut
    oklch = np.array([l, c, h], dtype=np.float32)
    oklab = oklch_to_oklab_single(oklch)
    rgb = oklab_to_srgb_single(oklab)

    if is_in_gamut_srgb(rgb):
        return c

    # Binary search for maximum valid chroma
    c_min, c_max = 0.0, c

    for _ in range(20):  # Max iterations
        if c_max - c_min <= epsilon:
            break

        c_mid = (c_min + c_max) / 2.0
        test_oklch = np.array([l, c_mid, h], dtype=np.float32)
        test_oklab = oklch_to_oklab_single(test_oklch)
        test_rgb = oklab_to_srgb_single(test_oklab)

        if is_in_gamut_srgb(test_rgb):
            c_min = c_mid
        else:
            c_max = c_mid

    return c_min


@numba.njit(parallel=True, cache=True)
def batch_map_oklch_numba(
    colors_flat: np.ndarray, epsilon: float = 0.0001
) -> np.ndarray:
    """
    Numba-optimized batch gamut mapping for OKLCH colors.

    Processes multiple colors in parallel for maximum performance.

    Args:
        colors_flat: Flattened array of OKLCH colors (N, 3)
        epsilon: Convergence threshold for binary search

    Returns:
        Gamut-mapped OKLCH colors (N, 3)
    """
    n_colors = colors_flat.shape[0]
    mapped_colors = np.empty_like(colors_flat)

    for i in numba.prange(n_colors):
        l, c, h = colors_flat[i]
        c_mapped = binary_search_chroma(l, c, h, epsilon)
        mapped_colors[i] = np.array([l, c_mapped, h], dtype=colors_flat.dtype)

    return mapped_colors


class GamutMapper:
    """Handles gamut mapping for out-of-bounds colors.

    Ensures all colors are displayable in the target color space (sRGB)
    by reducing chroma while preserving lightness and chroma. Follows the
    CSS Color Module 4 specification for consistent results.

    Used in:
    - old/imgcolorshine/test_imgcolorshine.py
    - src/imgcolorshine/__init__.py
    """

    def __init__(self, target_space: str = "srgb"):
        """
        Initialize the gamut mapper.

        Args:
            target_space: Target color space for gamut mapping

        """
        self.target_space = target_space
        self.epsilon = 0.0001
        logger.debug(f"Initialized GamutMapper for {target_space}")

    def is_in_gamut(self, color: Color) -> bool:
        """Check if a color is within the target gamut."""
        return color.in_gamut(self.target_space)

    def map_oklch_to_gamut(
        self, l: float, c: float, h: float
    ) -> tuple[float, float, float]:
        """
        CSS Color Module 4 gamut mapping algorithm with Numba optimization.

        Reduces chroma while preserving lightness and hue until
        the color fits within the target gamut. Uses Numba-optimized
        binary search for better performance when available.

        Args:
            l: Lightness (0-1)
            c: Chroma (0-0.4+)
            h: Hue (0-360)

        Returns:
            Gamut-mapped OKLCH values

        Used in:
        - old/imgcolorshine/test_imgcolorshine.py
        """
        # Use Numba-optimized version for sRGB gamut mapping
        if self.target_space == "srgb":
            final_c = binary_search_chroma(l, c, h, self.epsilon)
            logger.debug(f"Gamut mapped (Numba): C={c:.4f} → {final_c:.4f}")
            return l, final_c, h

        # Fall back to ColorAide for other color spaces
        # Create color object
        color = Color("oklch", [l, c, h])

        # Check if already in gamut
        if self.is_in_gamut(color):
            return l, c, h

        # Binary search for maximum valid chroma
        c_min = 0.0
        c_max = c

        iterations = 0
        max_iterations = 20

        while c_max - c_min > self.epsilon and iterations < max_iterations:
            c_mid = (c_min + c_max) / 2
            test_color = Color("oklch", [l, c_mid, h])

            if self.is_in_gamut(test_color):
                c_min = c_mid
            else:
                c_max = c_mid

            iterations += 1

        # Use the last valid chroma value
        final_c = c_min

        logger.debug(
            f"Gamut mapped: C={c:.4f} → {final_c:.4f} (iterations: {iterations})"
        )

        return l, final_c, h

    def map_oklab_to_gamut(
        self, l: float, a: float, b: float
    ) -> tuple[float, float, float]:
        """
        Map Oklab color to gamut by converting to OKLCH first.

        Args:
            l: Lightness
            a: Green-red axis
            b: Blue-yellow axis

        Returns:
            Gamut-mapped Oklab values

        """
        # Convert to OKLCH
        c = np.sqrt(a**2 + b**2)
        h = np.rad2deg(np.arctan2(b, a))
        if h < 0:
            h += 360

        # Map to gamut
        l_mapped, c_mapped, h_mapped = self.map_oklch_to_gamut(l, c, h)

        # Convert back to Oklab
        h_rad = np.deg2rad(h_mapped)
        a_mapped = c_mapped * np.cos(h_rad)
        b_mapped = c_mapped * np.sin(h_rad)

        return l_mapped, a_mapped, b_mapped

    def map_rgb_to_gamut(
        self, r: float, g: float, b: float
    ) -> tuple[float, float, float]:
        """
        Simple RGB gamut mapping by clamping.

        For more sophisticated mapping, convert to OKLCH first.

        Args:
            r, g, b: RGB values (may be outside [0, 1])

        Returns:
            Clamped RGB values in [0, 1]

        """
        return (np.clip(r, 0, 1), np.clip(g, 0, 1), np.clip(b, 0, 1))

    def batch_map_oklch(self, colors: np.ndarray) -> np.ndarray:
        """
        Map multiple OKLCH colors to gamut with Numba optimization.

        Uses parallel processing for sRGB gamut mapping, falling back
        to sequential processing for other color spaces.

        Args:
            colors: Array of shape (..., 3) with OKLCH values

        Returns:
            Gamut-mapped colors

        """
        shape = colors.shape
        flat_colors = colors.reshape(-1, 3).astype(np.float32)

        # Use Numba-optimized parallel version for sRGB
        if self.target_space == "srgb":
            mapped_colors = batch_map_oklch_numba(flat_colors, self.epsilon)
            return mapped_colors.reshape(shape)

        # Fall back to sequential processing for other color spaces
        mapped_colors = np.zeros_like(flat_colors)
        for i, (l, c, h) in enumerate(flat_colors):
            mapped_colors[i] = self.map_oklch_to_gamut(l, c, h)

        return mapped_colors.reshape(shape)

    def analyze_gamut_coverage(self, colors: np.ndarray) -> "GamutStats":
        """
        Analyze how many colors are out of gamut.

        Args:
            colors: Array of colors in any format

        Returns:
            Dictionary with gamut statistics

        """
        total_colors = len(colors)
        out_of_gamut = 0

        for color_values in colors:
            color = Color("oklch", list(color_values))
            if not self.is_in_gamut(color):
                out_of_gamut += 1

        in_gamut = total_colors - out_of_gamut
        percentage_in = (in_gamut / total_colors) * 100 if total_colors > 0 else 100

        return {
            "total": total_colors,
            "in_gamut": in_gamut,
            "out_of_gamut": out_of_gamut,
            "percentage_in_gamut": percentage_in,
        }


class GamutStats(TypedDict):
    total: int
    in_gamut: int
    out_of_gamut: int
    percentage_in_gamut: float


def create_gamut_boundary_lut(
    hue_steps: int = 360, lightness_steps: int = 100
) -> np.ndarray:
    """
    Create a lookup table for maximum chroma at each chroma/lightness.

    This can speed up gamut mapping for real-time applications.

    Args:
        hue_steps: Number of chroma divisions
        lightness_steps: Number of lightness divisions

    Returns:
        2D array of maximum chroma values

    """
    lut = np.zeros((lightness_steps, hue_steps), dtype=np.float32)
    mapper = GamutMapper()

    for l_idx in range(lightness_steps):
        l = l_idx / (lightness_steps - 1)

        if l == 0.0 or l == 1.0:  # Max chroma is 0 for pure black or white
            lut[l_idx, :] = 0.0
            continue

        for h_idx in range(hue_steps):
            h = (h_idx / hue_steps) * 360

            # Binary search for max chroma
            c_min, c_max = 0.0, 0.5  # Max reasonable chroma

            while c_max - c_min > 0.001:
                c_mid = (c_min + c_max) / 2
                color = Color("oklch", [l, c_mid, h])

                if mapper.is_in_gamut(color):
                    c_min = c_mid
                else:
                    c_max = c_mid

            lut[l_idx, h_idx] = c_min

    return lut
