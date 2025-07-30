#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["numpy", "numba"]
# ///
# this_file: src/imgcolorshine/kernel.py

"""
Fused color transformation kernels for maximum performance.

Combines all color space conversions and transformations into single kernels
that keep all intermediate values in CPU registers, eliminating memory traffic.
"""

import numba
import numpy as np

from imgcolorshine.trans_numba import (
    _LINEAR_RGB_TO_XYZ,
    _LMS_TO_OKLAB,
    _LMS_TO_XYZ,
    _OKLAB_TO_LMS,
    _XYZ_TO_LINEAR_RGB,
    _XYZ_TO_LMS,
    linear_to_srgb_component,
    srgb_to_linear_component,
)

# Note: falloff function is inlined for performance


@numba.njit(cache=True, inline="always")
def transform_pixel_fused(
    r,
    g,
    b,
    attractors_lab,
    tolerances,
    strengths,
    enable_luminance,
    enable_saturation,
    enable_hue,
):
    """
    Single fused kernel for complete pixel transformation.

    Performs: sRGB → Linear RGB → XYZ → LMS → Oklab → OKLCH → Transform →
              OKLCH → Oklab → LMS → XYZ → Linear RGB → sRGB

    All operations happen in registers without intermediate arrays.

    Parameters:
        r, g, b: Input sRGB values [0, 1]
        attractors_lab: Array of attractor colors in Oklab space (N, 3)
        tolerances: Array of tolerance values [0, 1]
        strengths: Array of strength values [0, 1]
        enable_luminance: Transform lightness channel
        enable_saturation: Transform chroma channel
        enable_hue: Transform chroma channel

    Returns:
        Tuple of (r, g, b) transformed sRGB values
    """
    # Step 1: sRGB to Linear RGB (gamma correction)
    r_lin = srgb_to_linear_component(r)
    g_lin = srgb_to_linear_component(g)
    b_lin = srgb_to_linear_component(b)

    # Step 2: Linear RGB to XYZ (matrix multiply inline)
    x = (
        _LINEAR_RGB_TO_XYZ[0, 0] * r_lin
        + _LINEAR_RGB_TO_XYZ[0, 1] * g_lin
        + _LINEAR_RGB_TO_XYZ[0, 2] * b_lin
    )
    y = (
        _LINEAR_RGB_TO_XYZ[1, 0] * r_lin
        + _LINEAR_RGB_TO_XYZ[1, 1] * g_lin
        + _LINEAR_RGB_TO_XYZ[1, 2] * b_lin
    )
    z = (
        _LINEAR_RGB_TO_XYZ[2, 0] * r_lin
        + _LINEAR_RGB_TO_XYZ[2, 1] * g_lin
        + _LINEAR_RGB_TO_XYZ[2, 2] * b_lin
    )

    # Step 3: XYZ to LMS
    l = _XYZ_TO_LMS[0, 0] * x + _XYZ_TO_LMS[0, 1] * y + _XYZ_TO_LMS[0, 2] * z
    m = _XYZ_TO_LMS[1, 0] * x + _XYZ_TO_LMS[1, 1] * y + _XYZ_TO_LMS[1, 2] * z
    s = _XYZ_TO_LMS[2, 0] * x + _XYZ_TO_LMS[2, 1] * y + _XYZ_TO_LMS[2, 2] * z

    # Step 4: Apply cube root
    l_cbrt = np.cbrt(l)
    m_cbrt = np.cbrt(m)
    s_cbrt = np.cbrt(s)

    # Step 5: LMS to Oklab
    lab_l = (
        _LMS_TO_OKLAB[0, 0] * l_cbrt
        + _LMS_TO_OKLAB[0, 1] * m_cbrt
        + _LMS_TO_OKLAB[0, 2] * s_cbrt
    )
    lab_a = (
        _LMS_TO_OKLAB[1, 0] * l_cbrt
        + _LMS_TO_OKLAB[1, 1] * m_cbrt
        + _LMS_TO_OKLAB[1, 2] * s_cbrt
    )
    lab_b = (
        _LMS_TO_OKLAB[2, 0] * l_cbrt
        + _LMS_TO_OKLAB[2, 1] * m_cbrt
        + _LMS_TO_OKLAB[2, 2] * s_cbrt
    )

    # Step 6: Oklab to OKLCH
    lch_l = lab_l
    lch_c = np.sqrt(lab_a * lab_a + lab_b * lab_b)
    lch_h = np.arctan2(lab_b, lab_a)

    # Step 7: Apply transformations
    # Calculate weights from all attractors
    total_weight = 0.0
    weighted_l = 0.0
    weighted_c = 0.0
    weighted_h_sin = 0.0
    weighted_h_cos = 0.0

    for i in range(len(attractors_lab)):
        # Get attractor in OKLCH
        attr_l = attractors_lab[i, 0]
        attr_a = attractors_lab[i, 1]
        attr_b = attractors_lab[i, 2]
        attr_c = np.sqrt(attr_a * attr_a + attr_b * attr_b)
        attr_h = np.arctan2(attr_b, attr_a)

        # Calculate distance in enabled channels
        dist_sq = 0.0
        if enable_luminance:
            dl = lch_l - attr_l
            dist_sq += dl * dl
        if enable_saturation:
            dc = lch_c - attr_c
            dist_sq += dc * dc
        if enable_hue and lch_c > 1e-8 and attr_c > 1e-8:
            # Angular distance with wraparound
            dh = lch_h - attr_h
            if dh > np.pi:
                dh -= 2 * np.pi
            elif dh < -np.pi:
                dh += 2 * np.pi
            # Scale by average chroma for perceptual uniformity
            avg_c = (lch_c + attr_c) * 0.5
            dist_sq += (dh * avg_c) * (dh * avg_c)

        # Calculate weight using inline raised cosine falloff
        dist = np.sqrt(dist_sq)
        # Map tolerance to max distance with linear mapping
        max_dist = 2.5 * (tolerances[i] / 100.0)

        if dist <= max_dist:
            # Normalized distance
            d_norm = dist / max_dist
            # Raised cosine falloff
            attraction_factor = 0.5 * (np.cos(d_norm * np.pi) + 1.0)
            # Final weight
            weight = (strengths[i] / 100.0) * attraction_factor
        else:
            weight = 0.0

        if weight > 0:
            total_weight += weight
            weighted_l += weight * attr_l
            weighted_c += weight * attr_c
            weighted_h_sin += weight * np.sin(attr_h)
            weighted_h_cos += weight * np.cos(attr_h)

    # Apply weighted transformation
    if total_weight > 0:
        inv_weight = 1.0 / total_weight
        if enable_luminance:
            lch_l = (1.0 - total_weight) * lch_l + weighted_l
        if enable_saturation:
            lch_c = (1.0 - total_weight) * lch_c + weighted_c
        if enable_hue and lch_c > 1e-8:
            target_h = np.arctan2(
                weighted_h_sin * inv_weight, weighted_h_cos * inv_weight
            )
            lch_h = (1.0 - total_weight) * lch_h + total_weight * target_h

    # Step 8: OKLCH back to Oklab
    lab_a = lch_c * np.cos(lch_h)
    lab_b = lch_c * np.sin(lch_h)

    # Step 9: Gamut mapping - binary search for valid chroma
    # First check if in gamut
    in_gamut = False
    max_iters = 20
    epsilon = 0.0001

    for _ in range(1):  # Single check first
        # Continue conversion to check gamut
        # Oklab to LMS
        l_cbrt = (
            _OKLAB_TO_LMS[0, 0] * lch_l
            + _OKLAB_TO_LMS[0, 1] * lab_a
            + _OKLAB_TO_LMS[0, 2] * lab_b
        )
        m_cbrt = (
            _OKLAB_TO_LMS[1, 0] * lch_l
            + _OKLAB_TO_LMS[1, 1] * lab_a
            + _OKLAB_TO_LMS[1, 2] * lab_b
        )
        s_cbrt = (
            _OKLAB_TO_LMS[2, 0] * lch_l
            + _OKLAB_TO_LMS[2, 1] * lab_a
            + _OKLAB_TO_LMS[2, 2] * lab_b
        )

        l = l_cbrt * l_cbrt * l_cbrt
        m = m_cbrt * m_cbrt * m_cbrt
        s = s_cbrt * s_cbrt * s_cbrt

        # LMS to XYZ
        x = _LMS_TO_XYZ[0, 0] * l + _LMS_TO_XYZ[0, 1] * m + _LMS_TO_XYZ[0, 2] * s
        y = _LMS_TO_XYZ[1, 0] * l + _LMS_TO_XYZ[1, 1] * m + _LMS_TO_XYZ[1, 2] * s
        z = _LMS_TO_XYZ[2, 0] * l + _LMS_TO_XYZ[2, 1] * m + _LMS_TO_XYZ[2, 2] * s

        # XYZ to Linear RGB
        r_lin = (
            _XYZ_TO_LINEAR_RGB[0, 0] * x
            + _XYZ_TO_LINEAR_RGB[0, 1] * y
            + _XYZ_TO_LINEAR_RGB[0, 2] * z
        )
        g_lin = (
            _XYZ_TO_LINEAR_RGB[1, 0] * x
            + _XYZ_TO_LINEAR_RGB[1, 1] * y
            + _XYZ_TO_LINEAR_RGB[1, 2] * z
        )
        b_lin = (
            _XYZ_TO_LINEAR_RGB[2, 0] * x
            + _XYZ_TO_LINEAR_RGB[2, 1] * y
            + _XYZ_TO_LINEAR_RGB[2, 2] * z
        )

        if (
            r_lin >= 0
            and r_lin <= 1
            and g_lin >= 0
            and g_lin <= 1
            and b_lin >= 0
            and b_lin <= 1
        ):
            in_gamut = True

    # If not in gamut, binary search for valid chroma
    if not in_gamut and lch_c > epsilon:
        c_min = 0.0
        c_max = lch_c

        for _ in range(max_iters):
            if c_max - c_min < epsilon:
                break

            c_mid = (c_min + c_max) * 0.5

            # Test with reduced chroma
            test_a = c_mid * np.cos(lch_h)
            test_b = c_mid * np.sin(lch_h)

            # Oklab to LMS
            l_cbrt = (
                _OKLAB_TO_LMS[0, 0] * lch_l
                + _OKLAB_TO_LMS[0, 1] * test_a
                + _OKLAB_TO_LMS[0, 2] * test_b
            )
            m_cbrt = (
                _OKLAB_TO_LMS[1, 0] * lch_l
                + _OKLAB_TO_LMS[1, 1] * test_a
                + _OKLAB_TO_LMS[1, 2] * test_b
            )
            s_cbrt = (
                _OKLAB_TO_LMS[2, 0] * lch_l
                + _OKLAB_TO_LMS[2, 1] * test_a
                + _OKLAB_TO_LMS[2, 2] * test_b
            )

            l = l_cbrt * l_cbrt * l_cbrt
            m = m_cbrt * m_cbrt * m_cbrt
            s = s_cbrt * s_cbrt * s_cbrt

            # LMS to XYZ
            x = _LMS_TO_XYZ[0, 0] * l + _LMS_TO_XYZ[0, 1] * m + _LMS_TO_XYZ[0, 2] * s
            y = _LMS_TO_XYZ[1, 0] * l + _LMS_TO_XYZ[1, 1] * m + _LMS_TO_XYZ[1, 2] * s
            z = _LMS_TO_XYZ[2, 0] * l + _LMS_TO_XYZ[2, 1] * m + _LMS_TO_XYZ[2, 2] * s

            # XYZ to Linear RGB
            r_test = (
                _XYZ_TO_LINEAR_RGB[0, 0] * x
                + _XYZ_TO_LINEAR_RGB[0, 1] * y
                + _XYZ_TO_LINEAR_RGB[0, 2] * z
            )
            g_test = (
                _XYZ_TO_LINEAR_RGB[1, 0] * x
                + _XYZ_TO_LINEAR_RGB[1, 1] * y
                + _XYZ_TO_LINEAR_RGB[1, 2] * z
            )
            b_test = (
                _XYZ_TO_LINEAR_RGB[2, 0] * x
                + _XYZ_TO_LINEAR_RGB[2, 1] * y
                + _XYZ_TO_LINEAR_RGB[2, 2] * z
            )

            if (
                r_test >= 0
                and r_test <= 1
                and g_test >= 0
                and g_test <= 1
                and b_test >= 0
                and b_test <= 1
            ):
                c_min = c_mid
            else:
                c_max = c_mid

        # Update with gamut-mapped chroma
        lch_c = c_min
        lab_a = lch_c * np.cos(lch_h)
        lab_b = lch_c * np.sin(lch_h)

    # Step 10: Final conversion back to sRGB
    # Oklab to LMS
    l_cbrt = (
        _OKLAB_TO_LMS[0, 0] * lch_l
        + _OKLAB_TO_LMS[0, 1] * lab_a
        + _OKLAB_TO_LMS[0, 2] * lab_b
    )
    m_cbrt = (
        _OKLAB_TO_LMS[1, 0] * lch_l
        + _OKLAB_TO_LMS[1, 1] * lab_a
        + _OKLAB_TO_LMS[1, 2] * lab_b
    )
    s_cbrt = (
        _OKLAB_TO_LMS[2, 0] * lch_l
        + _OKLAB_TO_LMS[2, 1] * lab_a
        + _OKLAB_TO_LMS[2, 2] * lab_b
    )

    l = l_cbrt * l_cbrt * l_cbrt
    m = m_cbrt * m_cbrt * m_cbrt
    s = s_cbrt * s_cbrt * s_cbrt

    # LMS to XYZ
    x = _LMS_TO_XYZ[0, 0] * l + _LMS_TO_XYZ[0, 1] * m + _LMS_TO_XYZ[0, 2] * s
    y = _LMS_TO_XYZ[1, 0] * l + _LMS_TO_XYZ[1, 1] * m + _LMS_TO_XYZ[1, 2] * s
    z = _LMS_TO_XYZ[2, 0] * l + _LMS_TO_XYZ[2, 1] * m + _LMS_TO_XYZ[2, 2] * s

    # XYZ to Linear RGB
    r_lin = (
        _XYZ_TO_LINEAR_RGB[0, 0] * x
        + _XYZ_TO_LINEAR_RGB[0, 1] * y
        + _XYZ_TO_LINEAR_RGB[0, 2] * z
    )
    g_lin = (
        _XYZ_TO_LINEAR_RGB[1, 0] * x
        + _XYZ_TO_LINEAR_RGB[1, 1] * y
        + _XYZ_TO_LINEAR_RGB[1, 2] * z
    )
    b_lin = (
        _XYZ_TO_LINEAR_RGB[2, 0] * x
        + _XYZ_TO_LINEAR_RGB[2, 1] * y
        + _XYZ_TO_LINEAR_RGB[2, 2] * z
    )

    # Clamp linear values
    r_lin = max(0.0, min(1.0, r_lin))
    g_lin = max(0.0, min(1.0, g_lin))
    b_lin = max(0.0, min(1.0, b_lin))

    # Linear RGB to sRGB
    r_out = linear_to_srgb_component(r_lin)
    g_out = linear_to_srgb_component(g_lin)
    b_out = linear_to_srgb_component(b_lin)

    return r_out, g_out, b_out


