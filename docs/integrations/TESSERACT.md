# Tesseract OCR Integration

The NOVA Vision Engine utilizes **Tesseract OCR** (via `pytesseract`) as its primary deterministic text extraction engine.

## Why Tesseract?
- **Local Processing**: Processes images completely locally without hitting cloud APIs, ensuring data privacy and zero network latency.
- **Bounding Boxes**: Provides pixel-perfect coordinate mapping for text, which is critical for mapping Execution Engine target clicks to exact screen locations.
- **Confidence Scores**: Allows the Vision Engine to filter out noise by only keeping bounding boxes with high confidence.

## Installation Requirements
Because `pytesseract` is a Python wrapper, it requires the actual Tesseract C++ executable to be installed on the host operating system.

### Windows
1. Download the Tesseract installer for Windows (e.g., from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)).
2. Install it. By default, it installs to `C:\Program Files\Tesseract-OCR\`.
3. Add the installation directory to your system `PATH`, OR set it explicitly in Python:
   ```python
   import pytesseract
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

### Troubleshooting
- **`TesseractNotFoundError`**: This means `pytesseract` cannot find `tesseract.exe` in your system's PATH. 

## Preprocessing Pipeline
To maximize Tesseract accuracy, images are run through our OpenCV `ImagePreprocessor` before extraction:
1. **Grayscale**: Converted from BGR to grayscale.
2. **Adaptive Thresholding**: Binarized (black text on white background) using a Gaussian threshold to eliminate shadows and background noise.

## Extraction Data
The Vision Engine uses `pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)` to receive structured output, pulling:
- `text`: The recognized string.
- `left`, `top`, `width`, `height`: The bounding box.
- `conf`: Confidence score (converted to 0.0 - 1.0).
