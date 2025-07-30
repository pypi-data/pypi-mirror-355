#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["numpy", "loguru"]
# ///
# this_file: src/imgcolorshine/gpu.py

"""
GPU backend selection and management for imgcolorshine.

Provides automatic detection and selection of GPU acceleration libraries
(CuPy, JAX, etc.) with graceful fallback to CPU when unavailable.
"""

import numpy as np
from loguru import logger

# Global flags for available backends
GPU_AVAILABLE = False
CUPY_AVAILABLE = False
JAX_AVAILABLE = False
cp = None  # Ensure cp is always defined globally

# Try to import GPU libraries
try:
    import cupy as cp

    CUPY_AVAILABLE = cp.cuda.is_available()
    if CUPY_AVAILABLE:
        GPU_AVAILABLE = True
        logger.info(f"CuPy available with CUDA {cp.cuda.runtime.runtimeGetVersion()}")
except ImportError:
    logger.debug("CuPy not installed")
except Exception as e:
    logger.debug(f"CuPy initialization failed: {e}")


# Check JAX availability without importing at module level
def _check_jax_available():
    """Check if JAX is available and compatible with current NumPy version."""
    global JAX_AVAILABLE, GPU_AVAILABLE
    try:
        import jax
        import jax.numpy as jnp

        # Check if GPU is available for JAX
        if len(jax.devices("gpu")) > 0:
            JAX_AVAILABLE = True
            GPU_AVAILABLE = True
            logger.info(f"JAX available with {len(jax.devices('gpu'))} GPU(s)")
            return True
    except ImportError as e:
        # Handle both standard ImportError and NumPy compatibility error
        error_msg = str(e)
        if (
            "numpy.core._multiarray_umath failed to import" in error_msg
            or "A module that was compiled using NumPy 1.x" in error_msg
        ):
            logger.debug(
                "JAX not compatible with current NumPy version (likely NumPy 2.x with JAX compiled for NumPy 1.x)"
            )
        else:
            logger.debug("JAX not installed")
    except Exception as e:
        logger.debug(f"JAX initialization failed: {e}")
    return False


# Defer JAX check to avoid import errors at module level
# This will be checked when JAX is actually needed
_jax_checked = False


class ArrayModule:
    """Wrapper for array operations that can use CPU or GPU."""

    def __init__(self, backend="auto"):
        """
        Initialize array module.

        Args:
            backend: 'auto', 'cpu', 'cupy', or 'jax'
        """
        self.backend = self._select_backend(backend)
        self.xp = self._get_module()

    def _select_backend(self, backend):
        """Select the appropriate backend based on availability."""
        global _jax_checked

        # Check JAX availability on first use
        if not _jax_checked:
            _check_jax_available()
            _jax_checked = True

        if backend == "auto":
            if CUPY_AVAILABLE:
                return "cupy"
            if JAX_AVAILABLE:
                return "jax"
            return "cpu"
        if backend == "cupy" and not CUPY_AVAILABLE:
            logger.warning("CuPy requested but not available, falling back to CPU")
            return "cpu"
        if backend == "jax" and not JAX_AVAILABLE:
            logger.warning("JAX requested but not available, falling back to CPU")
            return "cpu"
        return backend

    def _get_module(self):
        """Get the appropriate array module."""
        if self.backend == "cupy":
            import cupy

            return cupy
        if self.backend == "jax":
            import jax.numpy

            return jax.numpy
        return np

    def to_device(self, array):
        """Transfer array to the appropriate device."""
        if self.backend == "cupy":
            return cp.asarray(array)
        if self.backend == "jax":
            import jax.numpy as jnp

            return jnp.asarray(array)
        return np.asarray(array)

    def to_cpu(self, array):
        """Transfer array back to CPU."""
        if self.backend == "cupy":
            return cp.asnumpy(array)
        if self.backend == "jax":
            return np.array(array)
        return array

    def get_info(self):
        """Get information about the current backend."""
        info = {
            "backend": self.backend,
            "gpu_available": GPU_AVAILABLE,
        }

        if self.backend == "cupy":
            info["cuda_version"] = cp.cuda.runtime.runtimeGetVersion()
            info["device_name"] = cp.cuda.Device().name
            info["device_memory"] = cp.cuda.Device().mem_info
        elif self.backend == "jax":
            try:
                import jax

                info["devices"] = [str(d) for d in jax.devices()]
            except ImportError:
                info["devices"] = []

        return info


