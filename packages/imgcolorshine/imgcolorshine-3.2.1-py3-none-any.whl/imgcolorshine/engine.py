#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["coloraide", "numpy", "numba", "loguru"]
# ///
# this_file: src/imgcolorshine/engine.py

"""
Core color transformation engine for imgcolorshine.

This module contains the primary logic for the percentile-based color
transformation model. It handles color parsing, attractor management,
and the main two-pass image processing algorithm.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numba
import numpy as np
from coloraide import Color
from loguru import logger

from imgcolorshine import trans_numba


@dataclass
class Attractor:
    """
    Represents a single color attractor.

    Attributes:
        color: The target color object in OKLCH space.
        tolerance: The percentage of pixels (0-100) to be influenced.
        strength: The maximum transformation intensity (0-100).
        oklch_values: A cached tuple of the attractor's (L, C, H) values.
        oklab_values: A cached tuple of the attractor's (L, a, b) values.
    """

    color: Color
    tolerance: float
    strength: float
    oklch_values: tuple[float, float, float] = field(init=False)
    oklab_values: tuple[float, float, float] = field(init=False)

    def __post_init__(self) -> None:
        """Cache commonly used color conversions for performance."""
        self.oklch_values = (self.color["lightness"], self.color["chroma"], self.color["hue"])
        oklab_color = self.color.convert("oklab")
        self.oklab_values = (oklab_color["lightness"], oklab_color["a"], oklab_color["b"])


class OKLCHEngine:
    """
    Handles color space operations, color parsing, and batch conversions.
    """

    def __init__(self) -> None:
        """Initializes the engine with a cache for parsed colors."""
        self.cache: dict[str, Color] = {}
        logger.debug("Initialized OKLCH color engine.")

    def parse_color(self, color_str: str) -> Color:
        """Parses a CSS color string into a ColorAide object, with caching."""
        if color_str in self.cache:
            return self.cache[color_str].clone()
        try:
            color = Color(color_str)
            self.cache[color_str] = color.clone()
            return color
        except Exception as e:
            msg = f"Invalid color specification: {color_str}"
            raise ValueError(msg) from e

    def create_attractor(self, color_str: str, tolerance: float, strength: float) -> Attractor:
        """Creates an Attractor object from a color string and parameters."""
        color = self.parse_color(color_str).convert("oklch")
        return Attractor(color=color, tolerance=tolerance, strength=strength)

    def batch_rgb_to_oklab(self, rgb_image: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
        """Converts an entire sRGB image to Oklab using Numba."""
        return trans_numba.batch_srgb_to_oklab(rgb_image.astype(np.float32))

    def batch_oklab_to_rgb(self, oklab_image: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
        """Converts an entire Oklab image to sRGB with gamut mapping using Numba."""
        oklch_image = trans_numba.batch_oklab_to_oklch(oklab_image.astype(np.float32))
        oklch_mapped = trans_numba.batch_gamut_map_oklch(oklch_image)
        oklab_mapped = trans_numba.batch_oklch_to_oklab(oklch_mapped)
        return trans_numba.batch_oklab_to_srgb(oklab_mapped)


# # @numba.njit
def blend_pixel_colors(
    pixel_lab,
    pixel_lch,
    attractors_lab,
    attractors_lch,
    weights,
    flags,
):
    """Blend a single pixel's color based on attractor weights."""
    total_weight = np.sum(weights)
    if total_weight == 0:
        return pixel_lab

    src_weight = 1.0 - total_weight if total_weight < 1.0 else 0.0
    final_l, final_c, final_h = pixel_lch[0], pixel_lch[1], pixel_lch[2]

    if flags[0]:  # Luminance
        weighted_l = np.sum(weights * attractors_lch[:, 0])
        final_l = src_weight * pixel_lch[0] + weighted_l
    if flags[1]:  # Saturation
        weighted_c = np.sum(weights * attractors_lch[:, 1])
        final_c = src_weight * pixel_lch[1] + weighted_c
    if flags[2]:  # Hue
        sin_sum = src_weight * np.sin(np.deg2rad(pixel_lch[2])) + np.sum(
            weights * np.sin(np.deg2rad(attractors_lch[:, 2]))
        )
        cos_sum = src_weight * np.cos(np.deg2rad(pixel_lch[2])) + np.sum(
            weights * np.cos(np.deg2rad(attractors_lch[:, 2]))
        )
        final_h = np.rad2deg(np.arctan2(sin_sum, cos_sum))

    final_h = final_h + 360 if final_h < 0 else final_h
    h_rad = np.deg2rad(final_h)
    return np.array([final_l, final_c * np.cos(h_rad), final_c * np.sin(h_rad)], dtype=pixel_lab.dtype)


