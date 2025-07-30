#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["fire", "loguru"]
# ///
# this_file: src/imgcolorshine/cli.py

"""
Fire-based CLI interface for imgcolorshine.

Simple CLI class that delegates to the main processing logic.
"""

import fire

from imgcolorshine.colorshine import process_image


class ImgColorShineCLI:
    """CLI interface for imgcolorshine color transformations."""

    def shine(
        self,
        input_image: str,
        *attractors: str,
        output_image: str | None = None,
        chroma: bool = False,
        saturation: bool = False,
        luminance: bool = False,
        tile_size: int = 1024,
        LUT_size: int = 0,
        fast_hierar: bool = False,
        Fast_spatial: bool = True,
        gpu: bool = True,
        verbose: bool = False,
    ) -> None:
        """
        Transform image colors using OKLCH color attractors.

        Args:
            input_image: Path to input image
            *attractors: Color attractors in format "color;tolerance;strength"
            output_image: Output path (auto-generated if not provided)
            luminance: Transform lightness channel
            saturation: Transform chroma (saturation) channel
            chroma: Transform chroma channel
            verbose: Enable verbose logging
            tile_size: Tile size for processing large images
            gpu: Use GPU acceleration if available (default: True)
            LUT_size: Size of 3D LUT for acceleration (0=disabled, 65=default when enabled)
            fast_hierar: Enable fast_hierar multi-resolution processing (2-5x speedup)
            fast_spatial: Enable spatial acceleration (3-10x speedup, default: True)

        Examples:
            imgcolorshine shine photo.jpg "red;50;75"
            imgcolorshine shine landscape.png "oklch(80% 0.2 60);40;60" "#ff6b35;30;80" --output_image=sunset.png
            imgcolorshine shine portrait.jpg "green;60;90" --luminance=False --saturation=False
            imgcolorshine shine large.jpg "blue;30;50" --fast_hierar --fast_spatial

        """
        # Delegate to main processing logic
        process_image(
            input_image=input_image,
            attractors=attractors,
            output_image=output_image,
            luminance=luminance,
            saturation=saturation,
            chroma=chroma,
            verbose=verbose,
            tile_size=tile_size,
            gpu=gpu,
            lut_size=LUT_size,
            fast_hierar=fast_hierar,
            fast_spatial=Fast_spatial,
        )


def main():
    """Fire CLI entry point.

    Used in:
    - src/imgcolorshine/__main__.py
    """
    fire.Fire(ImgColorShineCLI)


if __name__ == "__main__":
    main()