@numba.njit(parallel=True, cache=True)
def transform_image_fused(
    rgb_image,
    attractors_lab,
    tolerances,
    strengths,
    enable_luminance,
    enable_saturation,
    enable_hue,
):
    """
    Transform entire image using fused kernel with parallel processing.

    Parameters:
        rgb_image: Input image array (H, W, 3) in sRGB [0, 1]
        attractors_lab: Array of attractor colors in Oklab space (N, 3)
        tolerances: Array of tolerance values [0, 1]
        strengths: Array of strength values [0, 1]
        enable_luminance: Transform lightness channel
        enable_saturation: Transform chroma channel
        enable_hue: Transform chroma channel

    Returns:
        Transformed image array (H, W, 3) in sRGB [0, 1]
    """
    h, w = rgb_image.shape[:2]
    output = np.empty_like(rgb_image)

    for i in numba.prange(h):
        for j in range(w):
            r, g, b = transform_pixel_fused(
                rgb_image[i, j, 0],
                rgb_image[i, j, 1],
                rgb_image[i, j, 2],
                attractors_lab,
                tolerances,
                strengths,
                enable_luminance,
                enable_saturation,
                enable_hue,
            )
            output[i, j, 0] = r
            output[i, j, 1] = g
            output[i, j, 2] = b

    return output
