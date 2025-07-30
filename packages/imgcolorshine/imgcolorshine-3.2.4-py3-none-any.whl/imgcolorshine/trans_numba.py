#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["numpy", "numba"]
# ///
# this_file: src/imgcolorshine/trans_numba.py

"""
Numba-optimized color space transformations for high performance.

This is the **single authoritative implementation** used by imgcolorshine.
It provides fully-vectorised sRGB ↔ Oklab ↔ OKLCH conversions, gamut
mapping and batch helpers.  All functions are JIT-compiled with Numba for
speed and are float32-centric to minimise memory traffic.
"""

from __future__ import annotations

from typing import Any

import numba
import numpy as np

# ---------------------------------------------------------------------------
# Colour-space matrices (CSS Color Module 4 reference values)
# ---------------------------------------------------------------------------

_LINEAR_RGB_TO_XYZ = np.array(
    [
        [0.4123907992659595, 0.3575843393838780, 0.1804807884018343],
        [0.2126390058715104, 0.7151686787677559, 0.0721923153607337],
        [0.0193308187155918, 0.1191947797946259, 0.9505321522496608],
    ],
    dtype=np.float32,
)

_XYZ_TO_LINEAR_RGB = np.array(
    [
        [3.2409699419045213, -1.5373831775700935, -0.4986107602930033],
        [-0.9692436362808798, 1.8759675015077206, 0.0415550574071756],
        [0.0556300796969936, -0.2039769588889765, 1.0569715142428784],
    ],
    dtype=np.float32,
)

_XYZ_TO_LMS = np.array(
    [
        [0.8189330101, 0.3618667424, -0.1288597137],
        [0.0329845436, 0.9293118715, 0.0361456387],
        [0.0482003018, 0.2643662691, 0.6338517070],
    ],
    dtype=np.float32,
)

_LMS_TO_XYZ = np.array(
    [
        [1.2270138511035211, -0.5577999806518222, 0.2812561489664678],
        [-0.0405801784232806, 1.1122568696168302, -0.0716766786656012],
        [-0.0763812845057069, -0.4214819784180127, 1.5861632204407947],
    ],
    dtype=np.float32,
)

_LMS_TO_OKLAB = np.array(
    [
        [0.2104542553, 0.7936177850, -0.0040720468],
        [1.9779984951, -2.4285922050, 0.4505937099],
        [0.0259040371, 0.7827717662, -0.8086757660],
    ],
    dtype=np.float32,
)

_OKLAB_TO_LMS = np.array(
    [
        [1.0000000000, 0.3963377774, 0.2158037573],
        [1.0000000000, -0.1055613458, -0.0638541728],
        [1.0000000000, -0.0894841775, -1.2914855480],
    ],
    dtype=np.float32,
)

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


