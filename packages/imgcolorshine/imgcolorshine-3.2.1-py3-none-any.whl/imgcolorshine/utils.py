#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["numpy", "loguru"]
# ///
# this_file: src/imgcolorshine/utils.py

"""
Utility functions for memory management and image processing.

Provides helper functions for tiled processing of large images,
memory estimation, validation, and batch operations. Essential
for handling images that exceed available memory.

"""

from collections.abc import Callable

import numpy as np
from loguru import logger


def process_large_image(
    image: np.ndarray,
    transform_func: Callable[[np.ndarray], np.ndarray],
    tile_size: int = 1024,
    overlap: int = 32,
    progress_callback: Callable[[float], None] | None = None,
) -> np.ndarray:
    """
    Process a large image in tiles to manage memory usage.

    Args:
        image: Input image array
        transform_func: Function to apply to each tile
        tile_size: Size of each tile
        overlap: Overlap between tiles to avoid edge artifacts
        progress_callback: Optional callback for progress updates

    Returns:
        Processed image

    Used by transform.py for processing images that exceed memory limits.

    Used in:
    - old/imgcolorshine/imgcolorshine/__init__.py
    - old/imgcolorshine/imgcolorshine/transform.py
    - src/imgcolorshine/transform.py
    """
    h, w = image.shape[:2]
    result = np.zeros_like(image)

    # Calculate number of tiles
    tiles_y = (h + tile_size - 1) // tile_size
    tiles_x = (w + tile_size - 1) // tile_size
    total_tiles = tiles_y * tiles_x
    processed_tiles = 0

    logger.info(f"Processing image in {tiles_x}×{tiles_y} tiles (size: {tile_size}×{tile_size})")

    for ty in range(tiles_y):
        for tx in range(tiles_x):
            # Calculate tile boundaries with overlap
            y_start = ty * tile_size
            y_end = min((ty + 1) * tile_size + overlap, h)
            x_start = tx * tile_size
            x_end = min((tx + 1) * tile_size + overlap, w)

            # Extract tile
            tile = image[y_start:y_end, x_start:x_end]

            # Process tile
            processed_tile = transform_func(tile)

            # Calculate the region to copy (without overlap)
            copy_y_start = 0 if ty == 0 else overlap // 2
            copy_y_end = processed_tile.shape[0] if ty == tiles_y - 1 else -overlap // 2
            copy_x_start = 0 if tx == 0 else overlap // 2
            copy_x_end = processed_tile.shape[1] if tx == tiles_x - 1 else -overlap // 2

            # Calculate destination coordinates
            dest_y_start = y_start if ty == 0 else y_start + overlap // 2
            dest_y_end = y_end if ty == tiles_y - 1 else y_end - overlap // 2
            dest_x_start = x_start if tx == 0 else x_start + overlap // 2
            dest_x_end = x_end if tx == tiles_x - 1 else x_end - overlap // 2

            # Copy processed tile to result
            result[dest_y_start:dest_y_end, dest_x_start:dest_x_end] = processed_tile[
                copy_y_start:copy_y_end, copy_x_start:copy_x_end
            ]

            # Update progress
            processed_tiles += 1
            if progress_callback:
                progress = processed_tiles / total_tiles
                progress_callback(progress)

            if processed_tiles % 10 == 0 or processed_tiles == total_tiles:
                logger.info(
                    f"Processing tiles: {processed_tiles}/{total_tiles} ({processed_tiles / total_tiles * 100:.1f}%)"
                )

    return result


def estimate_optimal_tile_size(image_shape: tuple, available_memory_mb: int = 2048, bytes_per_pixel: int = 12) -> int:
    """
    Estimate optimal tile size based on available memory.

    Args:
        image_shape: Shape of the image (H, W, C)
        available_memory_mb: Available memory in MB
        bytes_per_pixel: Estimated bytes per pixel for processing

    Returns:
        Optimal tile size

    """
    # Convert to bytes
    available_bytes = available_memory_mb * 1024 * 1024

    # Account for overhead (input, output, intermediate)
    overhead_factor = 3.0
    usable_bytes = available_bytes / overhead_factor

    # Calculate pixels that fit in memory
    pixels_in_memory = usable_bytes / bytes_per_pixel

    # Find square tile size
    tile_size = int(np.sqrt(pixels_in_memory))

    # Round to nearest power of 2 for efficiency
    tile_size = 2 ** int(np.log2(tile_size))

    # Clamp to reasonable range
    tile_size = max(256, min(tile_size, 4096))

    logger.debug(f"Optimal tile size: {tile_size}×{tile_size} (for {available_memory_mb}MB memory)")

    return tile_size


def create_progress_bar(total_steps: int, description: str = "Processing"):
    """
    Create a simple progress tracking context.

    This is a placeholder for integration with rich.progress or tqdm.

    """

    class SimpleProgress:
        """"""

        def __init__(self, total: int, desc: str):
            """"""
            self.total = total
            self.current = 0
            self.desc = desc

        def update(self, n: int = 1):
            """"""
            self.current += n
            percent = (self.current / self.total) * 100
            logger.info(f"{self.desc}: {percent:.1f}%")

        def __enter__(self):
            """"""
            return self

        def __exit__(self, *args):
            """"""

    return SimpleProgress(total_steps, description)


def validate_image(image: np.ndarray) -> None:
    """
    Validate image array format and values.

    Args:
        image: Image array to validate

    Raises:
        ValueError: If image is invalid

    Used in:
    - src/imgcolorshine/__init__.py
    """
    # Expected image dimensions
    EXPECTED_NDIM = 3
    EXPECTED_CHANNELS = 3

    if image.ndim != EXPECTED_NDIM:
        msg = f"Image must be 3D (H, W, C), got shape {image.shape}"
        raise ValueError(msg)

    if image.shape[2] != EXPECTED_CHANNELS:
        msg = f"Image must have 3 channels (RGB), got {image.shape[2]}"
        raise ValueError(msg)

    if image.dtype not in (np.float32, np.float64):
        msg = f"Image must be float32 or float64, got {image.dtype}"
        raise ValueError(msg)

    if np.any(image < 0) or np.any(image > 1):
        msg = "Image values must be in range [0, 1]"
        raise ValueError(msg)


def clamp_to_gamut(colors: np.ndarray) -> np.ndarray:
    """
    Clamp colors to valid sRGB gamut.

    Args:
        colors: Array of colors in sRGB space

    Returns:
        Clamped colors

    """
    return np.clip(colors, 0, 1)


def batch_process_images(image_paths: list, output_dir: str, transform_func: Callable, **kwargs) -> None:
    """
    Process multiple images in batch.

    Args:
        image_paths: List of input image paths
        output_dir: Directory for output images
        transform_func: Transformation function
        **kwargs: Additional arguments for transform_func

    Used in:
    - src/imgcolorshine/__init__.py
    """
    from pathlib import Path

    from imgcolorshine.io import ImageProcessor

    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    processor = ImageProcessor()

    for i, image_path in enumerate(image_paths):
        logger.info(f"Processing image {i + 1}/{len(image_paths)}: {image_path}")

        # Load image
        image = processor.load_image(image_path)

        # Transform
        result = transform_func(image, **kwargs)

        # Save with same filename
        output_path = output_dir_path / Path(image_path).name
        processor.save_image(result, output_path)

        logger.info(f"Saved: {output_path}")
