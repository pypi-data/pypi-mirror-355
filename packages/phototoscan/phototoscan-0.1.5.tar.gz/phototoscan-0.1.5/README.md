# PhotoToScan

A Python library that converts casual document snapshots into professional-quality scanned documents.

This project makes use of the [OpenCV-Document-Scanner](https://github.com/andrewdcampbell/OpenCV-Document-Scanner) from [@andrewdcampbell](https://github.com/andrewdcampbell) and [@joaofauvel](https://github.com/joaofauvel), and the transform and imutils modules from [@PyImageSearch](https://github.com/PyImageSearch) (which can be accessed [here](http://www.pyimagesearch.com/2014/09/01/build-kick-ass-mobile-document-scanner-just-5-minutes/)).

## Environment

### [uv](https://github.com/astral-sh/uv) - An extremely fast Python package and project manager, written in Rust.

## Installation

```
pip install phototoscan
```

## How To Use It

### As a library

#### Examples

```python
from phototoscan import OutputFormat, Mode, Photo

# Basic usage with file path
photo = Photo(
    img_input="path/to/image.jpg",
    output_format=OutputFormat.PATH_STR,
    output_dir="path/to/output",  # optional
    mode=Mode.COLOR  # optional, defaults to COLOR
)
result = photo.scan()

# Advanced usage with various input and output types
# 1. From file path to file path string
photo = Photo(
    img_input="path/to/image.jpg",
    output_format=OutputFormat.PATH_STR,
    mode=Mode.GRAYSCALE  # Use grayscale mode instead of default color
)
path_str = photo.scan()

# 2. From file path to Path object
photo = Photo(
    img_input="path/to/image.jpg",
    output_format=OutputFormat.FILE_PATH
)
path_obj = photo.scan()

# 3. From numpy array to bytes
photo = Photo(
    img_input=numpy_array,
    output_format=OutputFormat.BYTES,
    ext=".jpg"  # required when input is numpy array and output is bytes
)
bytes_data = photo.scan()

# 4. From bytes to numpy array
photo = Photo(
    img_input=image_bytes,
    output_format=OutputFormat.NP_ARRAY
)
np_array = photo.scan()
```

#### Parameters:

- `img_input`: Can be a file path (str/Path), bytes/bytearray, or numpy array
- `output_format`: Determines the return type (OutputFormat.PATH_STR, OutputFormat.FILE_PATH, OutputFormat.BYTES, or OutputFormat.NP_ARRAY)
- `mode`: Optional. Determines the output style (Mode.COLOR or Mode.GRAYSCALE). Defaults to COLOR
- `output_dir`: Optional. Directory to save the output (required for file outputs when input is numpy array)
- `output_filename`: Optional. Name for the output file (required for file outputs when input isn't a file path)
- `ext`: Optional. File extension for output (required for bytes output when input is numpy array)

#### Notes:

- When providing a file path as input and not specifying an output directory, a folder named "output" will be created at the same level as the input image.
- Any specified output directory that doesn't exist will be created automatically.
- The `scan()` method executes the full document scanning workflow:
  1. Load the image from the input source
  2. Detect document corners
  3. Apply perspective transformation for a top-down view
  4. Convert to the specified color mode
  5. Enhance document quality and readability
  6. Save or return the processed document

### As a command-line tool

#### To scan a single image:

```bash
uvx phototoscan --image <IMG_PATH> --output-dir <OUTPUT_DIR> --mode <MODE>
```

- `--output-dir` is optional.

  - If not provided, a directory named output will be created next to the image file.
  - If the specified directory does not exist, it will be created automatically.

- `--mode` is optional. Can be either `color` or `grayscale` (default is `color`).

#### Scan all images in a directory

```bash
uvx phototoscan --images <IMG_DIR> --output-dir <OUTPUT_DIR> --mode <MODE>
```

- The same rules apply for `--output-dir` and `--mode` as above.
