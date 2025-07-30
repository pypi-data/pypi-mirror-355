#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["numpy", "scipy", "loguru", "numba"]
# ///
# this_file: src/imgcolorshine/spatial.py

"""
Spatial acceleration structures for imgcolorshine.

Implements KD-tree based spatial indexing to quickly identify which pixels
can be affected by which attractors, enabling early termination and
tile coherence optimizations.
"""

from collections.abc import Callable
from dataclasses import dataclass

import numba
import numpy as np
from loguru import logger
from scipy.spatial import KDTree


@numba.njit(cache=True, parallel=True)
def compute_influence_mask_direct(
    pixels_flat: np.ndarray, centers: np.ndarray, radii: np.ndarray
) -> np.ndarray:
    """
    Numba-optimized direct computation of influence mask.

    Computes which pixels fall within any attractor's influence radius
    using parallel processing for maximum performance.

    Args:
        pixels_flat: Flattened pixel array in Oklab space (N, 3)
        centers: Attractor centers in Oklab space (M, 3)
        radii: Influence radii for each attractor (M,)

    Returns:
        Boolean mask (N,) where True indicates influenced pixels
    """
    n_pixels = pixels_flat.shape[0]
    n_attractors = centers.shape[0]
    mask = np.zeros(n_pixels, dtype=np.bool_)

    # Process pixels in parallel
    for i in numba.prange(n_pixels):
        pixel = pixels_flat[i]

        # Check against each attractor
        for j in range(n_attractors):
            # Compute Euclidean distance in Oklab space
            dx = pixel[0] - centers[j, 0]
            dy = pixel[1] - centers[j, 1]
            dz = pixel[2] - centers[j, 2]
            distance = np.sqrt(dx * dx + dy * dy + dz * dz)

            # Check if within influence radius
            if distance <= radii[j]:
                mask[i] = True
                break  # No need to check other attractors

    return mask


@numba.njit(cache=True)
def find_pixel_attractors(
    pixel: np.ndarray, centers: np.ndarray, radii: np.ndarray, indices: np.ndarray
) -> np.ndarray:
    """
    Numba-optimized function to find attractors influencing a pixel.

    Args:
        pixel: Single pixel in Oklab space (3,)
        centers: Attractor centers in Oklab space (M, 3)
        radii: Influence radii for each attractor (M,)
        indices: Attractor indices (M,)

    Returns:
        Array of attractor indices that influence this pixel
    """
    n_attractors = centers.shape[0]
    influencing = []

    for j in range(n_attractors):
        # Compute Euclidean distance in Oklab space
        dx = pixel[0] - centers[j, 0]
        dy = pixel[1] - centers[j, 1]
        dz = pixel[2] - centers[j, 2]
        distance = np.sqrt(dx * dx + dy * dy + dz * dz)

        # Check if within influence radius
        if distance <= radii[j]:
            influencing.append(indices[j])

    # Convert to numpy array
    if influencing:
        return np.array(influencing, dtype=np.int32)
    return np.empty(0, dtype=np.int32)


@dataclass
class InfluenceRegion:
    """Represents an attractor's region of influence in color space."""

    center: np.ndarray  # Oklab coordinates
    radius: float  # Max perceptual distance
    attractor_idx: int


@dataclass
class TileInfo:
    """Information about a tile for coherence optimization."""

    uniform: bool
    mean_color: np.ndarray
    variance: float
    dominant_attractors: list[int]
    coords: tuple[int, int, int, int]


