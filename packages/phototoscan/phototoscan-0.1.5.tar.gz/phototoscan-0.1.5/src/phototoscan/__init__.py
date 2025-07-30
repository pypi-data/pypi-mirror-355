"""
PhotoToScan: Convert casual photos of documents into professional scans.

This package provides functionality to automatically detect document boundaries
in photos, apply perspective correction to get a top-down view, and enhance
image quality to produce professional-looking scanned documents.

The module can be used as a command-line tool with the following usage:
    uvx phototoscan (--images <IMG_DIR> | --image <IMG_PATH>)

Examples:
    # Scan a single image
    uvx phototoscan --image path/to/document.jpg

    # Scan all images in a directory
    uvx phototoscan --images path/to/directory

    # Scan in grayscale mode
    uvx phototoscan --image path/to/document.jpg --mode grayscale

    # Specify custom output directory
    uvx phototoscan --image path/to/document.jpg --output-dir path/to/output

Processed images are saved to the specified output directory, or to an 'output'
directory in the same location as the input by default.
"""

import argparse
from pathlib import Path

from phototoscan.scanner import OutputFormat, Mode, Photo


def main():
    """
    Entry point for the command-line interface.

    Parses command-line arguments, validates inputs, and processes the images
    according to the specified options. Can handle both individual images and
    directories of images.

    Returns:
        None
    """
    # Create argument parser with descriptive help texts
    parser = argparse.ArgumentParser(
        description="Convert casual photos of documents into professional scans."
    )

    # Create mutually exclusive group for input selection (either single image or directory)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--images", help="Directory containing images to be scanned")
    group.add_argument("--image", help="Path to a single image to be scanned")

    # Add optional arguments
    parser.add_argument(
        "--mode",
        type=str,
        choices=["color", "grayscale"],
        default="color",
        help="Output mode: 'color' to preserve original colors, 'grayscale' for black and white",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Custom output directory for the scanned images (default: 'output' in the same directory as input)",
    )

    # Parse command-line arguments
    args = vars(parser.parse_args())
    im_dir = args["images"]
    im_file_path = args["image"]
    mode = Mode.GRAYSCALE if args["mode"] == "grayscale" else Mode.COLOR
    output_dir = args["output_dir"]

    # Define valid image file extensions
    valid_formats = [".jpg", ".jpeg", ".jp2", ".png", ".bmp", ".tiff", ".tif"]

    # Helper function to extract file extension
    get_ext = lambda f: Path(f).suffix.lower()

    # Process a single image if specified
    if im_file_path:
        f = Path(im_file_path)
        photo = Photo(
            f,
            output_format=OutputFormat.PATH_STR,  # Return output path as string
            mode=mode,  # Use specified color mode
            output_filename=f.name,  # Keep original filename
            output_dir=output_dir,  # Use specified output directory
        )
        path_str = photo.scan()  # Execute the document scanning process
        print("Processed " + path_str)  # Inform user of progress
    # Process all valid images in the specified directory
    else:
        im_dir = Path(im_dir)
        if output_dir is not None:
            output_dir = Path(output_dir)

        # Iterate through files in the directory
        for f in im_dir.iterdir():
            # Check if it's a file with valid image extension
            if f.is_file() and get_ext(f) in valid_formats:
                photo = Photo(
                    f,
                    output_format=OutputFormat.PATH_STR,  # Return output path as string
                    mode=mode,  # Use specified color mode
                    output_filename=f.name,  # Keep original filename
                    output_dir=output_dir,  # Use specified output directory
                )
                path_str = photo.scan()  # Execute the document scanning process
                print("Processed " + path_str)  # Inform user of progress


if __name__ == "__main__":
    main()
