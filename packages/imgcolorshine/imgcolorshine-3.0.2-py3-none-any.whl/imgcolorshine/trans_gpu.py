#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["numpy", "loguru"]
# ///
# this_file: src/imgcolorshine/trans_gpu.py

"""
GPU-accelerated color transformations using CuPy.

Provides GPU versions of all color space conversions and transformations
with automatic memory management and optimized kernels.
"""

import numpy as np
from imgcolorshine.gpu import (
    check_gpu_memory_available,
    estimate_gpu_memory_required,
    get_array_module,
)
from loguru import logger

# Try to import CuPy
try:
    import cupy as cp

    CUPY_AVAILABLE = cp.cuda.is_available()
except:
    CUPY_AVAILABLE = False
    cp = None


def get_gpu_color_matrices(xp):
    """Get color transformation matrices for the given array module."""
    # Linear RGB to XYZ D65 matrix
    LINEAR_RGB_TO_XYZ = xp.array(
        [
            [0.4123907992659595, 0.3575843393838780, 0.1804807884018343],
            [0.2126390058715104, 0.7151686787677559, 0.0721923153607337],
            [0.0193308187155918, 0.1191947797946259, 0.9505321522496608],
        ],
        dtype=xp.float32,
    )

    # XYZ D65 to Linear RGB matrix
    XYZ_TO_LINEAR_RGB = xp.array(
        [
            [3.2409699419045213, -1.5373831775700935, -0.4986107602930033],
            [-0.9692436362808798, 1.8759675015077206, 0.0415550574071756],
            [0.0556300796969936, -0.2039769588889765, 1.0569715142428784],
        ],
        dtype=xp.float32,
    )

    # XYZ D65 to LMS matrix
    XYZ_TO_LMS = xp.array(
        [
            [0.8189330101, 0.3618667424, -0.1288597137],
            [0.0329845436, 0.9293118715, 0.0361456387],
            [0.0482003018, 0.2643662691, 0.6338517070],
        ],
        dtype=xp.float32,
    )

    # LMS to XYZ D65 matrix
    LMS_TO_XYZ = xp.array(
        [
            [1.2270138511035211, -0.5577999806518222, 0.2812561489664678],
            [-0.0405801784232806, 1.1122568696168302, -0.0716766786656012],
            [-0.0763812845057069, -0.4214819784180127, 1.5861632204407947],
        ],
        dtype=xp.float32,
    )

    # LMS to Oklab matrix
    LMS_TO_OKLAB = xp.array(
        [
            [0.2104542553, 0.7936177850, -0.0040720468],
            [1.9779984951, -2.4285922050, 0.4505937099],
            [0.0259040371, 0.7827717662, -0.8086757660],
        ],
        dtype=xp.float32,
    )

    # Oklab to LMS matrix
    OKLAB_TO_LMS = xp.array(
        [
            [1.0000000000, 0.3963377774, 0.2158037573],
            [1.0000000000, -0.1055613458, -0.0638541728],
            [1.0000000000, -0.0894841775, -1.2914855480],
        ],
        dtype=xp.float32,
    )

    return {
        "LINEAR_RGB_TO_XYZ": LINEAR_RGB_TO_XYZ,
        "XYZ_TO_LINEAR_RGB": XYZ_TO_LINEAR_RGB,
        "XYZ_TO_LMS": XYZ_TO_LMS,
        "LMS_TO_XYZ": LMS_TO_XYZ,
        "LMS_TO_OKLAB": LMS_TO_OKLAB,
        "OKLAB_TO_LMS": OKLAB_TO_LMS,
    }


def srgb_to_linear_gpu(srgb, xp):
    """GPU version of sRGB to linear conversion."""
    return xp.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)


def linear_to_srgb_gpu(linear, xp):
    """GPU version of linear to sRGB conversion."""
    return xp.where(
        linear <= 0.0031308, linear * 12.92, 1.055 * (linear ** (1.0 / 2.4)) - 0.055
    )


def batch_srgb_to_oklab_gpu(rgb_image, xp=None):
    """
    GPU version of batch sRGB to Oklab conversion.

    Args:
        rgb_image: Input image (H, W, 3) in sRGB [0, 1]
        xp: Array module (auto-detect if None)

    Returns:
        Image in Oklab space
    """
    if xp is None:
        xp = get_array_module(use_gpu=True)

    # Get color matrices
    matrices = get_gpu_color_matrices(xp)

    # Ensure image is on GPU
    rgb_gpu = xp.asarray(rgb_image, dtype=xp.float32)

    # Step 1: sRGB to linear RGB
    linear = srgb_to_linear_gpu(rgb_gpu, xp)

    # Step 2: Linear RGB to XYZ (using einsum for efficiency)
    xyz = xp.einsum("ij,...j->...i", matrices["LINEAR_RGB_TO_XYZ"], linear)

    # Step 3: XYZ to LMS
    lms = xp.einsum("ij,...j->...i", matrices["XYZ_TO_LMS"], xyz)

    # Step 4: Apply cube root
    lms_cbrt = xp.cbrt(lms)

    # Step 5: LMS to Oklab
    return xp.einsum("ij,...j->...i", matrices["LMS_TO_OKLAB"], lms_cbrt)


