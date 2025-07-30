#!/usr/bin/env python3
"""
SKU Generator Script
Processes images with Google Gemini Pro Vision to generate product descriptions
"""

import os
import argparse
import base64
from pathlib import Path
from typing import List, Optional
import json

# Google Gemini imports
try:
    import google.generativeai as genai
    from PIL import Image
except ImportError:
    genai = None
    Image = None


class SKUGenerator:
    def __init__(self, model_type: str, api_key: str):
        self.model_type = model_type.lower()
        self.api_key = api_key
        
        if self.model_type == "gemini":
            if not genai or not Image:
                raise ImportError("Google Generative AI and PIL libraries not installed. Run: pip install google-generativeai pillow")
            genai.configure(api_key=api_key)
        else:
            raise ValueError("Model type must be 'gemini'")

    def process_with_gemini(self, image_paths: List[str], sku: str) -> str:
        """Process images with Google Gemini Pro Vision"""
        # Load images
        images = []
        for img_path in image_paths:
            img = Image.open(img_path)
            images.append(img)

        # Create prompt
        prompt = f"""Analyze these product images and generate a detailed product description in the following format:

SKU: {sku}
Brand: [Brand Name]
Model: [Model Name]
Material: [Material Description]
Color: [Color Description]
Size: [Size Information]
Year of Production: [Year if identifiable]
Category: [Category]
Sub-category: [Sub-category]
Condition Grade: [Condition Percentage]
Condition Description: [Detailed condition description]

Details:
- [Detailed observations about exterior, interior, hardware, etc.]

Accessories: [List any accessories]
Retail Price: [If known, with source URL]
Recommended Selling Price: [Price in GBP and JPY with source URLs for market research]
Reference Number: [Reference number if visible]

PRICING SOURCES: For any pricing information, you MUST provide ONLY real, verifiable URLs from these specific sources:
- Chanel official website: https://www.chanel.com
- Farfetch: https://www.farfetch.com
- Net-a-Porter: https://www.net-a-porter.com
- The RealReal: https://www.therealreal.com
- Vestiaire Collective: https://www.vestiairecollective.com
- Christie's: https://www.christies.com
- Sotheby's: https://www.sothebys.com

DO NOT make up URLs. If you cannot find a specific product page, state "Source: [Website name] - similar products available" or "Market research based on comparable items."

Please be thorough and accurate in your analysis."""

        # Generate content
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content([prompt] + images)
        
        return response.text

    def process_with_gemini_enhanced(self, image_paths: List[str], reference_number: str, chinese_context: str = "") -> str:
        """Process images with Google Gemini Pro Vision with enhanced Chinese context"""
        # Load images
        images = []
        for img_path in image_paths[:5]:  # Limit to 5 images
            try:
                img = Image.open(img_path)
                images.append(img)
            except Exception as e:
                print(f"Warning: Could not process image {img_path}: {e}")
                continue

        # Create prompt
        prompt = f"""Analyze these product images and generate a detailed product description in the following format:

Reference Number: {reference_number}
SKU: [Generate SKU in format: BRAND_MODELTYPE_COLOR_REFERENCENUMBER]
Brand: [Brand Name]
Model: [Model Name]
Material: [Material Description]
Color: [Color Description]
Size: [Size Information]
Year of Production: [Year if identifiable]
Category: [Category]
Sub-category: [Sub-category]
Condition Grade: [Condition Percentage]
Condition Description: [Detailed condition description]

Details:
- [Detailed observations about exterior, interior, hardware, etc.]

Accessories: [List any accessories]
Retail Price: [If known, with source URL]
Recommended Selling Price: [Price in GBP and JPY with source URLs for market research]

PRICING SOURCES: For any pricing information, you MUST provide ONLY real, verifiable URLs from these specific sources:
- Chanel official website: https://www.chanel.com
- Farfetch: https://www.farfetch.com
- Net-a-Porter: https://www.net-a-porter.com
- The RealReal: https://www.therealreal.com
- Vestiaire Collective: https://www.vestiairecollective.com
- Christie's: https://www.christies.com
- Sotheby's: https://www.sothebys.com

DO NOT make up URLs. If you cannot find a specific product page, state "Source: [Website name] - similar products available" or "Market research based on comparable items."

SKU FORMAT RULES:
- Use format: BRAND_MODELTYPE_COLOR_REFERENCENUMBER
- BRAND: Clean brand name (e.g., CHANEL, LOUISVUITTON, HERMES, GUCCI)
- MODELTYPE: Bag type (e.g., LEBOY, CLASSIC, FLAP, WOC, SPEEDY, KELLY, BIRKIN)
- COLOR: Main color (e.g., BLACK, WHITE, BEIGE, RED, BLUE, BROWN, PINK)
- REFERENCENUMBER: The provided reference number

{chinese_context}

Please be thorough and accurate in your analysis."""

        # Generate content
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content([prompt] + images)
        
        return response.text

    def generate_sku_description(self, folder_path: str, output_file: str):
        """Generate SKU description from images in the folder"""
        folder = Path(folder_path)
        
        # Get all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        image_files = []
        
        for file in folder.iterdir():
            if file.suffix.lower() in image_extensions:
                image_files.append(str(file))
        
        if not image_files:
            raise ValueError(f"No image files found in {folder_path}")
        
        # Sort images by name for consistent processing
        image_files.sort()
        
        # Extract SKU from folder name
        sku = folder.name
        
        print(f"Processing {len(image_files)} images for SKU: {sku}")
        print(f"Images: {', '.join([Path(f).name for f in image_files])}")
        
        # Process with Gemini
        description = self.process_with_gemini(image_files, sku)
        
        # Save to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(description)
        
        print(f"Generated description saved to: {output_file}")
        return description


def main():
    parser = argparse.ArgumentParser(description="Generate SKU descriptions from images using Google Gemini")
    parser.add_argument("--folder", required=True, help="Path to folder containing images")
    parser.add_argument("--api-key", required=True, help="Google Gemini API key")
    parser.add_argument("--output", default="generated_sku.txt", help="Output file path")
    
    args = parser.parse_args()
    
    try:
        generator = SKUGenerator("gemini", args.api_key)
        description = generator.generate_sku_description(args.folder, args.output)
        
        print("\nGenerated Description:")
        print("=" * 50)
        print(description)
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 