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
        luminance: bool = True,
        saturation: bool = True,
        hue: bool = True,
        verbose: bool = False,
    ) -> None:
        """
        Transform image colors using a percentile-based attractor model.

        Args:
            input_image: Path to input image
            *attractors: Color attractors in format "color;tolerance;strength"
            output_image: Path to output image
            luminance: Whether to include luminance in the transformation
            saturation: Whether to include saturation in the transformation
            hue: Whether to include hue in the transformation
            verbose: Whether to print verbose output

        Examples:
            imgcolorshine shine photo.jpg "red;50;75"
            imgcolorshine shine landscape.png "oklch(80% 0.2 60);40;60" "#ff6b35;30;80" --output_image=sunset.png
            imgcolorshine shine portrait.jpg "green;60;90" --luminance=False --saturation=False
            imgcolorshine shine large.jpg "blue;30;50" --fast_hierar --fast_spatial

        """
        process_image(
            input_image=input_image,
            attractors=attractors,
            output_image=output_image,
            luminance=luminance,
            saturation=saturation,
            hue=hue,
            verbose=verbose,
        )


def main():
    """Fire CLI entry point.

    Used in:
    - src/imgcolorshine/__main__.py
    """
    fire.Fire(ImgColorShineCLI)


if __name__ == "__main__":
    main()