def batch_oklab_to_srgb_gpu(oklab_image, xp=None):
    """
    GPU version of batch Oklab to sRGB conversion.

    Args:
        oklab_image: Input image (H, W, 3) in Oklab
        xp: Array module (auto-detect if None)

    Returns:
        Image in sRGB space [0, 1]
    """
    if xp is None:
        xp = get_array_module(use_gpu=True)

    # Get color matrices
    matrices = get_gpu_color_matrices(xp)

    # Ensure image is on GPU
    oklab_gpu = xp.asarray(oklab_image, dtype=xp.float32)

    # Step 1: Oklab to LMS (cbrt space)
    lms_cbrt = xp.einsum("ij,...j->...i", matrices["OKLAB_TO_LMS"], oklab_gpu)

    # Step 2: Apply cube
    lms = lms_cbrt**3

    # Step 3: LMS to XYZ
    xyz = xp.einsum("ij,...j->...i", matrices["LMS_TO_XYZ"], lms)

    # Step 4: XYZ to linear RGB
    linear = xp.einsum("ij,...j->...i", matrices["XYZ_TO_LINEAR_RGB"], xyz)

    # Step 5: Linear RGB to sRGB
    srgb = linear_to_srgb_gpu(linear, xp)

    # Clamp to valid range
    return xp.clip(srgb, 0.0, 1.0)


def batch_oklab_to_oklch_gpu(oklab_image, xp=None):
    """GPU version of Oklab to OKLCH conversion."""
    if xp is None:
        xp = get_array_module(use_gpu=True)

    oklab_gpu = xp.asarray(oklab_image, dtype=xp.float32)

    l = oklab_gpu[..., 0]
    a = oklab_gpu[..., 1]
    b = oklab_gpu[..., 2]

    c = xp.sqrt(a * a + b * b)
    h = xp.arctan2(b, a) * 180.0 / xp.pi
    h = xp.where(h < 0, h + 360.0, h)

    return xp.stack([l, c, h], axis=-1)


def batch_oklch_to_oklab_gpu(oklch_image, xp=None):
    """GPU version of OKLCH to Oklab conversion."""
    if xp is None:
        xp = get_array_module(use_gpu=True)

    oklch_gpu = xp.asarray(oklch_image, dtype=xp.float32)

    l = oklch_gpu[..., 0]
    c = oklch_gpu[..., 1]
    h = oklch_gpu[..., 2]

    h_rad = h * xp.pi / 180.0
    a = c * xp.cos(h_rad)
    b = c * xp.sin(h_rad)

    return xp.stack([l, a, b], axis=-1)


