#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["numpy", "opencv-python", "loguru", "numba"]
# ///
# this_file: src/imgcolorshine/fast_hierar.py

"""
Hierarchical multi-resolution image processing for imgcolorshine.

Implements a coarse-to-fine processing strategy that reduces computation
by processing low-resolution versions first and only refining pixels that
differ significantly from the coarse approximation.
"""

from collections.abc import Callable
from dataclasses import dataclass

import cv2
import numba
import numpy as np
from loguru import logger

from imgcolorshine.trans_numba import batch_srgb_to_oklab


@numba.njit(cache=True, parallel=True)
def compute_perceptual_distance_mask(
    fine_lab: np.ndarray, coarse_lab: np.ndarray, threshold: float
) -> np.ndarray:
    """
    Numba-optimized perceptual difference mask computation.

    Computes perceptual distance in Oklab space and creates a mask of pixels
    that exceed the threshold. Uses parallel processing for maximum performance.

    Args:
        fine_lab: Fine resolution image in Oklab space (H, W, 3)
        coarse_lab: Upsampled coarse result in Oklab space (H, W, 3)
        threshold: Perceptual distance threshold (0-2.5 range)

    Returns:
        Boolean mask where True indicates pixels needing refinement
    """
    h, w = fine_lab.shape[:2]
    mask = np.empty((h, w), dtype=np.bool_)

    # Process pixels in parallel
    for i in numba.prange(h):
        for j in range(w):
            # Perceptual distance in Oklab space (Euclidean distance)
            dl = fine_lab[i, j, 0] - coarse_lab[i, j, 0]
            da = fine_lab[i, j, 1] - coarse_lab[i, j, 1]
            db = fine_lab[i, j, 2] - coarse_lab[i, j, 2]
            distance = np.sqrt(dl * dl + da * da + db * db)
            mask[i, j] = distance > threshold

    return mask


@numba.njit(cache=True)
def compute_gradient_magnitude(gray: np.ndarray) -> np.ndarray:
    """
    Numba-optimized gradient magnitude computation using Sobel operators.

    Computes gradient magnitude efficiently without using OpenCV functions.

    Args:
        gray: Grayscale image

    Returns:
        Gradient magnitude array
    """
    h, w = gray.shape
    grad_mag = np.zeros((h, w), dtype=np.float32)

    # Sobel kernels
    sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)

    # Apply Sobel operators (skip borders)
    for i in range(1, h - 1):
        for j in range(1, w - 1):
            gx = 0.0
            gy = 0.0

            # Convolve with Sobel kernels
            for ki in range(3):
                for kj in range(3):
                    pixel = gray[i + ki - 1, j + kj - 1]
                    gx += pixel * sobel_x[ki, kj]
                    gy += pixel * sobel_y[ki, kj]

            # Gradient magnitude
            grad_mag[i, j] = np.sqrt(gx * gx + gy * gy)

    return grad_mag


@dataclass
class PyramidLevel:
    """Represents one level in the image pyramid."""

    image: np.ndarray
    scale: float
    shape: tuple[int, int]
    level: int


