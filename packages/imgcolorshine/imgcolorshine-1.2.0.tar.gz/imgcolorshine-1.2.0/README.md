# imgcolorshine

Transform image colors using OKLCH color attractors - a physics-inspired tool that operates in perceptually uniform color space.

## Overview

`imgcolorshine` applies a gravitational-inspired color transformation where specified "attractor" colors pull the image's colors toward them. The tool works in the OKLCH color space, ensuring perceptually uniform and natural-looking results.

## Features

- **Perceptually Uniform**: Operations in OKLCH color space for intuitive results
- **Flexible Color Input**: Supports all CSS color formats (hex, rgb, hsl, oklch, named colors)
- **Selective Channel Control**: Transform lightness, saturation, and/or hue independently
- **Multiple Attractors**: Blend influences from multiple color targets
- **High Performance**: Optimized with NumPy and Numba for fast processing
- **Memory Efficient**: Automatic tiling for large images
- **Professional Quality**: CSS Color Module 4 compliant gamut mapping

## Installation

```bash
# Install from PyPI
pip install imgcolorshine

# Or install from source
git clone https://github.com/twardoch/imgcolorshine.git
cd imgcolorshine
pip install -e .
```

## Usage

### Basic Example

Transform an image to be more red:

```bash
imgcolorshine shine photo.jpg "red;50;75"
```

### Command Syntax

```bash
imgcolorshine shine INPUT_IMAGE ATTRACTOR1 [ATTRACTOR2 ...] [OPTIONS]
```

Each attractor has the format: `"color;tolerance;strength"`

- **color**: Any CSS color (e.g., "red", "#ff0000", "oklch(70% 0.2 120)")
- **tolerance**: 0-100 (radius of influence - how far the color reaches)
- **strength**: 0-100 (transformation intensity - how much colors are pulled)

### Options

- `--output_image PATH`: Output image file (auto-generated if not specified)
- `--luminance BOOL`: Enable/disable lightness transformation (default: True)
- `--saturation BOOL`: Enable/disable chroma transformation (default: True)
- `--hue BOOL`: Enable/disable hue transformation (default: True)
- `--verbose BOOL`: Enable verbose logging (default: False)
- `--tile_size INT`: Tile size for large images (default: 1024)

### Examples

**Warm sunset effect:**
```bash
imgcolorshine shine landscape.png \
  "oklch(80% 0.2 60);40;60" \
  "#ff6b35;30;80" \
  --output_image=sunset.png
```

**Shift only hues toward green:**
```bash
imgcolorshine shine portrait.jpg "green;60;90" \
  --luminance=False --saturation=False
```

**Multiple color influences:**
```bash
imgcolorshine shine photo.jpg \
  "oklch(70% 0.15 120);50;70" \
  "hsl(220 100% 50%);25;50" \
  "#ff00ff;30;40"
```


## How It Works

1. **Color Space**: All operations happen in OKLCH space for perceptual uniformity
2. **Attraction Model**: Each attractor color exerts influence based on:
   - **Distance**: How similar a pixel's color is to the attractor
   - **Tolerance**: Maximum distance at which influence occurs
   - **Strength**: Maximum transformation amount
3. **Falloff**: Smooth raised-cosine curve for natural transitions
4. **Blending**: Multiple attractors blend using normalized weighted averaging
5. **Gamut Mapping**: Out-of-bounds colors are mapped back to displayable range

## Understanding Parameters

### Tolerance (0-100)
- **Low values (0-20)**: Only very similar colors are affected
- **Medium values (30-60)**: Moderate range of colors transformed
- **High values (70-100)**: Wide range of colors influenced

### Strength (0-100)
- **Low values (0-30)**: Subtle color shifts
- **Medium values (40-70)**: Noticeable but natural transformations
- **High values (80-100)**: Strong color replacement

## Performance

- Processes a 1920×1080 image in ~2-5 seconds
- Automatic tiling for images larger than 2GB memory usage
- GPU acceleration available with CuPy (10-100x speedup)

## Technical Details

- **Color Engine**: ColorAide for accurate OKLCH operations
- **Image I/O**: OpenCV (4x faster than PIL for PNG)
- **Computation**: NumPy + Numba JIT compilation
- **Gamut Mapping**: CSS Color Module 4 algorithm
- **Falloff Function**: Raised cosine for smooth transitions

## Development

This project follows a structured approach focusing on code quality, documentation, and maintainable development practices.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

- Created by Adam Twardoch
- Developed with Antropic software
