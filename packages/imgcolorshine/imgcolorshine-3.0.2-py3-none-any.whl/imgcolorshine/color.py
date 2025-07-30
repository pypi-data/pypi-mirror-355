#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["coloraide", "numpy", "loguru"]
# ///
# this_file: src/imgcolorshine/color.py

"""
OKLCH color space operations and attractor management.

Handles color parsing, OKLCH/Oklab conversions, delta E calculations,
and gamut mapping. This module is the core of the color transformation
system, providing perceptually uniform color operations.

"""

from dataclasses import dataclass, field

import numpy as np
from coloraide import Color
from loguru import logger

# Import Numba-optimized color transforms
from imgcolorshine import trans_numba


@dataclass
class Attractor:
    """Represents a color attractor with its parameters.

    Stores color information in both OKLCH and Oklab formats for
    efficient processing. Used by transform.py for applying color
    attractions to images.

    Used in:
    - old/imgcolorshine/imgcolorshine/__init__.py
    - old/imgcolorshine/imgcolorshine/transform.py
    - src/imgcolorshine/__init__.py
    - src/imgcolorshine/transform.py
    """

    color: Color  # In OKLCH space
    tolerance: float  # 0-100
    strength: float  # 0-100
    oklch_values: tuple[float, float, float] = field(init=False)  # L, C, H
    oklab_values: tuple[float, float, float] = field(init=False)  # L, a, b

    def __post_init__(self):
        """Cache commonly used conversions for performance."""
        self.oklch_values = (
            self.color["lightness"],
            self.color["chroma"],
            self.color["hue"],
        )

        # Convert to Oklab for distance calculations
        oklab_color = self.color.convert("oklab")
        self.oklab_values = (
            oklab_color["lightness"],
            oklab_color["a"],
            oklab_color["b"],
        )


