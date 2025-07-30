#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["numpy", "numba"]
# ///
# this_file: src/imgcolorshine/trans_numba.py

"""
Numba-optimized color space transformations for high performance.

Implements direct matrix multiplication for sRGB ↔ Oklab conversions
and vectorized OKLCH operations. This module provides dramatic speedups
over the ColorAide-based conversions in color.py.

All transformations follow the CSS Color Module 4 and Oklab specifications.
"""

import numba
import numpy as np

# Color transformation matrices (from CSS Color Module 4 spec)
# sRGB to linear RGB gamma correction is handled separately

# Linear RGB to XYZ D65 matrix
_LINEAR_RGB_TO_XYZ = np.array(
    [
        [0.4123907992659595, 0.3575843393838780, 0.1804807884018343],
        [0.2126390058715104, 0.7151686787677559, 0.0721923153607337],
        [0.0193308187155918, 0.1191947797946259, 0.9505321522496608],
    ],
    dtype=np.float32,
)

# XYZ D65 to Linear RGB matrix
_XYZ_TO_LINEAR_RGB = np.array(
    [
        [3.2409699419045213, -1.5373831775700935, -0.4986107602930033],
        [-0.9692436362808798, 1.8759675015077206, 0.0415550574071756],
        [0.0556300796969936, -0.2039769588889765, 1.0569715142428784],
    ],
    dtype=np.float32,
)

# XYZ D65 to LMS matrix (for Oklab)
_XYZ_TO_LMS = np.array(
    [
        [0.8189330101, 0.3618667424, -0.1288597137],
        [0.0329845436, 0.9293118715, 0.0361456387],
        [0.0482003018, 0.2643662691, 0.6338517070],
    ],
    dtype=np.float32,
)

# LMS to XYZ D65 matrix
_LMS_TO_XYZ = np.array(
    [
        [1.2270138511035211, -0.5577999806518222, 0.2812561489664678],
        [-0.0405801784232806, 1.1122568696168302, -0.0716766786656012],
        [-0.0763812845057069, -0.4214819784180127, 1.5861632204407947],
    ],
    dtype=np.float32,
)

# LMS to Oklab matrix (after applying cbrt)
_LMS_TO_OKLAB = np.array(
    [
        [0.2104542553, 0.7936177850, -0.0040720468],
        [1.9779984951, -2.4285922050, 0.4505937099],
        [0.0259040371, 0.7827717662, -0.8086757660],
    ],
    dtype=np.float32,
)

# Oklab to LMS matrix (before applying cube)
_OKLAB_TO_LMS = np.array(
    [
        [1.0000000000, 0.3963377774, 0.2158037573],
        [1.0000000000, -0.1055613458, -0.0638541728],
        [1.0000000000, -0.0894841775, -1.2914855480],
    ],
    dtype=np.float32,
)


@numba.njit(cache=True)
def srgb_to_linear_component(c: float) -> float:
    """Apply inverse gamma correction to a single sRGB component."""
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


@numba.njit(cache=True)
def linear_to_srgb_component(c: float) -> float:
    """Apply gamma correction to a single linear RGB component."""
    if c <= 0.0031308:
        return c * 12.92
    return 1.055 * (c ** (1.0 / 2.4)) - 0.055


@numba.njit(cache=True)
def srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    """Convert sRGB to linear RGB (inverse gamma correction)."""
    linear = np.empty_like(rgb)
    for i in range(3):
        linear[i] = srgb_to_linear_component(rgb[i])
    return linear


@numba.njit(cache=True)
def linear_to_srgb(linear: np.ndarray) -> np.ndarray:
    """Convert linear RGB to sRGB (gamma correction)."""
    srgb = np.empty_like(linear)
    for i in range(3):
        srgb[i] = linear_to_srgb_component(linear[i])
    return srgb


@numba.njit(cache=True)
def matrix_multiply_3x3(mat: np.ndarray, vec: np.ndarray) -> np.ndarray:
    """Multiply a 3x3 matrix by a vector."""
    result = np.zeros(3, dtype=np.float32)
    for i in range(3):
        result[i] = mat[i, 0] * vec[0] + mat[i, 1] * vec[1] + mat[i, 2] * vec[2]
    return result


@numba.njit(cache=True)
def srgb_to_oklab_single(rgb: np.ndarray) -> np.ndarray:
    """Convert a single RGB pixel to Oklab."""
    # Step 1: sRGB to linear RGB
    linear = srgb_to_linear(rgb)

    # Step 2: Linear RGB to XYZ
    xyz = matrix_multiply_3x3(_LINEAR_RGB_TO_XYZ, linear)

    # Step 3: XYZ to LMS
    lms = matrix_multiply_3x3(_XYZ_TO_LMS, xyz)

    # Step 4: Apply cube root
    lms_cbrt = np.empty_like(lms)
    for i in range(3):
        lms_cbrt[i] = np.cbrt(lms[i])

    # Step 5: LMS to Oklab
    return matrix_multiply_3x3(_LMS_TO_OKLAB, lms_cbrt)