# @numba.njit
def _calculate_weights_percentile(
    pixel_lab,
    attractors_lab,
    delta_e_maxs,
    strengths,
):
    """Calculate weights based on pre-calculated percentile distance thresholds."""
    weights = np.zeros(len(attractors_lab), dtype=np.float32)
    for i in range(len(attractors_lab)):
        delta_e = np.sqrt(np.sum((pixel_lab - attractors_lab[i]) ** 2))
        delta_e_max = delta_e_maxs[i]
        if delta_e < delta_e_max and delta_e_max > 0:
            d_norm = delta_e / delta_e_max
            falloff = 0.5 * (np.cos(d_norm * np.pi) + 1.0)  # 1 → 0 as d_norm 0→1

            if strengths[i] <= 100.0:
                # Traditional regime: scale fall-off by 0-1 strength factor
                weights[i] = (strengths[i] / 100.0) * falloff
            else:
                # Extended regime 100-200: progressively override fall-off
                s_extra = (strengths[i] - 100.0) / 100.0  # 0-1
                # Blend between falloff (at s_extra=0) and full influence (1.0)
                weights[i] = falloff + s_extra * (1.0 - falloff)
    return weights


# @numba.njit(parallel=True)
def _transform_pixels_percentile(
    pixels_lab,
    pixels_lch,
    attractors_lab,
    attractors_lch,
    delta_e_maxs,
    strengths,
    flags,
):
    """Transform pixels using the percentile-based tolerance model."""
    h, w = pixels_lab.shape[:2]
    result = np.empty_like(pixels_lab)
    for y in numba.prange(h):
        for x in range(w):
            weights = _calculate_weights_percentile(pixels_lab[y, x], attractors_lab, delta_e_maxs, strengths)
            result[y, x] = blend_pixel_colors(
                pixels_lab[y, x], pixels_lch[y, x], attractors_lab, attractors_lch, weights, flags
            )
    return result


class ColorTransformer:
    """High-level color transformation interface."""

    def __init__(self, engine: OKLCHEngine):
        self.engine = engine
        logger.debug("Initialized ColorTransformer")

    def transform_image(
        self,
        image: np.ndarray[Any, Any],
        attractors: list[Attractor],
        flags: dict[str, bool],
        progress_callback: Callable[[float], None] | None = None,
    ) -> np.ndarray[Any, Any]:
        """Transforms an image using the percentile-based color attractor model."""
        h, w = image.shape[:2]
        logger.info(f"Transforming {w}×{h} image with {len(attractors)} attractors")

        if not attractors:
            logger.warning("No attractors provided, returning original image.")
            return image.copy()

        flags_array = np.array([flags.get("luminance", True), flags.get("saturation", True), flags.get("hue", True)])
        attractors_lab = np.array([a.oklab_values for a in attractors])
        attractors_lch = np.array([a.oklch_values for a in attractors])
        tolerances = np.array([a.tolerance for a in attractors])
        strengths = np.array([a.strength for a in attractors])

        logger.info("Analyzing image color distribution...")
        image_lab = self.engine.batch_rgb_to_oklab(image)

        delta_e_maxs = np.zeros_like(tolerances, dtype=np.float32)
        for i in range(len(attractors)):
            distances = np.sqrt(np.sum((image_lab - attractors_lab[i]) ** 2, axis=-1))
            if tolerances[i] <= 0:
                delta_e_maxs[i] = 0.0
            elif tolerances[i] >= 100:
                delta_e_maxs[i] = np.max(distances) + 1e-6
            else:
                delta_e_maxs[i] = np.percentile(distances, tolerances[i])

        logger.debug(f"Calculated distance thresholds (ΔE max): {delta_e_maxs}")

        logger.info("Applying color transformation...")
        image_lch = trans_numba.batch_oklab_to_oklch(image_lab.astype(np.float32))
        transformed_lab = _transform_pixels_percentile(
            image_lab, image_lch, attractors_lab, attractors_lch, delta_e_maxs, strengths, flags_array
        )

        result = self.engine.batch_oklab_to_rgb(transformed_lab)
        if progress_callback:
            progress_callback(1.0)

        logger.info("Transformation complete.")
        return np.clip(result, 0, 1)