class OKLCHEngine:
    """Handles OKLCH color space operations and conversions.

    Central engine for all color operations, providing OKLCH/Oklab
    conversions, color parsing, and gamut mapping. Used throughout
    the application for perceptually uniform color transformations.

    Used in:
    - old/imgcolorshine/imgcolorshine/__init__.py
    - old/imgcolorshine/imgcolorshine/transform.py
    - old/imgcolorshine/imgcolorshine_main.py
    - old/imgcolorshine/test_imgcolorshine.py
    - src/imgcolorshine/__init__.py
    - src/imgcolorshine/colorshine.py
    - src/imgcolorshine/transform.py
    """

    def __init__(self):
        """Initialize the color engine with caching."""
        self.cache: dict[str, Color] = {}
        logger.debug("Initialized OKLCH color engine")

    def parse_color(self, color_str: str) -> Color:
        """
        Parse any CSS color format and return a Color object.

        Supports: hex, rgb(), hsl(), oklch(), named colors, etc.
        Results are cached for performance.

        Used in:
        - old/imgcolorshine/test_imgcolorshine.py
        """
        if color_str in self.cache:
            return self.cache[color_str].clone()

        try:
            color = Color(color_str)
            self.cache[color_str] = color.clone()
            logger.debug(
                "Parsed color '%s' → %s",
                color_str,
                color,
            )
            return color
        except Exception as e:
            logger.error(f"Failed to parse color '{color_str}': {e}")
            msg = f"Invalid color specification: {color_str}"
            raise ValueError(msg) from e

    def create_attractor(
        self, color_str: str, tolerance: float, strength: float
    ) -> Attractor:
        """Create an attractor from color string and parameters.

        Parses the color string and converts to OKLCH space for
        perceptually uniform operations.

        Used in:
        - old/imgcolorshine/imgcolorshine_main.py
        - old/imgcolorshine/test_imgcolorshine.py
        - src/imgcolorshine/colorshine.py
        """
        color = self.parse_color(color_str)
        oklch_color = color.convert("oklch")

        return Attractor(color=oklch_color, tolerance=tolerance, strength=strength)

    def calculate_delta_e(self, color1: np.ndarray, color2: np.ndarray) -> float:
        """
        Calculate perceptual distance in Oklab space.

        Args:
            color1: [L, a, b] values
            color2: [L, a, b] values

        Returns:
            Euclidean distance in Oklab space

        """
        return np.sqrt(np.sum((color1 - color2) ** 2))

    def oklch_to_oklab(
        self, l: float, c: float, h: float
    ) -> tuple[float, float, float]:  # noqa: E741
        """Convert OKLCH to Oklab coordinates."""
        h_rad = np.deg2rad(h)
        a = c * np.cos(h_rad)
        b = c * np.sin(h_rad)
        return l, a, b

    def oklab_to_oklch(
        self, l: float, a: float, b: float
    ) -> tuple[float, float, float]:  # noqa: E741
        """Convert Oklab to OKLCH coordinates.

        Used by transform.py for color space conversions.

        Used in:
        - old/imgcolorshine/imgcolorshine/transform.py
        - src/imgcolorshine/transform.py
        """
        c = np.sqrt(a**2 + b**2)
        h = np.rad2deg(np.arctan2(b, a))
        if h < 0:
            h += 360
        return l, c, h

    def rgb_to_oklab(self, rgb: np.ndarray) -> np.ndarray:
        """
        Convert sRGB to Oklab.

        Args:
            rgb: Array of shape (..., 3) with values in [0, 1]

        Returns:
            Array of shape (..., 3) with Oklab values

        """
        # First convert to linear RGB
        self.srgb_to_linear(rgb)

        # Convert to Oklab using ColorAide's matrices
        # This is a simplified version - in production, use ColorAide's convert
        color = Color("srgb", list(rgb))
        oklab = color.convert("oklab")
        return np.array([oklab["lightness"], oklab["a"], oklab["b"]])

    def oklab_to_rgb(self, oklab: np.ndarray) -> np.ndarray:
        """
        Convert Oklab to sRGB.

        Args:
            oklab: Array of shape (..., 3) with Oklab values

        Returns:
            Array of shape (..., 3) with sRGB values in [0, 1]

        """
        # Use ColorAide for accurate conversion
        color = Color("oklab", list(oklab))
        srgb = color.convert("srgb")
        return np.array([srgb["red"], srgb["green"], srgb["blue"]])

    def srgb_to_linear(self, srgb: np.ndarray) -> np.ndarray:
        """Apply inverse gamma correction."""
        return np.where(
            srgb <= 0.04045, srgb / 12.92, np.power((srgb + 0.055) / 1.055, 2.4)
        )

    def linear_to_srgb(self, linear: np.ndarray) -> np.ndarray:
        """Apply gamma correction."""
        return np.where(
            linear <= 0.0031308,
            linear * 12.92,
            1.055 * np.power(linear, 1 / 2.4) - 0.055,
        )

    def gamut_map_oklch(
        self, l: float, c: float, h: float
    ) -> tuple[float, float, float]:  # noqa: E741
        """
        CSS Color Module 4 compliant gamut mapping.

        Reduces chroma while preserving lightness and chroma until the color
        is within sRGB gamut. Uses binary search for efficiency.

        """
        color = Color("oklch", [l, c, h])

        if color.in_gamut("srgb"):
            return l, c, h

        # Binary search for maximum valid chroma
        c_min, c_max = 0.0, c
        epsilon = 0.0001

        while c_max - c_min > epsilon:
            c_mid = (c_min + c_max) / 2
            test_color = Color("oklch", [l, c_mid, h])

            if test_color.in_gamut("srgb"):
                c_min = c_mid
            else:
                c_max = c_mid

        logger.debug("Gamut mapped: C=%.3f → %.3f", c, c_min)
        return l, c_min, h

    def batch_rgb_to_oklab(self, rgb_image: np.ndarray) -> np.ndarray:
        """
        Convert entire RGB image to Oklab.

        Args:
            rgb_image: Array of shape (H, W, 3) with values in [0, 1]

        Returns:
            Array of shape (H, W, 3) with Oklab values

        Used by transform.py for batch image processing.

        Used in:
        - old/imgcolorshine/imgcolorshine/transform.py
        - src/imgcolorshine/transform.py
        """
        # Use Numba-optimized batch conversion
        logger.debug("Using Numba-optimized RGB to Oklab conversion")
        return trans_numba.batch_srgb_to_oklab(rgb_image.astype(np.float32))

    def batch_oklab_to_rgb(self, oklab_image: np.ndarray) -> np.ndarray:
        """
        Convert entire Oklab image to RGB.

        Args:
            oklab_image: Array of shape (H, W, 3) with Oklab values

        Returns:
            Array of shape (H, W, 3) with sRGB values in [0, 1]

        Used by transform.py for batch image processing.

        Used in:
        - old/imgcolorshine/imgcolorshine/transform.py
        - src/imgcolorshine/transform.py
        """
        # Use Numba-optimized batch conversion with gamut mapping
        logger.debug("Using Numba-optimized Oklab to RGB conversion")

        # First convert to OKLCH for gamut mapping
        oklch_image = trans_numba.batch_oklab_to_oklch(oklab_image.astype(np.float32))

        # Apply gamut mapping
        oklch_mapped = trans_numba.batch_gamut_map_oklch(oklch_image)

        # Convert back to Oklab then to sRGB
        oklab_mapped = trans_numba.batch_oklch_to_oklab(oklch_mapped)
        return trans_numba.batch_oklab_to_srgb(oklab_mapped)
