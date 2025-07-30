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

import numpy as np
from loguru import logger

from imgcolorshine.color import OKLCHEngine
from imgcolorshine.io import ImageProcessor
from imgcolorshine.transform import ColorTransformer


def setup_logging(verbose: bool = False):
    """Configure loguru logging based on verbosity."""
    logger.remove()
    if verbose:
        logger.add(
            sys.stderr, level="DEBUG", format="{time:HH:mm:ss} | {level} | {message}"
        )
    else:
        logger.add(sys.stderr, level="INFO", format="{message}")


def parse_attractor(attractor_str: str) -> tuple[str, float, float]:
    """Parse attractor string format: 'color;tolerance;strength'."""
    try:
        parts = attractor_str.split(";")
        if len(parts) != 3:
            msg = f"Invalid attractor format: {attractor_str}"
            raise ValueError(msg)

        color = parts[0].strip()
        tolerance = float(parts[1])
        strength = float(parts[2])

        if not 0 <= tolerance <= 100:
            msg = f"Tolerance must be 0-100, got {tolerance}"
            raise ValueError(msg)
        if not 0 <= strength <= 100:
            msg = f"Strength must be 0-100, got {strength}"
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
    luminance: bool = True,
    saturation: bool = True,
    chroma: bool = True,
    verbose: bool = False,
    tile_size: int = 1024,
    gpu: bool = True,
    lut_size: int = 0,
    fast_hierar: bool = False,
    fast_spatial: bool = True,
) -> None:
    """
    Process an image with color attractors.

    Main processing pipeline that handles logging setup, attractor parsing,
    image loading, transformation, and saving.

    Args:
        input_image: Path to input image
        attractors: Color attractors in format "color;tolerance;strength"
        output_image: Output path (auto-generated if None)
        luminance: Enable lightness transformation
        saturation: Enable chroma transformation
        chroma: Enable chroma transformation
        verbose: Enable verbose logging
        tile_size: Tile size for large image processing
        gpu: Use GPU acceleration if available
        lut_size: Size of 3D LUT (0=disabled)
        fast_hierar: Enable fast_hierar multi-resolution processing
        fast_spatial: Enable spatial acceleration

    Used in:
    - src/imgcolorshine/cli.py
    """
    setup_logging(verbose)

    # Convert to Path
    input_path = Path(input_image)

    # Validate inputs
    if not attractors:
        msg = "At least one attractor must be provided"
        raise ValueError(msg)

    if not any([luminance, saturation, chroma]):
        msg = "At least one channel (luminance, saturation, chroma) must be enabled"
        raise ValueError(msg)

    # Parse attractors
    logger.debug(f"Parsing {len(attractors)} attractors")
    parsed_attractors = []
    for attr_str in attractors:
        color, tolerance, strength = parse_attractor(attr_str)
        parsed_attractors.append((color, tolerance, strength))
        logger.debug(
            f"Attractor: color={color}, tolerance={tolerance}, strength={strength}"
        )

    # Set output path
    if output_image is None:
        output_path = generate_output_path(input_path)
        logger.info(f"Output path auto-generated: {output_path}")
    else:
        output_path = Path(output_image)

    # Initialize components
    engine = OKLCHEngine()
    processor = ImageProcessor(tile_size=tile_size)
    transformer = ColorTransformer(engine)

    # Create attractor objects
    attractor_objects = []
    for color_str, tolerance, strength in parsed_attractors:
        attractor = engine.create_attractor(color_str, tolerance, strength)
        attractor_objects.append(attractor)
        logger.info(
            f"Created attractor: {color_str} (tolerance={tolerance}, strength={strength})"
        )

    # Load image
    logger.info(f"Loading image: {input_path}")
    image = processor.load_image(input_path)

    # Try LUT transformation first if enabled
    transformed = None
    if lut_size > 0:
        try:
            logger.info(f"Building {lut_size}³ color LUT...")
            import numpy as np
            from imgcolorshine.kernel import transform_pixel_fused
            from imgcolorshine.lut import ColorLUT

            # Create LUT
            lut = ColorLUT(size=lut_size if lut_size > 0 else 65)

            # Prepare attractor data
            attractors_lab = np.array([a.oklab_values for a in attractor_objects])
            tolerances = np.array([a.tolerance for a in attractor_objects])
            strengths = np.array([a.strength for a in attractor_objects])
            channels = [luminance, saturation, chroma]

            # Build LUT using fused kernel
            def transform_func(rgb, attr_lab, tol, str_vals, l, s, h):
                return np.array(
                    transform_pixel_fused(
                        rgb[0], rgb[1], rgb[2], attr_lab, tol, str_vals, l, s, h
                    )
                )

            lut.build_lut(
                transform_func, attractors_lab, tolerances, strengths, channels
            )

            # Apply LUT
            logger.info("Applying LUT transformation...")
            transformed = lut.apply_lut(image)
            logger.info("LUT processing successful")

        except Exception as e:
            logger.warning(
                f"LUT processing failed: {e}, falling back to standard processing"
            )
            transformed = None

    # Try GPU transformation if LUT failed or disabled
    if transformed is None and gpu:
        try:
            from imgcolorshine.gpu import GPU_AVAILABLE

            if GPU_AVAILABLE:
                logger.info("Attempting GPU acceleration...")
                import numpy as np
                from imgcolorshine.trans_gpu import process_image_gpu

                # Prepare attractor data
                attractors_lab = np.array([a.oklab_values for a in attractor_objects])
                tolerances = np.array([a.tolerance for a in attractor_objects])
                strengths = np.array([a.strength for a in attractor_objects])

                # Process on GPU
                transformed = process_image_gpu(
                    image,
                    attractors_lab,
                    tolerances,
                    strengths,
                    luminance,
                    saturation,
                    chroma,
                )

                if transformed is not None:
                    logger.info("GPU processing successful")
                else:
                    logger.warning("GPU processing failed, falling back to CPU")
                    gpu = False
            else:
                logger.debug("GPU not available, using CPU")
                gpu = False
        except ImportError:
            logger.debug("GPU libraries not installed, using CPU")
            gpu = False

    # CPU processing (fallback or if GPU disabled)
    if not gpu or transformed is None:
        # Check if we should use optimizations
        if fast_hierar or fast_spatial:
            logger.info("Using optimized CPU processing...")
            transformed = process_with_optimizations(
                image,
                attractor_objects,
                luminance,
                saturation,
                chroma,
                fast_hierar,
                fast_spatial,
                transformer,
                engine,
            )
        else:
            logger.info("Transforming colors on CPU...")
            flags = {"luminance": luminance, "saturation": saturation, "chroma": chroma}
            transformed = transformer.transform_image(image, attractor_objects, flags)

    # Save image
    logger.info(f"Saving image: {output_path}")
    processor.save_image(transformed, output_path)

    logger.info(f"Processing complete: {input_path} → {output_path}")