class SpatialAccelerator:
    """Spatial acceleration for color transformation queries."""

    def __init__(
        self,
        uniformity_threshold: float = 0.01,
        tile_size: int = 64,
        cache_tiles: bool = True,
    ):
        """
        Initialize spatial accelerator.

        Args:
            uniformity_threshold: Variance threshold for uniform tiles
            tile_size: Size for tile coherence analysis
            cache_tiles: Whether to cache tile analysis results
        """
        self.uniformity_threshold = uniformity_threshold
        self.tile_size = tile_size
        self.cache_tiles = cache_tiles
        self.color_tree: KDTree | None = None
        self.influence_regions: list[InfluenceRegion] = []
        self.tile_cache: dict[tuple, TileInfo] = {}
        self._max_radius: float = 0.0

    def build_spatial_index(
        self, attractors_oklab: np.ndarray, tolerances: np.ndarray
    ) -> None:
        """
        Build KD-tree and influence regions from attractors.

        Creates a spatial index for fast nearest-neighbor queries
        in Oklab color space.

        Args:
            attractors_oklab: Attractor colors in Oklab space (N, 3)
            tolerances: Tolerance values (0-100) for each attractor
        """
        # Import MAX_DELTA_E from transforms module
        from imgcolorshine.transform import MAX_DELTA_E

        # Map tolerances to perceptual distances
        max_distances = MAX_DELTA_E * (tolerances / 100.0)
        self._max_radius = np.max(max_distances)

        # Build KD-tree from attractor coordinates
        self.color_tree = KDTree(attractors_oklab)

        # Store influence regions
        self.influence_regions = [
            InfluenceRegion(
                center=attractors_oklab[i].copy(),
                radius=max_distances[i],
                attractor_idx=i,
            )
            for i in range(len(attractors_oklab))
        ]

        # Clear tile cache when index is rebuilt
        self.tile_cache.clear()

        logger.debug(
            f"Built spatial index: {len(self.influence_regions)} attractors, max radius {self._max_radius:.3f}"
        )

    def get_influenced_pixels_mask(self, pixels_oklab: np.ndarray) -> np.ndarray:
        """
        Create mask of pixels within any attractor's influence.

        Uses KD-tree for efficient spatial queries to determine which
        pixels fall within at least one attractor's influence radius.

        Args:
            pixels_oklab: Pixel colors in Oklab space (H, W, 3)

        Returns:
            Boolean mask (H, W) where True = pixel needs processing
        """
        if not self.influence_regions:
            logger.warning("No influence regions defined")
            return np.zeros(pixels_oklab.shape[:2], dtype=bool)

        h, w = pixels_oklab.shape[:2]
        pixels_flat = pixels_oklab.reshape(-1, 3)

        # Initialize mask
        mask_flat = np.zeros(len(pixels_flat), dtype=bool)

        # For each influence region, find pixels within radius
        for region in self.influence_regions:
            # Query all points within this region's radius
            indices = self.color_tree.query_ball_point(
                pixels_flat, r=region.radius, workers=-1
            )

            # Check which pixels are close to this specific attractor
            for idx, neighbors in enumerate(indices):
                if region.attractor_idx in neighbors:
                    mask_flat[idx] = True

        # Alternative approach: check each pixel against all regions
        # This might be faster for small numbers of attractors
        if len(self.influence_regions) < 10:
            mask_flat_alt = self._get_mask_direct(pixels_flat)
            # Use the direct method if we have few attractors
            mask_flat = mask_flat_alt

        return mask_flat.reshape(h, w)

    def _get_mask_direct(self, pixels_flat: np.ndarray) -> np.ndarray:
        """
        Direct method to compute influence mask using Numba optimization.

        More efficient for small numbers of attractors. Uses parallel
        processing to compute distances for all pixels simultaneously.

        Args:
            pixels_flat: Flattened pixel array in Oklab space (N, 3)

        Returns:
            Boolean mask (N,)
        """
        if not self.influence_regions:
            return np.zeros(len(pixels_flat), dtype=bool)

        # Prepare data for Numba function
        len(self.influence_regions)
        centers = np.array(
            [region.center for region in self.influence_regions], dtype=np.float32
        )
        radii = np.array(
            [region.radius for region in self.influence_regions], dtype=np.float32
        )

        # Use Numba-optimized function for parallel computation
        return compute_influence_mask_direct(
            pixels_flat.astype(np.float32), centers, radii
        )

    def query_pixel_attractors(self, pixel_oklab: np.ndarray) -> list[int]:
        """
        Find which attractors influence a specific pixel using Numba optimization.

        Uses optimized distance computation to quickly identify all attractors
        that have influence over the given pixel color.

        Args:
            pixel_oklab: Single pixel color in Oklab space (3,)

        Returns:
            List of attractor indices that influence this pixel
        """
        if not self.influence_regions:
            return []

        # Prepare data for Numba function
        len(self.influence_regions)
        centers = np.array(
            [region.center for region in self.influence_regions], dtype=np.float32
        )
        radii = np.array(
            [region.radius for region in self.influence_regions], dtype=np.float32
        )
        indices = np.array(
            [region.attractor_idx for region in self.influence_regions], dtype=np.int32
        )

        # Use Numba-optimized function
        result = find_pixel_attractors(
            pixel_oklab.astype(np.float32), centers, radii, indices
        )

        return result.tolist()

    @staticmethod
    @numba.njit
    def _compute_tile_stats(tile_oklab: np.ndarray) -> tuple[np.ndarray, float]:
        """
        Compute mean and variance for a tile.

        Numba-optimized for performance.

        Args:
            tile_oklab: Tile in Oklab space (H, W, 3)

        Returns:
            Tuple of (mean_color, variance)
        """
        h, w, c = tile_oklab.shape
        n_pixels = h * w

        # Compute mean
        mean = np.zeros(3, dtype=np.float32)
        for y in range(h):
            for x in range(w):
                for ch in range(c):
                    mean[ch] += tile_oklab[y, x, ch]
        mean /= n_pixels

        # Compute variance
        variance = 0.0
        for y in range(h):
            for x in range(w):
                for ch in range(c):
                    diff = tile_oklab[y, x, ch] - mean[ch]
                    variance += diff * diff
        variance /= n_pixels

        return mean, variance

    def analyze_tile_coherence(
        self, tile_oklab: np.ndarray, tile_coords: tuple[int, int, int, int]
    ) -> TileInfo:
        """
        Analyze spatial coherence within a tile for optimization.

        Determines if a tile is uniform enough to process as a single unit,
        and identifies which attractors affect the tile.

        Args:
            tile_oklab: Tile in Oklab space
            tile_coords: Tile boundaries (y1, y2, x1, x2)

        Returns:
            TileInfo with coherence analysis results
        """
        # Check cache first
        if self.cache_tiles and tile_coords in self.tile_cache:
            return self.tile_cache[tile_coords]

        # Compute statistics
        mean_color, variance = self._compute_tile_stats(tile_oklab)

        # Check uniformity
        is_uniform = variance < self.uniformity_threshold

        # Find dominant attractors
        if is_uniform:
            # For uniform tiles, check which attractors affect the mean color
            dominant_attractors = self.query_pixel_attractors(mean_color)
        else:
            # Sample tile at key points
            h, w = tile_oklab.shape[:2]
            sample_points = [
                tile_oklab[0, 0],  # Top-left
                tile_oklab[0, w - 1],  # Top-right
                tile_oklab[h - 1, 0],  # Bottom-left
                tile_oklab[h - 1, w - 1],  # Bottom-right
                tile_oklab[h // 2, w // 2],  # Center
            ]

            # Find common attractors across sample points
            attractor_sets = [
                set(self.query_pixel_attractors(p)) for p in sample_points
            ]
            if attractor_sets:
                common_attractors = set.intersection(*attractor_sets)
                dominant_attractors = list(common_attractors)
            else:
                dominant_attractors = []

        result = TileInfo(
            uniform=is_uniform,
            mean_color=mean_color,
            variance=variance,
            dominant_attractors=dominant_attractors,
            coords=tile_coords,
        )

        # Cache result
        if self.cache_tiles:
            self.tile_cache[tile_coords] = result

        return result

    def transform_with_spatial_accel(
        self,
        image_rgb: np.ndarray,
        image_oklab: np.ndarray,
        attractors_oklab: np.ndarray,
        tolerances: np.ndarray,
        strengths: np.ndarray,
        transform_func: Callable,
        channels: list[bool],
    ) -> np.ndarray:
        """
        Transform image using spatial acceleration.

        Main entry point for spatially-accelerated transformation.
        Builds spatial index and uses it to skip unaffected pixels.

        Args:
            image_rgb: Original image in RGB
            image_oklab: Image in Oklab space
            attractors_oklab: Attractor colors in Oklab
            tolerances: Tolerance values
            strengths: Strength values
            transform_func: Function to transform pixels
            channels: Channel enable flags

        Returns:
            Transformed image in RGB
        """
        # Build spatial index
        self.build_spatial_index(attractors_oklab, tolerances)

        # Get influenced pixels mask
        influence_mask = self.get_influenced_pixels_mask(image_oklab)

        # Early exit if no pixels are influenced
        if not np.any(influence_mask):
            logger.info("No pixels within attractor influence, returning original")
            return image_rgb

        # Calculate statistics
        total_pixels = influence_mask.size
        influenced_pixels = np.sum(influence_mask)
        influence_ratio = influenced_pixels / total_pixels

        logger.info(
            f"Spatial acceleration: processing {influenced_pixels:,} of {total_pixels:,} "
            f"pixels ({influence_ratio * 100:.1f}%)"
        )

        # If most pixels are influenced, skip spatial optimization
        if influence_ratio > 0.8:
            logger.debug("Most pixels influenced, using standard processing")
            return transform_func(
                image_rgb, attractors_oklab, tolerances, strengths, channels
            )

        # Process with spatial optimization
        # For now, we'll use a simple approach - in production this would be optimized
        result = image_rgb.copy()

        # Transform the whole image (this is the optimization opportunity)
        transformed = transform_func(
            image_rgb, attractors_oklab, tolerances, strengths, channels
        )

        # Apply only to influenced pixels
        result[influence_mask] = transformed[influence_mask]

        return result

    def process_with_tile_coherence(
        self,
        image_rgb: np.ndarray,
        image_oklab: np.ndarray,
        attractors_oklab: np.ndarray,
        tolerances: np.ndarray,
        strengths: np.ndarray,
        transform_func: Callable,
        channels: list[bool],
        tile_size: int | None = None,
    ) -> np.ndarray:
        """
        Process image using tile coherence optimization.

        Divides image into tiles and processes uniform tiles more efficiently.

        Args:
            image_rgb: Original image in RGB
            image_oklab: Image in Oklab space
            attractors_oklab: Attractor colors
            tolerances: Tolerance values
            strengths: Strength values
            transform_func: Transformation function
            channels: Channel flags
            tile_size: Override default tile size

        Returns:
            Transformed image
        """
        if tile_size is None:
            tile_size = self.tile_size

        h, w = image_rgb.shape[:2]
        result = np.zeros_like(image_rgb)

        # Process in tiles
        uniform_tiles = 0
        total_tiles = 0

        for y in range(0, h, tile_size):
            for x in range(0, w, tile_size):
                # Get tile boundaries
                y2 = min(y + tile_size, h)
                x2 = min(x + tile_size, w)
                coords = (y, y2, x, x2)

                # Extract tiles
                tile_rgb = image_rgb[y:y2, x:x2]
                tile_oklab = image_oklab[y:y2, x:x2]

                # Analyze tile
                tile_info = self.analyze_tile_coherence(tile_oklab, coords)
                total_tiles += 1

                if tile_info.uniform and tile_info.dominant_attractors:
                    # Uniform tile with attractors - transform mean color only
                    uniform_tiles += 1

                    # Transform the mean color
                    mean_rgb = np.mean(tile_rgb.reshape(-1, 3), axis=0)
                    transformed_mean = transform_func(
                        mean_rgb.reshape(1, 1, 3),
                        attractors_oklab[tile_info.dominant_attractors],
                        tolerances[tile_info.dominant_attractors],
                        strengths[tile_info.dominant_attractors],
                        channels,
                    )[0, 0]

                    # Apply to entire tile
                    result[y:y2, x:x2] = transformed_mean

                elif not tile_info.dominant_attractors:
                    # No attractors affect this tile, copy original
                    result[y:y2, x:x2] = tile_rgb

                else:
                    # Non-uniform tile, process normally
                    result[y:y2, x:x2] = transform_func(
                        tile_rgb, attractors_oklab, tolerances, strengths, channels
                    )

        logger.info(
            f"Tile coherence: {uniform_tiles}/{total_tiles} tiles were uniform "
            f"({uniform_tiles / total_tiles * 100:.1f}%)"
        )

        return result

    def clear_cache(self) -> None:
        """Clear the tile cache."""
        self.tile_cache.clear()
        logger.debug("Cleared tile cache")