@numba.njit(cache=True)
def _srgb_to_linear_component(c: float) -> float:
    """Inverse gamma for a single sRGB component."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


@numba.njit(cache=True)
def _linear_to_srgb_component(c: float) -> float:
    """Gamma-correct a single linear-RGB component."""
    if c <= 0.0031308:
        return c * 12.92
    return 1.055 * (c ** (1.0 / 2.4)) - 0.055


@numba.njit(cache=True)
def srgb_to_linear(srgb: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    """Vectorised inverse gamma for 3-component array."""
    return np.where(
        srgb <= 0.04045,
        srgb / 12.92,
        ((srgb + 0.055) / 1.055) ** 2.4,
    )


@numba.njit(cache=True)
def linear_to_srgb(linear: np.ndarray) -> np.ndarray:
    """Vectorised gamma correction for 3-component array."""
    out = np.empty_like(linear)
    for i in range(3):
        out[i] = _linear_to_srgb_component(linear[i])
    return out


@numba.njit(cache=True)
def _matmul_3x3(mat: np.ndarray, vec: np.ndarray) -> np.ndarray:
    """3×3 matrix × vector (we unroll for Numba speed)."""
    res = np.zeros(3, dtype=np.float32)
    for i in range(3):
        res[i] = mat[i, 0] * vec[0] + mat[i, 1] * vec[1] + mat[i, 2] * vec[2]
    return res


# ---------------------------------------------------------------------------
# Pixel-wise conversions
# ---------------------------------------------------------------------------


@numba.njit(cache=True)
def srgb_to_oklab_single(rgb: np.ndarray) -> np.ndarray:
    linear = srgb_to_linear(rgb)
    xyz = _matmul_3x3(_LINEAR_RGB_TO_XYZ, linear)
    lms = _matmul_3x3(_XYZ_TO_LMS, xyz)
    lms_cbrt = np.empty_like(lms)
    for i in range(3):
        lms_cbrt[i] = np.cbrt(lms[i])
    return _matmul_3x3(_LMS_TO_OKLAB, lms_cbrt)


@numba.njit(cache=True)
def oklab_to_srgb_single(oklab: np.ndarray) -> np.ndarray:
    lms_cbrt = _matmul_3x3(_OKLAB_TO_LMS, oklab)
    lms = np.empty_like(lms_cbrt)
    for i in range(3):
        lms[i] = lms_cbrt[i] ** 3
    xyz = _matmul_3x3(_LMS_TO_XYZ, lms)
    linear = _matmul_3x3(_XYZ_TO_LINEAR_RGB, xyz)
    return linear_to_srgb(linear)


# ---------------------------------------------------------------------------
# Batch conversions (parallel)
# ---------------------------------------------------------------------------


@numba.njit(parallel=True, cache=True)
def batch_srgb_to_oklab(rgb_image: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    h, w = rgb_image.shape[:2]
    out = np.empty_like(rgb_image, dtype=np.float32)
    for y in numba.prange(h):
        for x in range(w):
            out[y, x] = srgb_to_oklab_single(rgb_image[y, x])
    return out


@numba.njit(parallel=True, cache=True)
def batch_oklab_to_srgb(oklab_image: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    h, w = oklab_image.shape[:2]
    out = np.empty_like(oklab_image, dtype=np.float32)
    for y in numba.prange(h):
        for x in range(w):
            out[y, x] = oklab_to_srgb_single(oklab_image[y, x])
    return out


@numba.njit(cache=True)
def oklab_to_oklch_single(oklab: np.ndarray) -> np.ndarray:
    L, a, b = oklab
    C = np.sqrt(a * a + b * b)
    H = np.degrees(np.arctan2(b, a))
    if H < 0:
        H += 360.0
    return np.array([L, C, H], dtype=oklab.dtype)


@numba.njit(cache=True)
def oklch_to_oklab_single(oklch: np.ndarray) -> np.ndarray:
    L, C, H = oklch
    h_rad = np.radians(H)
    a = C * np.cos(h_rad)
    b = C * np.sin(h_rad)
    return np.array([L, a, b], dtype=oklch.dtype)


@numba.njit(parallel=True, cache=True)
def batch_oklab_to_oklch(oklab_image: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    h, w = oklab_image.shape[:2]
    out = np.empty_like(oklab_image, dtype=np.float32)
    for y in numba.prange(h):
        for x in range(w):
            out[y, x] = oklab_to_oklch_single(oklab_image[y, x])
    return out


@numba.njit(parallel=True, cache=True)
def batch_oklch_to_oklab(oklch_image: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    h, w = oklch_image.shape[:2]
    out = np.empty_like(oklch_image, dtype=np.float32)
    for y in numba.prange(h):
        for x in range(w):
            out[y, x] = oklch_to_oklab_single(oklch_image[y, x])
    return out


# ---------------------------------------------------------------------------
# Gamut mapping (binary-search on chroma)
# ---------------------------------------------------------------------------


@numba.njit(cache=True)
def _in_gamut(r_lin: float, g_lin: float, b_lin: float) -> bool:
    return bool((0 <= r_lin <= 1) and (0 <= g_lin <= 1) and (0 <= b_lin <= 1))


@numba.njit(cache=True)
def gamut_map_oklch_single(oklch: np.ndarray, eps: float = 1e-4) -> np.ndarray:
    L, C, H = oklch
    oklab = oklch_to_oklab_single(oklch)
    rgb = oklab_to_srgb_single(oklab)
    if _in_gamut(rgb[0], rgb[1], rgb[2]):
        return oklch
    c_lo, c_hi = 0.0, C
    while c_hi - c_lo > eps:
        c_mid = 0.5 * (c_lo + c_hi)
        test_oklch = np.array([L, c_mid, H], dtype=np.float32)
        test_rgb = oklab_to_srgb_single(oklch_to_oklab_single(test_oklch))
        if _in_gamut(test_rgb[0], test_rgb[1], test_rgb[2]):
            c_lo = c_mid
        else:
            c_hi = c_mid
    return np.array([L, c_lo, H], dtype=np.float32)


@numba.njit(parallel=True, cache=True)
def batch_gamut_map_oklch(oklch_image: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    h, w = oklch_image.shape[:2]
    out = np.empty_like(oklch_image, dtype=np.float32)
    for y in numba.prange(h):
        for x in range(w):
            out[y, x] = gamut_map_oklch_single(oklch_image[y, x])
    return out
