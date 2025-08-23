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

# Import prompt template
from prompts import get_enhanced_prompt

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

    def process_with_gemini_enhanced(self, image_paths: List[str], reference_number: str, 
                                   chinese_context: str = "", custom_prompt: str = None) -> dict:
        """Process images with Google Gemini Pro Vision with enhanced Chinese context"""
        # Load images
        images = []
        for img_path in image_paths:  # Limit to 5 images
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
            prompt = get_enhanced_prompt(chinese_context)

        # Generate content
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content([prompt] + images)
        
        # Try to parse JSON response
        try:
            # Clean the response text to extract JSON
            response_text = response.text.strip()
            
            # Find JSON content (remove any text before or after JSON)
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_text = response_text[start_idx:end_idx]
                parsed_json = json.loads(json_text)
                
                # Add reference number to the JSON
                parsed_json["reference_number"] = reference_number
                
                # Generate and add SKU to the JSON
                sku = self.generate_sku_from_json(parsed_json, reference_number)
                parsed_json["sku"] = sku
                
                return parsed_json
            else:
                raise ValueError("No JSON object found in response")
        
        
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse JSON response: {e}")
            print(f"Raw response: {response.text}")
            # Return a structured error response
            return {
                "error": "Failed to parse JSON response",
                "raw_response": response.text,
                "reference_number": reference_number,
                "sku": f"error-error-error-error-error-{reference_number}".lower()
            }
        except Exception as e:
            print(f"Error processing response: {e}")
            return {
                "error": f"Error processing response: {str(e)}",
                "reference_number": reference_number,
                "sku": f"error-error-error-error-error-{reference_number}".lower()
            }

    def generate_sku_from_json(self, json_data: dict, reference_number: str) -> str:
        """Generate SKU from JSON data in format: color-material-model-brand-subcategory-reference_number"""
        try:
            # Extract required fields, with fallbacks for missing data
            color = json_data.get("color", "unknown").lower().replace(" ", "-")
            material = json_data.get("material", "unknown").lower().replace(" ", "-")
            model = json_data.get("model", "unknown").lower().replace(" ", "_")
            brand = json_data.get("brand", "unknown").lower().replace(" ", "-")
            sub_category = json_data.get("sub_category", "unknown").lower().replace(" ", "-")
            
            # Clean up values (remove special characters, normalize)
            color = "".join(c for c in color if c.isalnum() or c == "-")
            material = "".join(c for c in material if c.isalnum() or c == "-")
            model = "".join(c for c in model if c.isalnum() or c == "-")
            brand = "".join(c for c in brand if c.isalnum() or c == "-")
            sub_category = "".join(c for c in sub_category if c.isalnum() or c == "-")
            
            # Generate SKU in the specified format
            sku = f"{color}-{material}-{model}-{brand}-{sub_category}-{reference_number}"
            
            return sku.lower()
            
        except Exception as e:
            print(f"Warning: Error generating SKU: {e}")
            # Return a fallback SKU
            return f"unknown-unknown-unknown-unknown-unknown-{reference_number}".lower()

    def generate_sku_description(self, folder_path: str, output_file: str):
        """Generate SKU description from images in the folder"""
        folder = Path(folder_path)
        
        # Get all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
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
        result = self.process_with_gemini_enhanced(image_files, sku, "")
        
        # Save to output file
        if output_file.endswith('.json'):
            # Save as JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        else:
            # Save as formatted text
            with open(output_file, 'w', encoding='utf-8') as f:
                if isinstance(result, dict):
                    f.write(json.dumps(result, indent=2, ensure_ascii=False))
                else:
                    f.write(str(result))
        
        print(f"Generated description saved to: {output_file}")
        return result


def main():
    parser = argparse.ArgumentParser(description="Generate SKU descriptions from images using Google Gemini")
    parser.add_argument("--folder", required=True, help="Path to folder containing images")
    parser.add_argument("--api-key", required=True, help="Google Gemini API key")
    parser.add_argument("--output", default="generated_sku.json", help="Output file path (recommended: .json extension)")
    
    args = parser.parse_args()
    
    try:
        generator = SKUGenerator("gemini", args.api_key)
        description = generator.generate_sku_description(args.folder, args.output)
        
        print("\nGenerated Description:")
        print("=" * 50)
        if isinstance(description, dict):
            print(json.dumps(description, indent=2, ensure_ascii=False))
        else:
            print(description)
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 
