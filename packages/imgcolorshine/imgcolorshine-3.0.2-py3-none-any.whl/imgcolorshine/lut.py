#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["numpy", "numba", "loguru"]
# ///
# this_file: src/imgcolorshine/lut.py

"""
3D Color Look-Up Table (LUT) implementation for fast color transformations.

Provides dramatic speedup by pre-computing color transformations on a 3D grid
and using trilinear interpolation for arbitrary colors.
"""

import hashlib
import pickle
from pathlib import Path

import numba
import numpy as np
from loguru import logger


class ColorLUT:
    """
    3D Color Look-Up Table for accelerated transformations.

    Pre-computes transformations on a 3D grid in RGB space and uses
    trilinear interpolation for fast lookups. Includes disk caching
    to avoid recomputation.
    """

    def __init__(self, size=65, cache_dir=None):
        """
        Initialize the Color LUT.

        Args:
            size: Resolution of the 3D LUT (size x size x size)
            cache_dir: Directory for caching LUTs (default: ~/.cache/imgcolorshine)
        """
        self.size = size
        self.cache_dir = (
            Path(cache_dir) if cache_dir else Path.home() / ".cache" / "imgcolorshine"
        )
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Pre-allocate LUT array
        self.lut = None

        logger.debug(f"ColorLUT initialized with size {size}³ = {size**3} entries")

    def _get_cache_key(self, attractors_lab, tolerances, strengths, channels):
        """Generate a unique cache key for the transformation parameters."""
        # Create a hashable representation
        data = {
            "attractors": attractors_lab.tobytes(),
            "tolerances": tolerances.tobytes(),
            "strengths": strengths.tobytes(),
            "channels": channels,
            "size": self.size,
        }

        # Generate hash
        hasher = hashlib.sha256()
        for key, value in sorted(data.items()):
            hasher.update(str(key).encode())
            if isinstance(value, bytes):
                hasher.update(value)
            else:
                hasher.update(str(value).encode())

        return hasher.hexdigest()[:16]

    def _get_cache_path(self, cache_key):
        """Get the cache file path for a given key."""
        return self.cache_dir / f"lut_{cache_key}_{self.size}.pkl"

    def load_from_cache(self, cache_key):
        """Try to load LUT from cache."""
        cache_path = self._get_cache_path(cache_key)

        if cache_path.exists():
            try:
                with open(cache_path, "rb") as f:
                    self.lut = pickle.load(f)
                logger.info(f"Loaded LUT from cache: {cache_path.name}")
                return True
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")

        return False

    def save_to_cache(self, cache_key):
        """Save LUT to cache."""
        cache_path = self._get_cache_path(cache_key)

        try:
            with open(cache_path, "wb") as f:
                pickle.dump(self.lut, f)
            logger.debug(f"Saved LUT to cache: {cache_path.name}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def build_lut(
        self, transform_func, attractors_lab, tolerances, strengths, channels
    ):
        """
        Build the 3D LUT by sampling the transformation function.

        Args:
            transform_func: Function that transforms a single RGB pixel
            attractors_lab: Attractor colors in Oklab space
            tolerances: Tolerance values [0, 100]
            strengths: Strength values [0, 100]
            channels: Channel flags (luminance, saturation, chroma)
        """
        # Check cache first
        cache_key = self._get_cache_key(attractors_lab, tolerances, strengths, channels)
        if self.load_from_cache(cache_key):
            return

        logger.info(f"Building {self.size}³ LUT...")

        # Allocate LUT
        self.lut = np.empty((self.size, self.size, self.size, 3), dtype=np.float32)

        # Build LUT by sampling transformation at grid points
        total_points = self.size**3
        processed = 0

        for r_idx in range(self.size):
            for g_idx in range(self.size):
                for b_idx in range(self.size):
                    # Convert indices to RGB values [0, 1]
                    rgb = np.array(
                        [
                            r_idx / (self.size - 1),
                            g_idx / (self.size - 1),
                            b_idx / (self.size - 1),
                        ],
                        dtype=np.float32,
                    )

                    # Apply transformation
                    transformed = transform_func(
                        rgb,
                        attractors_lab,
                        tolerances,
                        strengths,
                        channels[0],
                        channels[1],
                        channels[2],
                    )

                    # Store in LUT
                    self.lut[r_idx, g_idx, b_idx] = transformed

                    processed += 1
                    if processed % 10000 == 0:
                        progress = processed / total_points * 100
                        logger.debug(f"LUT building progress: {progress:.1f}%")

        # Save to cache
        self.save_to_cache(cache_key)
        logger.info(f"LUT built successfully ({total_points} entries)")

    def apply_lut(self, image):
        """
        Apply the LUT to an entire image using trilinear interpolation.

        Args:
            image: Input image (H, W, 3) in RGB [0, 1]

        Returns:
            Transformed image
        """
        if self.lut is None:
            msg = "LUT not built. Call build_lut() first."
            raise ValueError(msg)

        h, w = image.shape[:2]
        logger.debug(f"Applying LUT to {w}×{h} image")

        # Use numba-optimized application
        return apply_lut_trilinear(image, self.lut, self.size)


