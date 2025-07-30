#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["numpy", "scipy", "loguru"]
# ///
# this_file: src/imgcolorshine/lut.py

"""
3D Look-Up Table (LUT) acceleration for imgcolorshine.

Provides pre-computed color transformation via 3D interpolation for
extremely fast processing of images with the same attractor settings.
"""

from __future__ import annotations

import hashlib
import pickle
from pathlib import Path
from typing import Any

import numpy as np
from loguru import logger
from scipy.interpolate import RegularGridInterpolator

# Constants
DEFAULT_LUT_SIZE = 65  # 65x65x65 3D grid
LUT_CACHE_DIR = Path.home() / ".cache" / "imgcolorshine" / "luts"


class LUTManager:
    """Manages 3D Look-Up Tables for fast color transformation."""

    def __init__(self, cache_dir: Path | None = None, lut_size: int = DEFAULT_LUT_SIZE):
        """Initialize LUT manager.

        Args:
            cache_dir: Directory to store cached LUTs
            lut_size: Size of the 3D LUT grid (e.g., 65 for 65x65x65)
        """
        self.cache_dir = cache_dir or LUT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.lut_size = lut_size
        logger.debug(f"Initialized LUTManager (size={lut_size}, cache={self.cache_dir})")

    def _generate_cache_key(self, attractors: list[Any], flags: dict[str, bool]) -> str:
        """Generate a unique cache key for the transformation settings.

        Args:
            attractors: List of attractor objects
            flags: Channel transformation flags

        Returns:
            SHA256 hash of the settings
        """
        # Create a hashable representation of the settings
        attractor_data = []
        for attr in attractors:
            attractor_data.append(
                {
                    "color": attr.color_str,
                    "tolerance": attr.tolerance,
                    "strength": attr.strength,
                }
            )

        settings = {
            "attractors": attractor_data,
            "flags": flags,
            "lut_size": self.lut_size,
        }

        # Generate hash
        settings_str = str(sorted(settings.items()))
        return hashlib.sha256(settings_str.encode()).hexdigest()

    def _build_lut(
        self,
        transformer: Any,
        attractors: list[Any],
        flags: dict[str, bool],
    ) -> np.ndarray:
        """Build a 3D LUT by transforming a grid of colors.

        Args:
            transformer: ColorTransformer instance
            attractors: List of attractor objects
            flags: Channel transformation flags

        Returns:
            3D LUT array of shape (lut_size, lut_size, lut_size, 3)
        """
        logger.info(f"Building {self.lut_size}³ 3D LUT...")

        # Create a 3D grid of RGB colors
        grid_1d = np.linspace(0, 1, self.lut_size, dtype=np.float32)
        r_grid, g_grid, b_grid = np.meshgrid(grid_1d, grid_1d, grid_1d, indexing="ij")

        # Flatten to create synthetic image
        grid_image = np.stack([r_grid, g_grid, b_grid], axis=-1)
        original_shape = grid_image.shape
        grid_image_flat = grid_image.reshape(-1, 3)

        # Transform the grid using the color transformer
        # Reshape to fake image dimensions for the transformer
        fake_h = int(np.sqrt(len(grid_image_flat)))
        fake_w = len(grid_image_flat) // fake_h
        if fake_h * fake_w < len(grid_image_flat):
            fake_h += 1

        # Pad if necessary
        padding = fake_h * fake_w - len(grid_image_flat)
        if padding > 0:
            grid_image_flat = np.pad(grid_image_flat, ((0, padding), (0, 0)), constant_values=0)

        grid_image_2d = grid_image_flat.reshape(fake_h, fake_w, 3)

        # Transform
        transformed_grid = transformer.transform_image(grid_image_2d, attractors, flags)

        # Reshape back and remove padding
        transformed_flat = transformed_grid.reshape(-1, 3)
        if padding > 0:
            transformed_flat = transformed_flat[:-padding]

        # Reshape to LUT format
        lut = transformed_flat.reshape(original_shape)

        logger.info("LUT build complete")
        return lut

    def get_lut(
        self,
        transformer: Any,
        attractors: list[Any],
        flags: dict[str, bool],
    ) -> tuple[np.ndarray, RegularGridInterpolator]:
        """Get or create a LUT for the given transformation settings.

        Args:
            transformer: ColorTransformer instance
            attractors: List of attractor objects
            flags: Channel transformation flags

        Returns:
            Tuple of (LUT array, interpolator)
        """
        # Generate cache key
        cache_key = self._generate_cache_key(attractors, flags)
        cache_path = self.cache_dir / f"{cache_key}_{self.lut_size}.pkl"

        # Check cache
        if cache_path.exists():
            logger.debug(f"Loading cached LUT: {cache_key[:8]}...")
            try:
                with cache_path.open("rb") as f:
                    lut = pickle.load(f)
                logger.info("Loaded LUT from cache")
            except Exception as e:
                logger.warning(f"Failed to load cached LUT: {e}")
                lut = self._build_lut(transformer, attractors, flags)
                self._save_lut(lut, cache_path)
        else:
            # Build new LUT
            lut = self._build_lut(transformer, attractors, flags)
            self._save_lut(lut, cache_path)

        # Create interpolator
        grid_1d = np.linspace(0, 1, self.lut_size)
        interpolator = RegularGridInterpolator(
            (grid_1d, grid_1d, grid_1d),
            lut,
            method="linear",
            bounds_error=False,
            fill_value=None,
        )

        return lut, interpolator

    def _save_lut(self, lut: np.ndarray, cache_path: Path) -> None:
        """Save LUT to cache.

        Args:
            lut: LUT array to save
            cache_path: Path to save to
        """
        try:
            with cache_path.open("wb") as f:
                pickle.dump(lut, f)
            logger.debug(f"Saved LUT to cache: {cache_path.name}")
        except Exception as e:
            logger.warning(f"Failed to save LUT to cache: {e}")

    def apply_lut(
        self,
        image: np.ndarray,
        interpolator: RegularGridInterpolator,
    ) -> np.ndarray:
        """Apply LUT to an image using trilinear interpolation.

        Args:
            image: Input image (H, W, 3) in range [0, 1]
            interpolator: Pre-computed interpolator

        Returns:
            Transformed image
        """
        logger.debug("Applying LUT transformation...")

        # Flatten image for interpolation
        h, w = image.shape[:2]
        pixels_flat = image.reshape(-1, 3)

        # Apply interpolation
        transformed_flat = interpolator(pixels_flat)

        # Reshape back
        return transformed_flat.reshape(h, w, 3)

    def clear_cache(self) -> None:
        """Clear all cached LUTs."""
        if self.cache_dir.exists():
            for lut_file in self.cache_dir.glob("*.pkl"):
                lut_file.unlink()
            logger.info(f"Cleared LUT cache: {self.cache_dir}")

    def get_cache_info(self) -> dict[str, Any]:
        """Get information about the LUT cache.

        Returns:
            Dictionary with cache statistics
        """
        if not self.cache_dir.exists():
            return {
                "cache_dir": str(self.cache_dir),
                "num_luts": 0,
                "total_size_mb": 0.0,
            }

        lut_files = list(self.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in lut_files)

        return {
            "cache_dir": str(self.cache_dir),
            "num_luts": len(lut_files),
            "total_size_mb": total_size / (1024 * 1024),
            "lut_size": self.lut_size,
        }