def get_array_module(use_gpu=True, backend="auto"):
    """
    Get numpy or GPU array module based on availability and preference.

    Args:
        use_gpu: Whether to use GPU if available
        backend: Specific backend to use ('auto', 'cpu', 'cupy', 'jax')

    Returns:
        Array module (numpy, cupy, or jax.numpy)
    """
    if not use_gpu:
        return np

    module = ArrayModule(backend)
    logger.debug(f"Using {module.backend} backend for array operations")
    return module.xp


def estimate_gpu_memory_required(image_shape, num_attractors, dtype=np.float32):
    """
    Estimate GPU memory required for processing.

    Args:
        image_shape: Tuple of (height, width, channels)
        num_attractors: Number of color attractors
        dtype: Data type for arrays

    Returns:
        Estimated memory in MB
    """
    h, w, c = image_shape
    bytes_per_element = np.dtype(dtype).itemsize

    # Memory for images
    image_memory = h * w * c * bytes_per_element
    # Input + output + 2 intermediate color spaces
    total_image_memory = image_memory * 4

    # Memory for attractors (small, but kept on GPU)
    attractor_memory = num_attractors * c * bytes_per_element * 2  # Lab + LCH

    # Memory for weights and distances
    weight_memory = h * w * num_attractors * bytes_per_element

    # Total with safety margin
    total_bytes = (total_image_memory + attractor_memory + weight_memory) * 1.2
    return total_bytes / (1024 * 1024)


def check_gpu_memory_available(required_mb):
    """
    Check if enough GPU memory is available.

    Args:
        required_mb: Required memory in MB

    Returns:
        Tuple of (has_enough_memory, available_mb, total_mb)
    """
    global _jax_checked

    if CUPY_AVAILABLE:
        free, total = cp.cuda.Device().mem_info
        free_mb = free / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        has_enough = free_mb >= required_mb
        return has_enough, free_mb, total_mb

    # Check JAX availability on first use
    if not _jax_checked:
        _check_jax_available()
        _jax_checked = True

    # For JAX, assume we have enough memory (harder to check)
    if JAX_AVAILABLE:
        return True, 0, 0

    return False, 0, 0


class GPUMemoryPool:
    """Manages GPU memory allocation with pooling for better performance."""

    def __init__(self, backend="auto"):
        """Initialize memory pool."""
        self.backend = ArrayModule(backend).backend
        self.pool = None

        if self.backend == "cupy":
            # Create memory pool for CuPy
            self.pool = cp.cuda.MemoryPool()
            cp.cuda.set_allocator(self.pool.malloc)
            logger.debug("Initialized CuPy memory pool")

    def clear(self):
        """Clear the memory pool."""
        if self.pool and self.backend == "cupy":
            self.pool.free_all_blocks()
            logger.debug("Cleared GPU memory pool")

    def get_usage(self):
        """Get current memory usage."""
        if self.pool and self.backend == "cupy":
            return {
                "used_bytes": self.pool.used_bytes(),
                "total_bytes": self.pool.total_bytes(),
                "n_free_blocks": self.pool.n_free_blocks(),
            }
        return None


# Singleton instance for global memory management
_memory_pool = None


def get_memory_pool(backend="auto"):
    """Get the global memory pool instance."""
    global _memory_pool
    if _memory_pool is None:
        _memory_pool = GPUMemoryPool(backend)
    return _memory_pool
