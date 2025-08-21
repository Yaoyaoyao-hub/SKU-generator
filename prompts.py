#!/usr/bin/env python3
"""
Prompt templates for SKU generation
"""

def get_enhanced_prompt(chinese_context: str = "") -> str:
    """Get the enhanced prompt template with SKU generation"""
    return """Analyze these product images and generate a detailed product description in VALID JSON format.

IMPORTANT: You MUST respond with ONLY valid JSON. Do not include any text before or after the JSON.

The JSON should have the following structure:
{{
    "category": "Category, e.g. bag, watch, shoe...",
    "sub_category": "Sub-category, e.g., handbag, wallet, etc.",
    "brand": "Brand Name",
    "model": "Model Name",
    "material": "Material Description, e.g., leather, cotton, polyester, etc.",
    "color": "Color Description, e.g., black, white, beige, red, blue, brown, pink",
    "size": "Size Information, provide mini,small,medium,large",
    "height": "Height in inches",
    "width": "Width in inches",
    "depth": "Depth in inches",
    "serial_number": "Serial Number if identifiable",
    "year_of_production": "Year if identifiable",
    "condition_grade": "Condition Percentage",
    "condition_description": "Detailed condition description, include detailed observations about exterior, interior, hardware, etc",
    "accessories": ["List any accessories"],
    "estimated_price_range": "The price range in GBP for good condition product",
    "urls": ["The source urls for the estimated price range"],
    "recommended_selling_price": "Price in GBP"
}}

{chinese_context}

Please be thorough and accurate in your analysis, and ensure all sources for the estimated price range are provided with working URLs. Respond ONLY with the JSON object."""
