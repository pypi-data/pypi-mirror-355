#!/usr/bin/env -S uv run -s
# /// script
# dependencies = []
# ///
# this_file: src/imgcolorshine/__init__.py

"""
imgcolorshine - Transform image colors using OKLCH color attractors.

A physics-inspired tool that operates in perceptually uniform color space,
allowing intuitive color transformations based on attraction principles.
"""

from imgcolorshine.color import Attractor, OKLCHEngine
from imgcolorshine.falloff import FalloffType, get_falloff_function
from imgcolorshine.gamut import GamutMapper
from imgcolorshine.io import ImageProcessor
from imgcolorshine.transform import ColorTransformer
from imgcolorshine.utils import batch_process_images, validate_image

__version__ = "0.1.0"
__all__ = [
    "Attractor",
    "ColorTransformer",
    "FalloffType",
    "GamutMapper",
    "ImageProcessor",
    "OKLCHEngine",
    "batch_process_images",
    "get_falloff_function",
    "validate_image",
]