@numba.njit(parallel=True, cache=True)
def apply_lut_trilinear(image, lut, lut_size):
    """
    Apply 3D LUT using trilinear interpolation (Numba optimized).

    Args:
        image: Input image (H, W, 3)
        lut: 3D lookup table (size, size, size, 3)
        lut_size: Size of the LUT

    Returns:
        Transformed image
    """
    h, w = image.shape[:2]
    result = np.empty_like(image)

    scale = lut_size - 1

    for y in numba.prange(h):
        for x in range(w):
            # Get RGB values
            r = image[y, x, 0]
            g = image[y, x, 1]
            b = image[y, x, 2]

            # Scale to LUT coordinates
            r_scaled = r * scale
            g_scaled = g * scale
            b_scaled = b * scale

            # Get integer indices
            r0 = int(r_scaled)
            g0 = int(g_scaled)
            b0 = int(b_scaled)

            # Clamp indices
            r0 = max(0, min(r0, lut_size - 2))
            g0 = max(0, min(g0, lut_size - 2))
            b0 = max(0, min(b0, lut_size - 2))

            r1 = r0 + 1
            g1 = g0 + 1
            b1 = b0 + 1

            # Get fractional parts
            rf = r_scaled - r0
            gf = g_scaled - g0
            bf = b_scaled - b0

            # Trilinear interpolation
            # Interpolate along R axis
            c000 = lut[r0, g0, b0]
            c100 = lut[r1, g0, b0]
            c00 = c000 * (1 - rf) + c100 * rf

            c010 = lut[r0, g1, b0]
            c110 = lut[r1, g1, b0]
            c10 = c010 * (1 - rf) + c110 * rf

            c001 = lut[r0, g0, b1]
            c101 = lut[r1, g0, b1]
            c01 = c001 * (1 - rf) + c101 * rf

            c011 = lut[r0, g1, b1]
            c111 = lut[r1, g1, b1]
            c11 = c011 * (1 - rf) + c111 * rf

            # Interpolate along G axis
            c0 = c00 * (1 - gf) + c10 * gf
            c1 = c01 * (1 - gf) + c11 * gf

            # Interpolate along B axis
            result[y, x] = c0 * (1 - bf) + c1 * bf

    return result


def create_identity_lut(size=65):
    """
    Create an identity LUT (no transformation).

    Useful for testing and as a base for modifications.
    """
    lut = np.empty((size, size, size, 3), dtype=np.float32)

    for r in range(size):
        for g in range(size):
            for b in range(size):
                lut[r, g, b, 0] = r / (size - 1)
                lut[r, g, b, 1] = g / (size - 1)
                lut[r, g, b, 2] = b / (size - 1)

    return lut


@numba.njit(cache=True)
def transform_pixel_for_lut(
    rgb,
    attractors_lab,
    tolerances,
    strengths,
    enable_luminance,
    enable_saturation,
    enable_hue,
):
    """
    Transform a single pixel for LUT building.

    This is a wrapper around the fused kernel that handles the single pixel case.
    """
    from imgcolorshine.kernel import transform_pixel_fused

    # Transform and return
    r_out, g_out, b_out = transform_pixel_fused(
        rgb[0],
        rgb[1],
        rgb[2],
        attractors_lab,
        tolerances,
        strengths,
        enable_luminance,
        enable_saturation,
        enable_hue,
    )

    return np.array([r_out, g_out, b_out], dtype=np.float32)