def transform_pixels_gpu(
    oklab_image,
    oklch_image,
    attractors_lab,
    attractors_lch,
    tolerances,
    strengths,
    flags,
    xp=None,
):
    """
    GPU version of pixel transformation.

    Args:
        oklab_image: Image in Oklab space (H, W, 3)
        oklch_image: Image in OKLCH space (H, W, 3)
        attractors_lab: Attractors in Oklab (N, 3)
        attractors_lch: Attractors in OKLCH (N, 3)
        tolerances: Tolerance values [0, 100]
        strengths: Strength values [0, 100]
        flags: Boolean array [luminance, saturation, chroma]
        xp: Array module (auto-detect if None)

    Returns:
        Transformed image in Oklab space
    """
    if xp is None:
        xp = get_array_module(use_gpu=True)

    # Transfer to GPU
    oklab_gpu = xp.asarray(oklab_image, dtype=xp.float32)
    oklch_gpu = xp.asarray(oklch_image, dtype=xp.float32)
    attr_lab = xp.asarray(attractors_lab, dtype=xp.float32)
    attr_lch = xp.asarray(attractors_lch, dtype=xp.float32)
    tol = xp.asarray(tolerances, dtype=xp.float32)
    str_vals = xp.asarray(strengths, dtype=xp.float32)

    h, w = oklab_gpu.shape[:2]
    num_attractors = len(attr_lab)

    # Reshape for broadcasting
    pixels_lab = oklab_gpu.reshape(-1, 3)  # (H*W, 3)
    pixels_lch = oklch_gpu.reshape(-1, 3)  # (H*W, 3)

    # Calculate distances to all attractors
    # Broadcasting: (H*W, 1, 3) - (1, N, 3) = (H*W, N, 3)
    delta = pixels_lab[:, None, :] - attr_lab[None, :, :]
    distances = xp.sqrt(xp.sum(delta**2, axis=2))  # (H*W, N)

    # Calculate weights
    max_distances = 2.5 * (tol / 100.0)  # Linear mapping
    d_norm = distances / max_distances[None, :]

    # Raised cosine falloff
    within_tolerance = d_norm <= 1.0
    falloff = 0.5 * (xp.cos(d_norm * xp.pi) + 1.0)
    weights = within_tolerance * (str_vals[None, :] / 100.0) * falloff  # (H*W, N)

    # Normalize weights
    total_weights = xp.sum(weights, axis=1, keepdims=True)  # (H*W, 1)
    has_weight = total_weights > 0

    # Source weight for pixels with attractors
    source_weights = xp.where(total_weights > 1.0, 0.0, 1.0 - total_weights)

    # Normalize if needed
    weights = xp.where(total_weights > 1.0, weights / total_weights, weights)

    # Initialize result with original values
    result_lch = pixels_lch.copy()

    # Transform each channel if enabled
    if flags[0]:  # Luminance
        weighted_l = xp.sum(weights * attr_lch[:, 0][None, :], axis=1)
        result_lch[:, 0] = xp.where(
            has_weight.squeeze(),
            source_weights.squeeze() * pixels_lch[:, 0] + weighted_l,
            pixels_lch[:, 0],
        )

    if flags[1]:  # Saturation
        weighted_c = xp.sum(weights * attr_lch[:, 1][None, :], axis=1)
        result_lch[:, 1] = xp.where(
            has_weight.squeeze(),
            source_weights.squeeze() * pixels_lch[:, 1] + weighted_c,
            pixels_lch[:, 1],
        )

    if flags[2]:  # Hue
        # Circular mean for chroma
        h_rad = pixels_lch[:, 2] * xp.pi / 180.0
        sin_sum = source_weights.squeeze() * xp.sin(h_rad)
        cos_sum = source_weights.squeeze() * xp.cos(h_rad)

        # Add weighted attractor hues
        for i in range(num_attractors):
            h_attr_rad = attr_lch[i, 2] * xp.pi / 180.0
            sin_sum += weights[:, i] * xp.sin(h_attr_rad)
            cos_sum += weights[:, i] * xp.cos(h_attr_rad)

        new_h = xp.arctan2(sin_sum, cos_sum) * 180.0 / xp.pi
        new_h = xp.where(new_h < 0, new_h + 360.0, new_h)

        result_lch[:, 2] = xp.where(has_weight.squeeze(), new_h, pixels_lch[:, 2])

    # Convert back to Oklab
    h_rad = result_lch[:, 2] * xp.pi / 180.0
    result_lab = xp.stack(
        [
            result_lch[:, 0],
            result_lch[:, 1] * xp.cos(h_rad),
            result_lch[:, 1] * xp.sin(h_rad),
        ],
        axis=1,
    )

    # Reshape back to image dimensions
    return result_lab.reshape(h, w, 3)


def process_image_gpu(
    rgb_image,
    attractors_lab,
    tolerances,
    strengths,
    enable_luminance=True,
    enable_saturation=True,
    enable_hue=True,
):
    """
    Complete GPU pipeline for image processing.

    Args:
        rgb_image: Input image (H, W, 3) in sRGB [0, 1]
        attractors_lab: Attractor colors in Oklab (N, 3)
        tolerances: Tolerance values [0, 100]
        strengths: Strength values [0, 100]
        enable_luminance: Transform lightness
        enable_saturation: Transform chroma
        enable_hue: Transform chroma

    Returns:
        Transformed image in sRGB [0, 1]
    """
    # Check GPU memory
    required_mb = estimate_gpu_memory_required(rgb_image.shape, len(attractors_lab))
    has_memory, free_mb, total_mb = check_gpu_memory_available(required_mb)

    if not has_memory:
        logger.warning(
            f"Insufficient GPU memory: need {required_mb:.1f}MB, have {free_mb:.1f}MB"
        )
        return None

    xp = get_array_module(use_gpu=True)

    try:
        # Convert to Oklab
        oklab = batch_srgb_to_oklab_gpu(rgb_image, xp)

        # Convert to OKLCH
        oklch = batch_oklab_to_oklch_gpu(oklab, xp)

        # Also convert attractors to OKLCH
        attr_lab_gpu = xp.asarray(attractors_lab, dtype=xp.float32)
        attr_lch = batch_oklab_to_oklch_gpu(attr_lab_gpu.reshape(-1, 1, 3), xp).reshape(
            -1, 3
        )

        # Transform
        flags = xp.array([enable_luminance, enable_saturation, enable_hue])
        transformed_lab = transform_pixels_gpu(
            oklab, oklch, attractors_lab, attr_lch, tolerances, strengths, flags, xp
        )

        # Gamut mapping in OKLCH space
        batch_oklab_to_oklch_gpu(transformed_lab, xp)
        # Simple gamut clipping for now (TODO: implement proper gamut mapping)

        # Convert back to sRGB
        result_srgb = batch_oklab_to_srgb_gpu(transformed_lab, xp)

        # Transfer back to CPU
        if hasattr(result_srgb, "get"):  # CuPy array
            return result_srgb.get()
        return np.array(result_srgb)

    except Exception as e:
        logger.error(f"GPU processing failed: {e}")
        return None
