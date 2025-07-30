# SKU Generator Script

A simple Python script that processes product images with LLM models (Google Gemini Pro Vision) to generate detailed product descriptions.

## Features

- Supports Google Gemini Pro Vision
- Processes multiple images from a folder
- Generates structured product descriptions
- Outputs results to a text file
- Handles various image formats (JPEG, PNG, BMP, TIFF)

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python generate_sku.py --folder /path/to/image/folder --api-key YOUR_API_KEY
```

### Parameters

- `--folder`: Path to the folder containing product images (required)
- `--model`: LLM model to use - "gemini" (required)
- `--api-key`: API key for the selected model (required)
- `--output`: Output file path (optional, defaults to "generated_sku.txt")

### Examples


#### Using Google Gemini Pro Vision:
```bash
python generate_sku.py \
  --folder "/Users/yaogong-flylane/google-drive/CHANEL_LEBOY_BLACK_JK01450072402" \
  --model gemini \
  --api-key "your-gemini-api-key" \
  --output "chanel_leboy_description.txt"
```

## Output Format

The script generates a structured product description including:

- SKU (extracted from folder name)
- Brand and Model information
- Material and Color details
- Size specifications
- Production year (if identifiable)
- Condition assessment
- Detailed observations
- Pricing recommendations
- Reference numbers

## API Keys

### Google Gemini
Get your API key from: https://makersuite.google.com/app/apikey

## Notes

- The script processes all image files in the specified folder
- Images are sorted alphabetically for consistent processing
- The SKU is automatically extracted from the folder name
- The script supports JPEG, PNG, BMP, and TIFF image formats 
