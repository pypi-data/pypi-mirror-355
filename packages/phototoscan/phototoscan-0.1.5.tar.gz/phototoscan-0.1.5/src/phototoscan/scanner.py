"""
Document scanning module for converting casual photos into professional scans.

This module provides functionality to detect document boundaries in photos,
apply perspective transformation to get a "top-down" view, and enhance
the image quality to produce professional-quality scanned documents.
"""

from enum import Enum, auto
import mimetypes
from pathlib import Path
from typing import Union

import cv2
import numpy as np
import puremagic

from phototoscan.pyimagesearch import transform
from phototoscan.document_scanner.scan import get_contour


class OutputFormat(Enum):
    """
    Enumeration of supported output formats for processed images.

    Attributes
    ----------
    PATH_STR : auto
        Return the path to the saved image as a string.
    FILE_PATH : auto
        Return the path to the saved image as a Path object.
    BYTES : auto
        Return the image data as bytes.
    NP_ARRAY : auto
        Return the image data as a NumPy array.
    """

    PATH_STR = auto()
    FILE_PATH = auto()
    BYTES = auto()
    NP_ARRAY = auto()


class Mode(Enum):
    """
    Enumeration of supported image color modes.

    Attributes
    ----------
    COLOR : auto
        Process the image in color (BGR) mode.
    GRAYSCALE : auto
        Process the image in grayscale mode.
    """

    COLOR = auto()
    GRAYSCALE = auto()


