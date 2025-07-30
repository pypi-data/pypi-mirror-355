#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["numpy", "numba"]
# ///
# this_file: src/imgcolorshine/numba_utils.py

"""
Additional Numba-optimized utility functions for imgcolorshine.

Provides performance-critical functions optimized with Numba JIT compilation
for spatial and hierarchical processing operations.
"""

import numba
import numpy as np


@numba.njit(cache=True, parallel=True)
def compute_color_distances_batch(pixels: np.ndarray, attractors: np.ndarray) -> np.ndarray:
    """
    Compute perceptual distances between all pixels and all attractors.

    Uses parallel processing to compute Euclidean distances in Oklab space
    between each pixel and each attractor color.

    Args:
        pixels: Pixel colors in Oklab space (N, 3)
        attractors: Attractor colors in Oklab space (M, 3)

    Returns:
        Distance matrix (N, M) with perceptual distances
    """
    n_pixels = pixels.shape[0]
    n_attractors = attractors.shape[0]
    distances = np.empty((n_pixels, n_attractors), dtype=np.float32)

    for i in numba.prange(n_pixels):
        for j in range(n_attractors):
            # Euclidean distance in Oklab space
            dl = pixels[i, 0] - attractors[j, 0]
            da = pixels[i, 1] - attractors[j, 1]
            db = pixels[i, 2] - attractors[j, 2]
            distances[i, j] = np.sqrt(dl * dl + da * da + db * db)

    return distances


@numba.njit(cache=True, parallel=True)
def find_nearest_attractors(
    pixels: np.ndarray, attractors: np.ndarray, max_distance: float
) -> tuple[np.ndarray, np.ndarray]:
    """
    Find nearest attractor for each pixel within max distance.

    Optimized function to find the closest attractor for each pixel,
    returning both the attractor index and distance.

    Args:
        pixels: Pixel colors in Oklab space (N, 3)
        attractors: Attractor colors in Oklab space (M, 3)
        max_distance: Maximum distance to consider

    Returns:
        Tuple of (nearest_indices, distances) arrays of shape (N,)
        Index is -1 if no attractor within max_distance
    """
    n_pixels = pixels.shape[0]
    n_attractors = attractors.shape[0]

    nearest_indices = np.full(n_pixels, -1, dtype=np.int32)
    nearest_distances = np.full(n_pixels, np.inf, dtype=np.float32)

    for i in numba.prange(n_pixels):
        pixel = pixels[i]
        min_dist = max_distance
        min_idx = -1

        for j in range(n_attractors):
            # Euclidean distance in Oklab space
            dl = pixel[0] - attractors[j, 0]
            da = pixel[1] - attractors[j, 1]
            db = pixel[2] - attractors[j, 2]
            dist = np.sqrt(dl * dl + da * da + db * db)

            if dist < min_dist:
                min_dist = dist
                min_idx = j

        if min_idx >= 0:
            nearest_indices[i] = min_idx
            nearest_distances[i] = min_dist

    return nearest_indices, nearest_distances


@numba.njit(cache=True, parallel=True)
def compute_tile_uniformity(tile: np.ndarray, threshold: float) -> tuple[bool, np.ndarray, float]:
    """
    Check if a tile is uniform in color.

    Computes mean color and variance for a tile, determining if it's
    uniform enough to process as a single unit.

    Args:
        tile: Tile in color space (H, W, 3)
        threshold: Variance threshold for uniformity

    Returns:
        Tuple of (is_uniform, mean_color, variance)
    """
    h, w, c = tile.shape
    n_pixels = h * w

    # Compute mean color
    mean = np.zeros(3, dtype=np.float32)
    for i in range(h):
        for j in range(w):
            for k in range(c):
                mean[k] += tile[i, j, k]
    mean /= n_pixels

    # Compute variance
    variance = 0.0
    for i in range(h):
        for j in range(w):
            for k in range(c):
                diff = tile[i, j, k] - mean[k]
                variance += diff * diff
    variance /= n_pixels * c

    is_uniform = variance < threshold

    return is_uniform, mean, variance


@numba.njit(cache=True, parallel=True)
def apply_transformation_mask(original: np.ndarray, transformed: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    Apply transformation only to masked pixels.

    Efficiently combines original and transformed images based on a mask,
    using parallel processing for optimal performance.

    Args:
        original: Original image (H, W, 3)
        transformed: Transformed image (H, W, 3)
        mask: Boolean mask (H, W) where True = use transformed

    Returns:
        Combined image with selective transformation
    """
    h, w, c = original.shape
    result = np.empty_like(original)

    for i in numba.prange(h):
        for j in range(w):
            if mask[i, j]:
                for k in range(c):
                    result[i, j, k] = transformed[i, j, k]
            else:
                for k in range(c):
                    result[i, j, k] = original[i, j, k]

    return result


@numba.njit(cache=True)
def compute_edge_strength(gray: np.ndarray, threshold: float) -> np.ndarray:
    """
    Compute edge strength map using simple gradient.

    Fast edge detection for identifying high-frequency regions
    that need fine-resolution processing.

    Args:
        gray: Grayscale image
        threshold: Edge strength threshold

    Returns:
        Boolean mask where True = strong edge
    """
    h, w = gray.shape
    edges = np.zeros((h, w), dtype=np.bool_)

    # Simple gradient computation (skip borders)
    for i in range(1, h - 1):
        for j in range(1, w - 1):
            # Horizontal and vertical gradients
            gx = abs(gray[i, j + 1] - gray[i, j - 1])
            gy = abs(gray[i + 1, j] - gray[i - 1, j])

            # Combined gradient magnitude
            grad = np.sqrt(gx * gx + gy * gy)
            edges[i, j] = grad > threshold

    return edges


@numba.njit(cache=True, parallel=True)
def downsample_oklab(image: np.ndarray, factor: int) -> np.ndarray:
    """
    Downsample image in Oklab space with proper averaging.

    Performs area-averaging downsampling that's perceptually correct
    in Oklab color space.

    Args:
        image: Image in Oklab space (H, W, 3)
        factor: Downsampling factor (must divide dimensions evenly)

    Returns:
        Downsampled image (H//factor, W//factor, 3)
    """
    h, w, c = image.shape
    new_h = h // factor
    new_w = w // factor

    result = np.zeros((new_h, new_w, c), dtype=np.float32)

    # Area averaging
    for i in numba.prange(new_h):
        for j in range(new_w):
            # Sum over the block
            for k in range(c):
                sum_val = 0.0
                for di in range(factor):
                    for dj in range(factor):
                        sum_val += image[i * factor + di, j * factor + dj, k]
                result[i, j, k] = sum_val / (factor * factor)

    return result
