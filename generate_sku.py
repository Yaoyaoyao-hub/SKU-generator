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

    def get_enhanced_prompt(self, reference_number: str, chinese_context: str = "") -> str:
        """Get the enhanced prompt template with SKU generation"""
        return f"""Analyze these product images and generate a detailed product description in the following format:

Reference Number: {reference_number}
SKU: [Generate SKU in format: BRAND_CATEGORY_MODEL_COLOR_REFERENCENUMBER]
Brand: [Brand Name]
Model: [Model Name]
Material: [Material Description]
Color: [Color Description,e.g., BLACK, WHITE, BEIGE, RED, BLUE, BROWN, PINK]
Size: [Size Information, provide mini,small,medium,large with the numbers]
Year of Production: [Year if identifiable]
Category: [Category, e.g. BAG, WATCH, SHOE...]
Sub-category: [Sub-category]
Condition Grade: [Condition Percentage]
Condition Description: [Detailed condition description]

Details:
- [Detailed observations about exterior, interior, hardware, etc.]

Accessories: [List any accessories]
Retail Price: [If known, with source URL]
Recommended Selling Price: [Price in GBP with source URLs for market research]

PRICING SOURCES: For any pricing information, you MUST provide ONLY real, verifiable URLs. DO NOT make up URLs.

SKU FORMAT RULES:
- Use format: BRAND_CATEGORY_MODEL_COLOR_REFERENCENUMBER
- BRAND: Clean brand name (e.g., CHANEL, LOUISVUITTON, HERMES, GUCCI)
- CATEGORY: product category (e.g., BAG, SHOE, WATCH)
- MODEL: Bag model (e.g., LEBOY, CLASSIC, FLAP, WOC, SPEEDYNANO, KELLY, BIRKIN)
- COLOR: Main color (e.g., BLACK, WHITE, BEIGE, RED, BLUE, BROWN, PINK)
- REFERENCENUMBER: The provided reference number

{chinese_context}

Please be thorough and accurate in your analysis."""

    def process_with_gemini_enhanced(self, image_paths: List[str], reference_number: str, 
                                   chinese_context: str = "", custom_prompt: str = None) -> str:
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

        # Use custom prompt or enhanced default
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = self.get_enhanced_prompt(reference_number, chinese_context)

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
        
        # Process with Gemini enhanced method
        description = self.process_with_gemini_enhanced(image_files, sku, "")
        
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
