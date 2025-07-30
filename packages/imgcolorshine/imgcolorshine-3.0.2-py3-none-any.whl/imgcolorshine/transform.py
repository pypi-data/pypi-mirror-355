#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["numpy", "numba", "loguru"]
# ///
# this_file: src/imgcolorshine/transform.py

"""
High-performance color transformation algorithms using NumPy and Numba.

Implements the core color transformation logic with JIT compilation for
optimal performance. Handles multi-attractor blending and channel-specific
transformations in the OKLCH color space.

"""

from collections.abc import Callable

import numba
import numpy as np
from loguru import logger

from imgcolorshine import trans_numba
from imgcolorshine.color import Attractor, OKLCHEngine
from imgcolorshine.utils import process_large_image


@numba.njit
def calculate_delta_e_fast(pixel_lab: np.ndarray, attractor_lab: np.ndarray) -> float:
    """
    Fast Euclidean distance calculation in Oklab space.

    Args:
        pixel_lab: [L, a, b] values
        attractor_lab: [L, a, b] values

    Returns:
        Perceptual distance

    """
    return np.sqrt(
        (pixel_lab[0] - attractor_lab[0]) ** 2
        + (pixel_lab[1] - attractor_lab[1]) ** 2
        + (pixel_lab[2] - attractor_lab[2]) ** 2
    )


# Maximum perceptual distance for tolerance=100
# This represents a large but reasonable distance in Oklab space
MAX_DELTA_E = 2.5


@numba.njit
def calculate_weights(
    pixel_lab: np.ndarray,
    attractors_lab: np.ndarray,
    tolerances: np.ndarray,
    strengths: np.ndarray,
) -> np.ndarray:
    """
    Calculate attraction weights for all attractors.

    This function calculates how much each attractor influences a pixel based on:
    - The perceptual distance between the pixel and attractor colors
    - The tolerance setting (radius of influence)
    - The strength setting (maximum transformation amount)

    The tolerance is linearly mapped to perceptual distance, fixing the previous
    quadratic mapping that made the tool unintuitive. With linear mapping:
    - tolerance=100 affects colors up to MAX_DELTA_E distance
    - tolerance=50 affects colors up to MAX_DELTA_E/2 distance
    - etc.

    Returns:
        Array of weights for each attractor

    """
    num_attractors = len(attractors_lab)
    weights = np.zeros(num_attractors)

    for i in range(num_attractors):
        # Calculate perceptual distance
        delta_e = calculate_delta_e_fast(pixel_lab, attractors_lab[i])

        # Map tolerance (0-100) to max distance with LINEAR mapping
        # This is the critical fix - was previously: delta_e_max = 1.0 * (tolerances[i] / 100.0) ** 2
        delta_e_max = MAX_DELTA_E * (tolerances[i] / 100.0)

        # Check if within tolerance
        if delta_e <= delta_e_max:
            # Calculate normalized distance
            d_norm = delta_e / delta_e_max

            # Apply falloff function (raised cosine)
            attraction_factor = 0.5 * (np.cos(d_norm * np.pi) + 1.0)

            # Calculate final weight
            weights[i] = (strengths[i] / 100.0) * attraction_factor

    return weights