def process_with_optimizations(
    image: np.ndarray,
    attractor_objects: list,
    luminance: bool,
    saturation: bool,
    hue: bool,
    hierarchical: bool,
    spatial_accel: bool,
    transformer: "ColorTransformer",
    engine: "OKLCHEngine",
) -> np.ndarray:
    """
    Process image with fast_hierar and/or spatial optimizations.

    Combines both optimizations when both are enabled for maximum performance.
    """
    import numpy as np

    # Prepare attractor data
    attractors_lab = np.array([a.oklab_values for a in attractor_objects])
    tolerances = np.array([a.tolerance for a in attractor_objects])
    strengths = np.array([a.strength for a in attractor_objects])
    channels = [luminance, saturation, hue]

    # Import optimization modules
    if hierarchical:
        from imgcolorshine.hierar import HierarchicalProcessor
    if spatial_accel:
        from imgcolorshine.spatial import SpatialAccelerator

    # Combined optimization path
    if hierarchical and spatial_accel:
        logger.info("Using combined fast_hierar + spatial acceleration")

        # Initialize processors
        hier_processor = HierarchicalProcessor()
        spatial_acc = SpatialAccelerator()

        # Build spatial index once
        spatial_acc.build_spatial_index(attractors_lab, tolerances)

        # Create a transform function that uses spatial acceleration
        def spatial_transform_func(img, *args):
            # Convert to Oklab for spatial queries
            # Convert to Oklab for spatial queries
            img_oklab = engine.batch_rgb_to_oklab(img / 255.0)

            # Create transform function wrapper
            attractors_lch = np.array([a.oklch_values for a in attractor_objects])
            flags_array = np.array(channels)

            def transform_wrapper(img_rgb, *args):
                return (
                    transformer._transform_tile(
                        img_rgb / 255.0,
                        attractors_lab,
                        attractors_lch,
                        tolerances,
                        strengths,
                        flags_array,
                    )
                    * 255.0
                )

            # Use spatial acceleration
            return spatial_acc.transform_with_spatial_accel(
                img,
                img_oklab,
                attractors_lab,
                tolerances,
                strengths,
                transform_wrapper,
                channels,
            )

        # Process hierarchically with spatial optimization
        transformed = hier_processor.process_hierarchical(
            image,
            spatial_transform_func,
            attractors_lab,
            tolerances,
            strengths,
            channels,
        )

    elif hierarchical:
        logger.info("Using fast_hierar processing")

        hier_processor = HierarchicalProcessor()

        # Create a wrapper for the transform function
        def transform_func(img_rgb, *args):
            # Prepare attractor data in OKLCH format too
            attractors_lch = np.array([a.oklch_values for a in attractor_objects])
            flags_array = np.array(channels)

            # Use the transformer's tile transform method
            return (
                transformer._transform_tile(
                    img_rgb / 255.0,  # Normalize to 0-1
                    attractors_lab,
                    attractors_lch,
                    tolerances,
                    strengths,
                    flags_array,
                )
                * 255.0
            )  # Convert back to 0-255

        transformed = hier_processor.process_hierarchical(
            image, transform_func, attractors_lab, tolerances, strengths, channels
        )

    elif spatial_accel:
        logger.info("Using spatial acceleration")

        # Convert image to Oklab for spatial queries
        image_oklab = engine.batch_rgb_to_oklab(image / 255.0)

        spatial_acc = SpatialAccelerator()

        # Create transform function wrapper
        attractors_lch = np.array([a.oklch_values for a in attractor_objects])
        flags_array = np.array(channels)

        def transform_func(img_rgb, *args):
            return (
                transformer._transform_tile(
                    img_rgb / 255.0,
                    attractors_lab,
                    attractors_lch,
                    tolerances,
                    strengths,
                    flags_array,
                )
                * 255.0
            )

        transformed = spatial_acc.transform_with_spatial_accel(
            image,
            image_oklab,
            attractors_lab,
            tolerances,
            strengths,
            transform_func,
            channels,
        )
    else:
        # Should not reach here, but fallback to standard processing
        flags = {"luminance": luminance, "saturation": saturation, "chroma": hue}
        transformed = transformer.transform_image(image, attractor_objects, flags)

    return transformed