class HierarchicalProcessor:
    """Multi-resolution image processing with adaptive refinement."""

    def __init__(
        self,
        min_size: int = 64,
        difference_threshold: float = 0.1,
        pyramid_factor: float = 0.5,
        use_adaptive_subdivision: bool = True,
        gradient_threshold: float = 0.05,
    ):
        """
        Initialize fast_hierar processor.

        Args:
            min_size: Minimum dimension for coarsest pyramid level
            difference_threshold: Threshold for refinement in perceptual units
            pyramid_factor: Downsampling factor between pyramid levels
            use_adaptive_subdivision: Enable gradient-based subdivision
            gradient_threshold: Threshold for detecting high-gradient regions
        """
        self.min_size = min_size
        self.difference_threshold = difference_threshold
        self.pyramid_factor = pyramid_factor
        self.use_adaptive_subdivision = use_adaptive_subdivision
        self.gradient_threshold = gradient_threshold
        self.pyramid_levels: list[PyramidLevel] = []

    def build_pyramid(self, image: np.ndarray) -> list[PyramidLevel]:
        """
        Build Gaussian pyramid from input image.

        Uses cv2.pyrDown for proper Gaussian filtering and downsampling.

        Args:
            image: Input image in RGB format

        Returns:
            List of pyramid levels from fine to coarse
        """
        levels = []
        current = image.copy()
        level = 0

        # Build pyramid until we reach minimum size
        while min(current.shape[:2]) > self.min_size:
            levels.append(
                PyramidLevel(
                    image=current.copy(),
                    scale=self.pyramid_factor**level,
                    shape=current.shape[:2],
                    level=level,
                )
            )

            # Downsample for next level
            current = cv2.pyrDown(current)
            level += 1

        # Add final coarsest level
        levels.append(
            PyramidLevel(
                image=current,
                scale=self.pyramid_factor**level,
                shape=current.shape[:2],
                level=level,
            )
        )

        logger.debug(
            f"Built pyramid with {len(levels)} levels: {[l.shape for l in levels]}"
        )
        return levels

    @staticmethod
    @numba.njit
    def _compute_perceptual_distance(lab1: np.ndarray, lab2: np.ndarray) -> np.ndarray:
        """
        Compute perceptual distance between two Lab images.

        Args:
            lab1: First image in Lab space (H, W, 3)
            lab2: Second image in Lab space (H, W, 3)

        Returns:
            Distance map (H, W)
        """
        # Simple Euclidean distance in Lab space
        # For better accuracy, could use CIEDE2000 but it's more complex
        diff = lab1 - lab2
        return np.sqrt(diff[:, :, 0] ** 2 + diff[:, :, 1] ** 2 + diff[:, :, 2] ** 2)

    def compute_difference_mask(
        self, fine_level: np.ndarray, coarse_upsampled: np.ndarray, threshold: float
    ) -> np.ndarray:
        """
        Create mask of pixels that need refinement using perceptual color distance.

        Compares fine level with upsampled coarse result in Oklab color space
        to identify pixels that differ significantly and need reprocessing.
        This provides more accurate refinement decisions based on human perception.

        Args:
            fine_level: Fine resolution image (RGB, 0-255)
            coarse_upsampled: Upsampled coarse result (RGB, 0-255)
            threshold: Perceptual distance threshold (0-1 maps to 0-2.5 in Oklab)

        Returns:
            Boolean mask where True indicates pixels needing refinement
        """
        # Normalize RGB to 0-1 range for color space conversion
        fine_norm = fine_level.astype(np.float32) / 255.0
        coarse_norm = coarse_upsampled.astype(np.float32) / 255.0

        # Convert to Oklab for perceptual distance calculation
        # This is ~77-115x faster than using ColorAide
        fine_lab = batch_srgb_to_oklab(fine_norm)
        coarse_lab = batch_srgb_to_oklab(coarse_norm)

        # Map threshold from 0-1 range to Oklab distance range (0-2.5)
        oklab_threshold = threshold * 2.5

        # Use Numba-optimized function for mask computation
        return compute_perceptual_distance_mask(fine_lab, coarse_lab, oklab_threshold)

    def detect_gradient_regions(
        self, image: np.ndarray, gradient_threshold: float
    ) -> np.ndarray:
        """
        Detect regions with high color gradients using Numba-optimized Sobel operators.

        Finds areas with rapid color changes that benefit from fine-resolution
        processing. Uses optimized gradient computation for better performance.

        Args:
            image: Input image (RGB, 0-255)
            gradient_threshold: Threshold for gradient magnitude (0-1)

        Returns:
            Boolean mask of high-gradient regions
        """
        # Convert to grayscale for edge detection
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY).astype(np.float32)

        # Use Numba-optimized gradient computation
        gradient_magnitude = compute_gradient_magnitude(gray)

        # Normalize gradient magnitude
        max_grad = gradient_magnitude.max()
        if max_grad > 0:
            gradient_magnitude = gradient_magnitude / max_grad

        # Create mask
        gradient_mask = gradient_magnitude > gradient_threshold

        # Dilate to ensure coverage of edge regions
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        gradient_mask = cv2.dilate(gradient_mask.astype(np.uint8), kernel)

        return gradient_mask.astype(bool)

    def process_hierarchical(
        self,
        image: np.ndarray,
        transform_func: Callable,
        attractors: np.ndarray,
        tolerances: np.ndarray,
        strengths: np.ndarray,
        channels: list[bool],
    ) -> np.ndarray:
        """
        Process image hierarchically from coarse to fine resolution.

        Main algorithm that implements the multi-resolution processing strategy.
        Starts with coarsest level and progressively refines the result.

        Args:
            image: Input image (RGB format, 0-255 range)
            transform_func: Function to transform pixels
            attractors: Attractor colors in Lab space
            tolerances: Tolerance values for each attractor
            strengths: Strength values for each attractor
            channels: Boolean flags for L, C, H channels

        Returns:
            Transformed image in RGB format
        """
        # Build image pyramid
        pyramid = self.build_pyramid(image)

        if len(pyramid) == 1:
            # Image too small for pyramid, process directly
            logger.debug("Image too small for pyramid, processing directly")
            return transform_func(image, attractors, tolerances, strengths, channels)

        # Process coarsest level completely
        coarsest = pyramid[-1]
        logger.info(f"Processing coarsest level: {coarsest.shape}")

        # Transform the coarsest level
        result = transform_func(
            coarsest.image, attractors, tolerances, strengths, channels
        )

        # Statistics tracking
        total_pixels_refined = 0
        total_pixels = 0

        # Process from coarse to fine
        for i in range(len(pyramid) - 2, -1, -1):
            level = pyramid[i]
            h, w = level.shape[:2]
            total_pixels += h * w

            logger.debug(f"Processing pyramid level {i}: {level.shape}")

            # Upsample previous result to current resolution
            upsampled = cv2.resize(result, (w, h), interpolation=cv2.INTER_LINEAR)

            # Compute refinement mask
            diff_mask = self.compute_difference_mask(
                level.image, upsampled, self.difference_threshold
            )

            # Add gradient regions if enabled
            if self.use_adaptive_subdivision:
                gradient_mask = self.detect_gradient_regions(
                    level.image, self.gradient_threshold
                )
                refinement_mask = diff_mask | gradient_mask
            else:
                refinement_mask = diff_mask

            # Count refined pixels
            num_refined = np.sum(refinement_mask)
            total_pixels_refined += num_refined

            # Process only masked pixels if any need refinement
            if num_refined > 0:
                logger.debug(
                    f"Refining {num_refined} pixels ({num_refined / refinement_mask.size * 100:.1f}%)"
                )

                # For efficient processing, we need to handle masked transformation
                # This is a simplified approach - in production, we'd optimize this
                refined_result = upsampled.copy()

                # Transform the entire level (optimization opportunity here)
                transformed_level = transform_func(
                    level.image, attractors, tolerances, strengths, channels
                )

                # Apply only to masked pixels
                refined_result[refinement_mask] = transformed_level[refinement_mask]

                result = refined_result
            else:
                # No refinement needed, use upsampled result
                logger.debug("No refinement needed at this level")
                result = upsampled

        # Log statistics
        if total_pixels > 0:
            refinement_ratio = total_pixels_refined / total_pixels
            logger.info(
                f"Hierarchical processing complete: refined {refinement_ratio * 100:.1f}% of pixels"
            )

        return result

    def process_hierarchical_tiled(
        self,
        image: np.ndarray,
        transform_func: Callable,
        attractors: np.ndarray,
        tolerances: np.ndarray,
        strengths: np.ndarray,
        channels: list[bool],
        tile_size: int = 512,
    ) -> np.ndarray:
        """
        Hierarchical processing with tiling for very large images.

        Combines fast_hierar processing with tile-based memory management
        for processing images that don't fit in memory.

        Args:
            image: Input image
            transform_func: Transformation function
            attractors: Attractor colors
            tolerances: Tolerance values
            strengths: Strength values
            channels: Channel flags
            tile_size: Size of tiles for processing

        Returns:
            Transformed image
        """
        h, w = image.shape[:2]

        # If image is small enough, process without tiling
        if h <= tile_size * 2 and w <= tile_size * 2:
            return self.process_hierarchical(
                image, transform_func, attractors, tolerances, strengths, channels
            )

        logger.info(f"Processing large image ({h}x{w}) with tiled fast_hierar approach")

        # Create output array
        result = np.zeros_like(image)

        # Process in tiles with overlap
        overlap = tile_size // 4  # 25% overlap

        for y in range(0, h, tile_size - overlap):
            for x in range(0, w, tile_size - overlap):
                # Calculate tile boundaries with padding
                y1 = max(0, y - overlap // 2)
                y2 = min(h, y + tile_size + overlap // 2)
                x1 = max(0, x - overlap // 2)
                x2 = min(w, x + tile_size + overlap // 2)

                logger.debug(f"Processing tile [{y1}:{y2}, {x1}:{x2}]")

                # Extract tile
                tile = image[y1:y2, x1:x2]

                # Process tile hierarchically
                processed_tile = self.process_hierarchical(
                    tile, transform_func, attractors, tolerances, strengths, channels
                )

                # Blend into result (simple approach - could use feathering)
                # Take center region without overlap
                ty1 = overlap // 2 if y > 0 else 0
                ty2 = processed_tile.shape[0] - (overlap // 2 if y2 < h else 0)
                tx1 = overlap // 2 if x > 0 else 0
                tx2 = processed_tile.shape[1] - (overlap // 2 if x2 < w else 0)

                ry1 = y1 + ty1
                ry2 = y1 + ty2
                rx1 = x1 + tx1
                rx2 = x1 + tx2

                result[ry1:ry2, rx1:rx2] = processed_tile[ty1:ty2, tx1:tx2]

        return result
