#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["loguru", "numpy"]
# ///
# this_file: src/imgcolorshine/colorshine.py

"""
Core processing logic for imgcolorshine.

Contains the main image transformation pipeline.
"""

import sys
from pathlib import Path
from typing import Any

import numpy as np
from loguru import logger

from imgcolorshine.engine import ColorTransformer, OKLCHEngine
from imgcolorshine.io import ImageProcessor
from imgcolorshine.lut import LUTManager

# Constants for attractor parsing
ATTRACTOR_PARTS = 3
TOLERANCE_MIN, TOLERANCE_MAX = 0.0, 100.0
STRENGTH_MIN, STRENGTH_MAX = 0.0, 200.0


def setup_logging(*, verbose: bool = False) -> None:
    """Configure loguru logging based on verbosity."""
    logger.remove()
    if verbose:
        logger.add(sys.stderr, level="DEBUG", format="{time:HH:mm:ss} | {level} | {message}")
    else:
        logger.add(sys.stderr, level="INFO", format="{message}")


def parse_attractor(attractor_str: str) -> tuple[str, float, float]:
    """Parse attractor string format: 'color;tolerance;strength'."""
    try:
        parts = attractor_str.split(";")
        if len(parts) != ATTRACTOR_PARTS:
            msg = f"Invalid attractor format: {attractor_str}"
            raise ValueError(msg)

        color = parts[0].strip()
        tolerance = float(parts[1])
        strength = float(parts[2])

        if not TOLERANCE_MIN <= tolerance <= TOLERANCE_MAX:
            msg = f"Tolerance must be {TOLERANCE_MIN}-{TOLERANCE_MAX}, got {tolerance}"
            raise ValueError(msg)
        if not STRENGTH_MIN <= strength <= STRENGTH_MAX:
            msg = f"Strength must be {STRENGTH_MIN}-{STRENGTH_MAX}, got {strength}"
            raise ValueError(msg)

        return color, tolerance, strength
    except Exception as e:
        msg = f"Invalid attractor '{attractor_str}': {e}"
        raise ValueError(msg) from e


def generate_output_path(input_path: Path) -> Path:
    """Generate output filename if not provided."""
    stem = input_path.stem
    suffix = input_path.suffix
    return input_path.parent / f"{stem}_colorshine{suffix}"


def process_image(
    input_image: str,
    attractors: tuple[str, ...],
    output_image: str | None = None,
    *,
    luminance: bool = True,
    saturation: bool = True,
    hue: bool = True,
    verbose: bool = False,
    **kwargs: Any,
) -> None:
    """
    Process an image with color attractors.

    Main processing pipeline that handles logging setup, attractor parsing,
    image loading, transformation, and saving.

    Args:
        input_image: Path to input image
        attractors: Color attractors in format "color;tolerance;strength"
        output_image: Output path (auto-generated if None)
        luminance: Enable lightness transformation (L in OKLCH)
        saturation: Enable saturation transformation (C in OKLCH)
        hue: Enable hue transformation (H in OKLCH)
        verbose: Enable verbose logging
        **kwargs: Additional keyword arguments (tile_size, gpu, lut_size, etc.)

    Used in:
    - src/imgcolorshine/cli.py
    """
    setup_logging(verbose=verbose)

    # Convert to Path
    input_path = Path(input_image)

    # Validate inputs
    if not attractors:
        msg = "At least one attractor must be provided"
        raise ValueError(msg)

    if not any([luminance, saturation, hue]):
        msg = "At least one channel (luminance, saturation, hue) must be enabled"
        raise ValueError(msg)

    # Parse attractors
    logger.debug(f"Parsing {len(attractors)} attractors")
    parsed_attractors = []
    for attr_str in attractors:
        color, tolerance, strength = parse_attractor(attr_str)
        parsed_attractors.append((color, tolerance, strength))
        logger.debug(f"Attractor: color={color}, tolerance={tolerance}, strength={strength}")

    # Set output path
    if output_image is None:
        output_path = generate_output_path(input_path)
        logger.info(f"Output path auto-generated: {output_path}")
    else:
        output_path = Path(output_image)

    # Initialize components
    engine = OKLCHEngine()
    processor = ImageProcessor(tile_size=kwargs.get("tile_size", 1024))
    transformer = ColorTransformer(
        engine, use_fused_kernel=kwargs.get("fused_kernel", False), use_gpu=kwargs.get("gpu", True)
    )

    # Create attractor objects
    attractor_objects = []
    for color_str, tolerance, strength in parsed_attractors:
        attractor = engine.create_attractor(color_str, tolerance, strength)
        attractor_objects.append(attractor)
        logger.info(f"Created attractor: {color_str} (tolerance={tolerance}, strength={strength})")

    # Load image
    logger.info(f"Loading image: {input_path}")
    image: np.ndarray[Any, Any] = processor.load_image(input_path)

    # --- Force standard transformer path for new percentile logic ---
    # The new percentile-based tolerance model requires a two-pass analysis
    # of the entire image, which is incompatible with the tile-based LUT,
    # GPU, and fused kernel optimizations. We prioritize correctness here.

    # Check if LUT acceleration is requested
    lut_size = kwargs.get("lut_size", 0)
    if lut_size > 0:
        logger.info(f"Using 3D LUT acceleration (size={lut_size})")
        lut_manager = LUTManager(lut_size=lut_size)

        # Get or build LUT
        flags = {"luminance": luminance, "saturation": saturation, "hue": hue}
        lut, interpolator = lut_manager.get_lut(transformer, attractor_objects, flags)

        # Apply LUT
        image_normalized = image / 255.0
        transformed_normalized = lut_manager.apply_lut(image_normalized, interpolator)
        transformed = (transformed_normalized * 255.0).astype(np.uint8)
    else:
        logger.info("Using percentile-based tolerance model.")
        transformed = transformer.transform_image(
            image,
            attractor_objects,
            {"luminance": luminance, "saturation": saturation, "hue": hue},
        )

    # Save the final image
    logger.info("Saving transformed image...")
    processor.save_image(transformed, output_path)
    logger.info(f"Successfully saved to {output_path}")