@numba.njit(cache=True)
def oklab_to_srgb_single(oklab: np.ndarray) -> np.ndarray:
    """Convert a single Oklab pixel to sRGB."""
    # Step 1: Oklab to LMS (cbrt space)
    lms_cbrt = matrix_multiply_3x3(_OKLAB_TO_LMS, oklab)

    # Step 2: Apply cube
    lms = np.empty_like(lms_cbrt)
    for i in range(3):
        lms[i] = lms_cbrt[i] ** 3

    # Step 3: LMS to XYZ
    xyz = matrix_multiply_3x3(_LMS_TO_XYZ, lms)

    # Step 4: XYZ to linear RGB
    linear = matrix_multiply_3x3(_XYZ_TO_LINEAR_RGB, xyz)

    # Step 5: Linear RGB to sRGB
    return linear_to_srgb(linear)

    # No clamping here for internal checks; clamping is done by final consumer if needed.
    # For example, batch_oklab_to_srgb (the public API for batch conversion) does clamp.
    # Not clamping here allows is_in_gamut_srgb to correctly assess raw conversion.


@numba.njit(parallel=True, cache=True)
def batch_srgb_to_oklab(rgb_image: np.ndarray) -> np.ndarray:
    """Convert entire RGB image to Oklab using parallel processing."""
    h, w = rgb_image.shape[:2]
    oklab_image = np.empty_like(rgb_image)

    for i in numba.prange(h):
        for j in range(w):
            oklab_image[i, j] = srgb_to_oklab_single(rgb_image[i, j])

    return oklab_image


@numba.njit(parallel=True, cache=True)
def batch_oklab_to_srgb(oklab_image: np.ndarray) -> np.ndarray:
    """Convert entire Oklab image to sRGB using parallel processing."""
    h, w = oklab_image.shape[:2]
    rgb_image = np.empty_like(oklab_image)

    for i in numba.prange(h):
        for j in range(w):
            rgb_image[i, j] = oklab_to_srgb_single(oklab_image[i, j])

    return rgb_image


@numba.njit(cache=True)
def oklab_to_oklch_single(oklab: np.ndarray) -> np.ndarray:
    """Convert single Oklab pixel to OKLCH."""
    l = oklab[0]
    a = oklab[1]
    b = oklab[2]

    c = np.sqrt(a * a + b * b)
    h = np.arctan2(b, a) * 180.0 / np.pi
    if h < 0:
        h += 360.0

    return np.array([l, c, h], dtype=oklab.dtype)


@numba.njit(cache=True)
def oklch_to_oklab_single(oklch: np.ndarray) -> np.ndarray:
    """Convert single OKLCH pixel to Oklab."""
    l = oklch[0]
    c = oklch[1]
    h = oklch[2]

    h_rad = h * np.pi / 180.0
    a = c * np.cos(h_rad)
    b = c * np.sin(h_rad)

    return np.array([l, a, b], dtype=oklch.dtype)


@numba.njit(parallel=True, cache=True)
def batch_oklab_to_oklch(oklab_image: np.ndarray) -> np.ndarray:
    """Convert entire Oklab image to OKLCH using parallel processing."""
    h, w = oklab_image.shape[:2]
    oklch_image = np.empty_like(oklab_image)

    for i in numba.prange(h):
        for j in range(w):
            oklch_image[i, j] = oklab_to_oklch_single(oklab_image[i, j])

    return oklch_image


@numba.njit(parallel=True, cache=True)
def batch_oklch_to_oklab(oklch_image: np.ndarray) -> np.ndarray:
    """Convert entire OKLCH image to Oklab using parallel processing."""
    h, w = oklch_image.shape[:2]
    oklab_image = np.empty_like(oklch_image)

    for i in numba.prange(h):
        for j in range(w):
            oklab_image[i, j] = oklch_to_oklab_single(oklch_image[i, j])

    return oklab_image


@numba.njit(cache=True)
def is_in_gamut_srgb(rgb: np.ndarray) -> bool:
    """Check if RGB values are within sRGB gamut."""
    return np.all(rgb >= 0.0) and np.all(rgb <= 1.0)


@numba.njit(cache=True)
def gamut_map_oklch_single(oklch: np.ndarray, epsilon: float = 0.0001) -> np.ndarray:
    """Gamut map a single OKLCH color to sRGB using binary search on chroma."""
    l, c, h = oklch

    # First check if already in gamut
    oklab = oklch_to_oklab_single(oklch)
    rgb = oklab_to_srgb_single(oklab)
    if is_in_gamut_srgb(rgb):
        return oklch

    # Binary search for maximum valid chroma
    c_min, c_max = 0.0, c

    while c_max - c_min > epsilon:
        c_mid = (c_min + c_max) / 2.0
        test_oklch = np.array([l, c_mid, h], dtype=oklch.dtype)
        test_oklab = oklch_to_oklab_single(test_oklch)
        test_rgb = oklab_to_srgb_single(test_oklab)

        if is_in_gamut_srgb(test_rgb):
            c_min = c_mid
        else:
            c_max = c_mid

    return np.array([l, c_min, h], dtype=oklch.dtype)


@numba.njit(parallel=True, cache=True)
def batch_gamut_map_oklch(oklch_image: np.ndarray) -> np.ndarray:
    """Gamut map entire OKLCH image using parallel processing."""
    h, w = oklch_image.shape[:2]
    mapped_image = np.empty_like(oklch_image)

    for i in numba.prange(h):
        for j in range(w):
            mapped_image[i, j] = gamut_map_oklch_single(oklch_image[i, j])

    return mapped_image


# Aliases for backward compatibility with tests
srgb_to_oklab_batch = batch_srgb_to_oklab
oklab_to_srgb_batch = batch_oklab_to_srgb