@numba.njit
def blend_colors(
    pixel_lab: np.ndarray,
    pixel_lch: np.ndarray,
    attractors_lab: np.ndarray,
    attractors_lch: np.ndarray,
    weights: np.ndarray,
    flags: np.ndarray,
) -> np.ndarray:
    """
    Blend pixel color with attractors based on weights and channel flags.

    Args:
        pixel_lab: Original pixel in Oklab [L, a, b]
        pixel_lch: Original pixel in OKLCH [L, C, H]
        attractors_lab: Attractor colors in Oklab
        attractors_lch: Attractor colors in OKLCH
        weights: Weight for each attractor
        flags: Boolean array [luminance, saturation, chroma]

    Returns:
        Blended color in Oklab space

    """
    total_weight = np.sum(weights)

    if total_weight == 0:
        return pixel_lab

    # Determine source weight
    if total_weight > 1.0:
        # Normalize weights
        weights = weights / total_weight
        src_weight = 0.0
    else:
        src_weight = 1.0 - total_weight

    # Start with original values
    final_l = pixel_lch[0]
    final_c = pixel_lch[1]
    final_h = pixel_lch[2]

    # Blend each enabled channel
    if flags[0]:  # Luminance
        final_l = src_weight * pixel_lch[0]
        for i in range(len(weights)):
            if weights[i] > 0:
                final_l += weights[i] * attractors_lch[i][0]

    if flags[1]:  # Saturation (Chroma)
        final_c = src_weight * pixel_lch[1]
        for i in range(len(weights)):
            if weights[i] > 0:
                final_c += weights[i] * attractors_lch[i][1]

    if flags[2]:  # Hue
        # Use circular mean for chroma
        sin_sum = src_weight * np.sin(np.deg2rad(pixel_lch[2]))
        cos_sum = src_weight * np.cos(np.deg2rad(pixel_lch[2]))

        for i in range(len(weights)):
            if weights[i] > 0:
                h_rad = np.deg2rad(attractors_lch[i][2])
                sin_sum += weights[i] * np.sin(h_rad)
                cos_sum += weights[i] * np.cos(h_rad)

        final_h = np.rad2deg(np.arctan2(sin_sum, cos_sum))
        if final_h < 0:
            final_h += 360

    # Convert back to Oklab
    h_rad = np.deg2rad(final_h)
    final_a = final_c * np.cos(h_rad)
    final_b = final_c * np.sin(h_rad)

    return np.array([final_l, final_a, final_b], dtype=pixel_lab.dtype)


@numba.njit(parallel=True)
def transform_pixels(
    pixels_lab: np.ndarray,
    pixels_lch: np.ndarray,
    attractors_lab: np.ndarray,
    attractors_lch: np.ndarray,
    tolerances: np.ndarray,
    strengths: np.ndarray,
    flags: np.ndarray,
) -> np.ndarray:
    """
    Transform all pixels using Numba parallel processing.

    Args:
        pixels_lab: Image in Oklab space (H, W, 3)
        pixels_lch: Image in OKLCH space (H, W, 3)
        attractors_lab: Attractor colors in Oklab
        attractors_lch: Attractor colors in OKLCH
        tolerances: Tolerance values for each attractor
        strengths: Strength values for each attractor
        flags: Boolean array [luminance, saturation, chroma]

    Returns:
        Transformed image in Oklab space

    """
    h, w = pixels_lab.shape[:2]
    result = np.empty_like(pixels_lab)

    for y in numba.prange(h):
        for x in range(w):
            pixel_lab = pixels_lab[y, x]
            pixel_lch = pixels_lch[y, x]

            # Calculate weights for all attractors
            weights = calculate_weights(
                pixel_lab, attractors_lab, tolerances, strengths
            )

            # Blend colors
            result[y, x] = blend_colors(
                pixel_lab, pixel_lch, attractors_lab, attractors_lch, weights, flags
            )

    return result


