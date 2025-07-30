#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["numpy", "loguru", "opencv-python", "pillow"]
# ///
# this_file: src/imgcolorshine/io.py

"""
High-performance image I/O with OpenCV and PIL fallback.

Provides efficient image loading and saving with automatic format detection,
memory estimation for large images, and tiling support. OpenCV is preferred
for performance, with PIL as a fallback.

"""

from pathlib import Path
from typing import Any

import numpy as np
from loguru import logger

# Try to import OpenCV first (faster), fall back to PIL
try:
    import cv2

    HAS_OPENCV = True
    logger.debug("Using OpenCV for image I/O")
except ImportError:
    HAS_OPENCV = False
    logger.warning("OpenCV not available, falling back to PIL")

from PIL import Image


class ImageProcessor:
    """Handles image loading and saving with optimal performance.

    Provides high-performance image I/O with OpenCV (preferred) or PIL fallback.
    Includes memory estimation and tiling support for large images. Used throughout
    the application for all image file operations.

    Used in:
    - old/imgcolorshine/imgcolorshine/__init__.py
    - old/imgcolorshine/imgcolorshine/transform.py
    - old/imgcolorshine/imgcolorshine/utils.py
    - old/imgcolorshine/imgcolorshine_main.py
    - old/imgcolorshine/test_imgcolorshine.py
    - src/imgcolorshine/__init__.py
    - src/imgcolorshine/colorshine.py
    - src/imgcolorshine/transform.py
    - src/imgcolorshine/utils.py
    """

    def __init__(self, tile_size: int = 1024) -> None:
        """
        Initialize the image processor.

        Args:
            tile_size: Size of tiles for processing large images

        """
        self.tile_size = tile_size
        self.use_opencv = HAS_OPENCV
        logger.debug(f"ImageProcessor initialized (OpenCV: {self.use_opencv}, tile_size: {tile_size})")

    def load_image(self, path: str | Path) -> np.ndarray[Any, Any]:
        """
        Load an image from file.

        Args:
            path: Path to the image file

        Returns:
            Image as numpy array with shape (H, W, 3) and values in [0, 1]

        Used by utils.py and main CLI for loading input images.

        Used in:
        - old/imgcolorshine/imgcolorshine/utils.py
        - old/imgcolorshine/imgcolorshine_main.py
        - src/imgcolorshine/colorshine.py
        - src/imgcolorshine/utils.py
        """
        path = Path(path)

        if not path.exists():
            msg = f"Image not found: {path}"
            raise FileNotFoundError(msg)

        logger.info(f"Loading image: {path}")

        if self.use_opencv:
            return self._load_opencv(path)
        return self._load_pil(path)

    def save_image(self, image: np.ndarray[Any, Any], path: str | Path, quality: int = 95) -> None:
        """
        Save an image to file.

        Args:
            image: Image array with values in [0, 1]
            path: Output path
            quality: JPEG quality (1-100) or PNG compression (0-9)

        Used by utils.py and main CLI for saving output images.

        Used in:
        - old/imgcolorshine/imgcolorshine/utils.py
        - old/imgcolorshine/imgcolorshine_main.py
        - old/imgcolorshine/test_imgcolorshine.py
        - src/imgcolorshine/colorshine.py
        - src/imgcolorshine/utils.py
        """
        path = Path(path)

        # Ensure output directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving image: {path}")

        if self.use_opencv:
            self._save_opencv(image, path, quality)
        else:
            self._save_pil(image, path, quality)

    def _load_opencv(self, path: Path) -> np.ndarray[Any, Any]:
        """Load image using OpenCV for better performance."""
        # OpenCV loads as BGR, we need RGB
        img = cv2.imread(str(path), cv2.IMREAD_COLOR)

        if img is None:
            msg = f"Failed to load image: {path}"
            raise ValueError(msg)

        # Convert BGR to RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Convert to float [0, 1]
        img = img.astype(np.float32) / 255.0

        h, w = img.shape[:2]
        size_mb = (h * w * 3 * 4) / (1024 * 1024)  # Float32 size in MB
        logger.debug(f"Loaded {w}×{h} image with OpenCV ({size_mb:.1f} MB in memory)")

        # Ensure C-contiguous memory layout for optimal performance
        return np.ascontiguousarray(img)

    def _load_pil(self, path: Path) -> np.ndarray[Any, Any]:
        """Load image using PIL as fallback."""
        with Image.open(path) as img:
            # Convert to RGB if necessary
            if img.mode != "RGB":
                logger.debug(f"Converting from {img.mode} to RGB")
                img = img.convert("RGB")

            # Convert to numpy array
            arr = np.array(img, dtype=np.float32) / 255.0

            h, w = arr.shape[:2]
            size_mb = (h * w * 3 * 4) / (1024 * 1024)  # Float32 size in MB
            logger.debug(f"Loaded {w}×{h} image with PIL ({size_mb:.1f} MB in memory)")

            # Ensure C-contiguous memory layout for optimal performance
            return np.ascontiguousarray(arr)

    def _save_opencv(self, image: np.ndarray[Any, Any], path: Path, quality: int) -> None:
        """Save image using OpenCV for better performance."""
        # Ensure values are in [0, 1]
        image = np.clip(image, 0, 1)

        # Convert to uint8
        img_uint8 = (image * 255).astype(np.uint8)

        # Convert RGB to BGR for OpenCV
        img_bgr = cv2.cvtColor(img_uint8, cv2.COLOR_RGB2BGR)

        # Set compression parameters based on format
        ext = path.suffix.lower()
        if ext in [".jpg", ".jpeg"]:
            params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        elif ext == ".png":
            # PNG compression level (0-9, where 9 is max compression)
            compression = int((100 - quality) / 11)
            params = [cv2.IMWRITE_PNG_COMPRESSION, compression]
        else:
            params = []

        success = cv2.imwrite(str(path), img_bgr, params)

        if not success:
            msg = f"Failed to save image: {path}"
            raise OSError(msg)

        logger.debug(f"Saved image with OpenCV (quality: {quality})")

    def _save_pil(self, image: np.ndarray[Any, Any], path: Path, quality: int) -> None:
        """Save image using PIL as fallback."""
        # Ensure values are in [0, 1]
        image = np.clip(image, 0, 1)

        # Convert to uint8
        img_uint8 = (image * 255).astype(np.uint8)

        # Create PIL Image
        pil_img = Image.fromarray(img_uint8, mode="RGB")

        # Set save parameters based on format
        ext = path.suffix.lower()
        save_kwargs = {}

        if ext in [".jpg", ".jpeg"]:
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True
        elif ext == ".png":
            # PNG compression level
            save_kwargs["compress_level"] = int((100 - quality) / 11)

        pil_img.save(path, **save_kwargs)

        logger.debug(f"Saved image with PIL (quality: {quality})")

    def estimate_memory_usage(self, width: int, height: int) -> int:
        """
        Estimate memory usage for processing an image.

        Returns:
            Estimated memory usage in MB

        """
        # Each pixel: 3 channels × 4 bytes (float32) × 2 (input + output)
        pixels = width * height
        bytes_per_pixel = 3 * 4 * 2

        # Add overhead for intermediate calculations (attractors, etc.)
        overhead_factor = 1.5

        total_bytes = pixels * bytes_per_pixel * overhead_factor
        total_mb = total_bytes / (1024 * 1024)

        return int(total_mb)

    def should_use_tiling(self, width: int, height: int, max_memory_mb: int = 2048) -> bool:
        """
        Determine if image should be processed in tiles.

        Args:
            width: Image width
            height: Image height
            max_memory_mb: Maximum memory to use

        Returns:
            True if tiling should be used

        Used by transform.py to decide on processing strategy.

        Used in:
        - old/imgcolorshine/imgcolorshine/transform.py
        - src/imgcolorshine/transform.py
        """
        estimated_mb = self.estimate_memory_usage(width, height)
        should_tile = estimated_mb > max_memory_mb

        if should_tile:
            logger.info(
                f"Large image ({width}×{height}), using tiled processing "
                f"(estimated {estimated_mb}MB > {max_memory_mb}MB limit)"
            )

        return should_tile