class Photo(object):
    """
    A class for converting casual document photos into professional scans.

    This class provides a set of professional document scanning tools that can be used
    independently or together:
    - Loading document photos from various sources (file path, bytes, numpy array)
    - Detecting document boundaries in the photo
    - Applying perspective correction to create a top-down view
    - Converting between color modes (color or grayscale)
    - Enhancing document quality and readability through sharpening and thresholding
    - Saving results in various formats

    Each processing method can be called individually to perform specific operations
    on the document image. For convenience, the `scan()` method orchestrates the
    complete document scanning workflow by executing all steps in sequence.
    """

    # Input parameters
    img_input: Union[str, Path, bytes, bytearray, np.ndarray]  # Source image
    output_format: OutputFormat  # Format for returning the processed image
    mode: Mode = Mode.COLOR  # Color mode for processing
    output_dir: Union[str, Path, None] = (
        None  # Directory to save output (if applicable)
    )
    output_filename: Union[str, Path, None] = (
        None  # Filename for saving output (if applicable)
    )
    ext: Union[str, None] = None  # File extension for the output
    mime: Union[str, None] = None  # MIME type of the image

    # Internal state
    image: Union[np.ndarray, None] = None  # Loaded/processed image data
    corners: Union[np.ndarray, None] = None  # Detected document corners

    def __init__(
        self,
        img_input: Union[str, Path, bytes, bytearray, np.ndarray],
        output_format: OutputFormat,
        mode: Mode = Mode.COLOR,
        output_dir: Union[str, Path, None] = None,
        output_filename: Union[str, Path, None] = None,
        ext: Union[str, None] = None,
    ):
        """
        Initialize a document scanning processor with specified parameters.

        Parameters
        ----------
        img_input : Union[str, Path, bytes, bytearray, np.ndarray]
            The source image to process. Can be:
            - A path string to an image file
            - A Path object pointing to an image file
            - Bytes or bytearray containing image data
            - A NumPy array containing image data
        output_format : OutputFormat
            The format in which to return the processed image
        mode : Mode, optional
            The color mode for processing, by default Mode.COLOR
        output_dir : Union[str, Path, None], optional
            Directory to save output (required for PATH_STR and FILE_PATH output formats
            when img_input is bytes or ndarray), by default None
        output_filename : Union[str, Path, None], optional
            Filename for saving output (required for PATH_STR and FILE_PATH output formats
            when img_input is bytes or ndarray), by default None
        ext : Union[str, None], optional
            File extension for output (required for BYTES output format when
            img_input is ndarray), by default None

        Notes
        -----
        The document detection process uses the following parameters internally:
        - MIN_QUAD_AREA_RATIO (0.25): A contour will be rejected if its corners
          do not form a quadrilateral that covers at least 25% of the original image.
        - MAX_QUAD_ANGLE_RANGE (40): A contour will be rejected if the range
          of its interior angles exceeds 40 degrees.
        """
        self.img_input = img_input
        self.output_format = output_format
        self.mode = mode
        self.output_dir = output_dir
        self.output_filename = output_filename
        self.ext = ext
        self.post_init()

    def post_init(self):
        """
        Validate inputs and initialize additional parameters after __init__.

        This method performs the following validations and initializations:
        1. Validates file existence for path inputs
        2. Ensures required parameters are provided based on input/output types
        3. Handles file extension and MIME type detection
        4. Normalizes file extensions

        Raises
        ------
        AssertionError
            If any validation check fails with a descriptive error message
        """
        # Validate that file exists if input is a path
        if isinstance(self.img_input, (str, Path)):
            assert Path(self.img_input).exists(), (
                f"File {self.img_input} does not exist"
            )

        # For binary/array inputs with file output, require output path information
        if isinstance(
            self.img_input, (bytes, bytearray, np.ndarray)
        ) and self.output_format in (OutputFormat.PATH_STR, OutputFormat.FILE_PATH):
            assert self.output_dir is not None, (
                f"output_dir must be provided for {self.output_format} output format when img_input is {type(self.img_input).__name__}"
            )
            assert self.output_filename is not None, (
                f"output_filename must be provided for {self.output_format} output format when img_input is {type(self.img_input).__name__}"
            )

        # For numpy array with bytes output, require extension
        if (
            isinstance(self.img_input, np.ndarray)
            and self.output_format is OutputFormat.BYTES
        ):
            assert self.ext is not None, (
                f"ext must be provided for {self.output_format} output format when img_input is {type(self.img_input).__name__}"
            )

        # For memory-only outputs, output_dir should be None
        if self.output_format in (OutputFormat.BYTES, OutputFormat.NP_ARRAY):
            assert self.output_dir is None, (
                "output_dir must be None if output_format is BYTES or NP_ARRAY as no file is saved"
            )

        output_filename_provided = False

        # Handle output filename processing
        if self.output_filename is not None:
            assert self.ext is None, (
                "ext must be None if output_filename is provided (extension is taken from filename)"
            )
            output_filename_provided = True
            if isinstance(self.output_filename, str):
                self.output_filename = Path(self.output_filename)
            assert (
                self.output_filename.stem != "" and self.output_filename.suffix != ""
            ), (
                "output_filename must be a valid filename with non-empty name and extension"
            )
            self.ext = self.output_filename.suffix
        elif isinstance(self.img_input, (str, Path)):
            # Default output filename to input filename if none provided
            self.output_filename = (
                Path(self.img_input)
                if isinstance(self.img_input, str)
                else self.img_input
            )
            # Detect MIME type from input file if extension not specified
            if self.ext is None:
                self.mime = puremagic.from_file(self.output_filename, mime=True)

        # Handle bytes/bytearray input MIME type detection
        if isinstance(self.img_input, (bytes, bytearray)):
            raw = (
                bytes(self.img_input)
                if isinstance(self.img_input, bytearray)
                else self.img_input
            )
            if self.ext is None:
                self.mime = puremagic.from_string(raw, mime=True)

        # Process extension and MIME type relationships
        if self.ext is not None and self.mime is None:
            # Normalize extension format
            self.ext = self.ext.lower()
            self.ext = f".{self.ext}" if not self.ext.startswith(".") else self.ext
            # Infer MIME type from extension
            self.mime, _ = mimetypes.guess_type(f"dummy{self.ext}")
            assert self.mime is not None, (
                f"Invalid extension '{self.ext}' in output_filename provided"
                if output_filename_provided
                else f"Invalid extension '{self.ext}' provided"
            )

        # Validate MIME type is an image type
        if self.mime is not None:
            assert self.mime.startswith("image/"), (
                f"Invalid MIME type '{self.mime}' for extension '{self.ext}' in output_filename provided"
                if output_filename_provided
                else f"Invalid MIME type '{self.mime}' for extension '{self.ext}' provided"
            )
            # If MIME type is valid but no extension, get default extension for this MIME type
            if self.ext is None:
                self.ext = mimetypes.guess_extension(self.mime)

    def load(self):
        """
        Load image data from the provided input source.

        Supports loading from:
        - File paths (str or Path)
        - Binary data (bytes or bytearray)
        - NumPy arrays

        The loaded image is stored in the `image` attribute as a NumPy array.
        """
        if isinstance(self.img_input, (str, Path)):
            # Convert Path to string if needed for OpenCV
            image_path_str = (
                str(self.img_input)
                if isinstance(self.img_input, Path)
                else self.img_input
            )
            # Load image from file
            self.image = cv2.imread(image_path_str)
        elif isinstance(self.img_input, (bytes, bytearray)):
            # Convert binary data to numpy array
            arr = np.frombuffer(self.img_input, np.uint8)
            # Decode image from memory buffer
            self.image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        elif isinstance(self.img_input, np.ndarray):
            # Use numpy array directly
            self.image = (
                self.img_input.copy()
            )  # Create a copy to avoid modifying the original

    def get_corner_coordinates(self):
        """
        Detect the four corners of the document in the image.

        Uses edge detection and contour finding algorithms to identify
        the document boundaries. The result is stored in the `corners`
        attribute as a NumPy array of shape (4, 2) containing the (x, y)
        coordinates of the four corners.
        """
        self.corners = get_contour(self.image)

    def warp(self):
        """
        Apply perspective transformation to get a "top-down" view of the document.

        Uses the detected corners to compute a homography matrix and warp
        the image to a rectangular shape. This corrects perspective distortion
        and produces a flat, frontal view of the document.
        """
        # Apply the perspective transformation based on detected corners
        self.image = transform.four_point_transform(self.image, self.corners)

    def change_mode(self):
        """
        Convert the image to the specified color mode.

        If the mode is GRAYSCALE, converts the image from BGR to grayscale.
        If the mode is COLOR, the image remains unchanged.
        """
        if self.mode is Mode.GRAYSCALE:
            # Convert from BGR color space to single-channel grayscale
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

    def enhance(self):
        """
        Enhance the image quality using sharpening and thresholding techniques.

        For grayscale images:
        1. Apply unsharp masking for sharpening
        2. Apply adaptive thresholding for binarization

        For color images:
        1. Split into BGR channels
        2. Apply unsharp masking to each channel independently
        3. Merge the enhanced channels

        This improves readability and reduces noise in the scanned document.
        """
        if len(self.image.shape) == 2:
            # For grayscale images (single channel)

            # Sharpen image using unsharp masking technique
            # 1. Create a blurred version of the image
            sharpen = cv2.GaussianBlur(self.image, (0, 0), 3)
            # 2. Subtract the blurred image from the original with weights
            #    (1.5 * original - 0.5 * blurred = original + 0.5 * (original - blurred))
            sharpen = cv2.addWeighted(self.image, 1.5, sharpen, -0.5, 0)

            # Apply adaptive threshold to get a clean black and white effect
            # Adapts the threshold based on local neighborhood (21x21 pixels)
            # 15 is the constant subtracted from the weighted mean
            self.image = cv2.adaptiveThreshold(
                sharpen, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 15
            )
        else:
            # For color images (3 channels)

            # Split the image into its color channels
            b, g, r = cv2.split(self.image)
            sharpened_channels = []

            # Sharpen each channel independently using the same unsharp masking technique
            for ch in (b, g, r):
                blur = cv2.GaussianBlur(ch, (0, 0), 3)
                sharpen = cv2.addWeighted(ch, 1.5, blur, -0.5, 0)
                sharpened_channels.append(sharpen)

            # Recombine the sharpened channels into a color image
            self.image = cv2.merge(sharpened_channels)

    def save_image(self):
        """
        Save or prepare the processed image according to the specified output format.

        Returns
        -------
        Union[str, Path, bytes, np.ndarray]
            The processed image in the requested format:
            - For PATH_STR: Path to the saved image as a string
            - For FILE_PATH: Path to the saved image as a Path object
            - For BYTES: Image data as bytes
            - For NP_ARRAY: Image data as a NumPy array
        """
        if self.output_format in (OutputFormat.PATH_STR, OutputFormat.FILE_PATH):
            # Determine output directory, creating default if needed
            self.output_dir = (
                Path(self.output_dir)
                if self.output_dir is not None
                else Path(self.img_input).parent / "output"
            )
            # Create full output path
            output_filepath = self.output_dir / self.output_filename.name
            # Create output directory if it doesn't exist
            self.output_dir.mkdir(parents=True, exist_ok=True)
            # Save image to file using OpenCV
            cv2.imwrite(str(output_filepath), self.image)
            # Return according to requested format
            return (
                output_filepath
                if self.output_format is OutputFormat.FILE_PATH
                else str(output_filepath)
            )
        elif self.output_format is OutputFormat.BYTES:
            # Encode image to bytes using the specified extension
            _, buffer = cv2.imencode(self.ext, self.image)
            return buffer.tobytes()
        elif self.output_format is OutputFormat.NP_ARRAY:
            # Return the NumPy array directly
            return self.image

    def scan(
        self,
    ) -> Union[str, Path, bytes, np.ndarray]:
        """
        Execute the complete document scanning workflow.

        This method orchestrates the full document scanning process to convert
        a casual document photo into a professional-quality scan:
        1. Load the image from the input source
        2. Detect document corners
        3. Apply perspective transformation for a top-down view
        4. Convert to the specified color mode
        5. Enhance document quality and readability
        6. Save or return the processed document

        Returns
        -------
        Union[str, Path, bytes, np.ndarray]
            The professional-quality scanned document in the requested output format
        """
        # Step 1: Load the image from the provided input source
        self.load()

        # Step 2: Detect the document corners in the image
        self.get_corner_coordinates()

        # Step 3: Apply perspective transformation to get a "top-down" view
        self.warp()

        # Step 4: Convert to grayscale if specified
        self.change_mode()

        # Step 5: Enhance image quality with sharpening and thresholding
        self.enhance()

        # Step 6: Save or return the processed image in the requested format
        return self.save_image()