class ColorTransformer:
    """High-level color transformation interface.

    Manages the transformation pipeline from RGB input to RGB output,
    handling color space conversions, tiling for large images, and
    progress tracking. Used by the main CLI for applying transformations.

    Used in:
    - old/imgcolorshine/imgcolorshine/__init__.py
    - old/imgcolorshine/imgcolorshine_main.py
    - old/imgcolorshine/test_imgcolorshine.py
    - src/imgcolorshine/__init__.py
    - src/imgcolorshine/colorshine.py
    """

    def __init__(self, engine: OKLCHEngine):
        """
        Initialize the color transformer.

        Args:
            engine: OKLCH color engine instance

        """
        self.engine = engine
        logger.debug("Initialized ColorTransformer")

    def transform_image(
        self,
        image: np.ndarray,
        attractors: list[Attractor],
        flags: dict[str, bool],
        progress_callback: Callable[[float], None] | None = None,
    ) -> np.ndarray:
        """
        Transform an entire image using color attractors.

        Args:
            image: Input image (H, W, 3) in sRGB [0, 1]
            attractors: List of color attractors
            flags: Channel flags {'luminance': bool, 'saturation': bool, 'chroma': bool}
            progress_callback: Optional callback for progress updates

        Returns:
            Transformed image in sRGB [0, 1]

        Used in:
        - old/imgcolorshine/imgcolorshine_main.py
        - old/imgcolorshine/test_imgcolorshine.py
        - src/imgcolorshine/colorshine.py
        """
        # Report dimensions in width×height order to match common conventions
        h, w = image.shape[:2]
        logger.info(f"Transforming {w}×{h} image with {len(attractors)} attractors")

        # Log attractor details
        for i, attractor in enumerate(attractors):
            logger.debug(
                f"  Attractor {i + 1}: color=OKLCH({attractor.oklch_values[0]:.2f}, "
                f"{attractor.oklch_values[1]:.3f}, {attractor.oklch_values[2]:.1f}°), "
                f"tolerance={attractor.tolerance}, strength={attractor.strength}"
            )

        # Convert flags to numpy array
        flags_array = np.array(
            [
                flags.get("luminance", True),
                flags.get("saturation", True),
                flags.get("chroma", True),
            ]
        )

        # Log enabled channels
        enabled_channels = []
        if flags.get("luminance", True):
            enabled_channels.append("luminance")
        if flags.get("saturation", True):
            enabled_channels.append("saturation")
        if flags.get("chroma", True):
            enabled_channels.append("chroma")
        logger.debug(f"Enabled channels: {', '.join(enabled_channels)}")

        # Prepare attractor data for Numba
        attractors_lab = np.array([a.oklab_values for a in attractors])
        attractors_lch = np.array([a.oklch_values for a in attractors])
        tolerances = np.array([a.tolerance for a in attractors])
        strengths = np.array([a.strength for a in attractors])

        # Check if we should use tiling
        from imgcolorshine.io import ImageProcessor

        processor = ImageProcessor()

        if processor.should_use_tiling(w, h):
            # Process in tiles for large images
            def transform_tile(tile):
                return self._transform_tile(
                    tile,
                    attractors_lab,
                    attractors_lch,
                    tolerances,
                    strengths,
                    flags_array,
                )

            result = process_large_image(
                image,
                transform_tile,
                tile_size=processor.tile_size,
                progress_callback=progress_callback,
            )
        else:
            # Process entire image at once
            result = self._transform_tile(
                image,
                attractors_lab,
                attractors_lch,
                tolerances,
                strengths,
                flags_array,
            )

            if progress_callback:
                progress_callback(1.0)

        logger.info("Transformation complete")
        return result

    def _transform_tile(
        self,
        tile: np.ndarray,
        attractors_lab: np.ndarray,
        attractors_lch: np.ndarray,
        tolerances: np.ndarray,
        strengths: np.ndarray,
        flags: np.ndarray,
    ) -> np.ndarray:
        """Transform a single tile of the image."""
        # Convert to Oklab
        tile_lab = self.engine.batch_rgb_to_oklab(tile)

        # Also need OKLCH for channel-specific operations
        # Use Numba-optimized batch conversion
        tile_lch = trans_numba.batch_oklab_to_oklch(tile_lab.astype(np.float32))

        # Apply transformation
        transformed_lab = transform_pixels(
            tile_lab,
            tile_lch,
            attractors_lab,
            attractors_lch,
            tolerances,
            strengths,
            flags,
        )

        # Convert back to RGB
        result = self.engine.batch_oklab_to_rgb(transformed_lab)

        # Ensure values are in valid range
        return np.clip(result, 0, 1)
