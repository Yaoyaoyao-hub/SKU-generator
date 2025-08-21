#!/usr/bin/env python3
"""
Streamlit Interface for SKU Generator
Web app for generating product descriptions from images using LLM
"""

import streamlit as st
import os
import tempfile
from pathlib import Path
import base64
from PIL import Image
import io
import re
import shutil
import csv
import json
from datetime import datetime
from generate_sku import SKUGenerator
from prompts import get_enhanced_prompt

# Page configuration
st.set_page_config(
    page_title="SKU Generator",
    page_icon="👜",
    layout="wide"
)

def extract_sku_from_description(description) -> str:
    """Extract SKU from the generated description (supports both string and JSON)"""
    # Handle JSON response
    if isinstance(description, dict):
        if 'sku' in description:
            return description['sku']
        elif 'error' in description:
            return None
        else:
            return None
    
    # Handle string response (legacy support)
    if isinstance(description, str):
        lines = description.split('\n')
        for line in lines:
            if line.startswith("SKU:"):
                sku = line.replace("SKU:", "").strip()
                return sku
    
    return None

def get_csv_path(local_folder: str) -> str:
    """Get the path to the CSV file in the local folder"""
    return os.path.join(local_folder, "sku_inventory.csv")

def create_csv_if_not_exists(csv_path: str):
    """Create CSV file with headers if it doesn't exist"""
    if not os.path.exists(csv_path):
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'SKU', 'Reference_Number', 'Brand', 'Model', 'Material', 'Color', 
                'Size', 'Year_of_Production', 'Category', 'Sub_category', 
                'Condition_Grade', 'Condition_Description', 'Accessories',
                'Retail_Price', 'Recommended_Selling_Price', 'Chinese_Description',
                'Height', 'Width', 'Depth', 'Serial_Number', 'URLs',
                'Image_Count', 'Folder_Path', 'Date_Added', 'Description_File'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

def extract_product_info_from_description(description) -> dict:
    """Extract structured product information from the description (supports both string and JSON)"""
    info = {
        'SKU': '',
        'Reference_Number': '',
        'Brand': '',
        'Model': '',
        'Material': '',
        'Color': '',
        'Size': '',
        'Year_of_Production': '',
        'Category': '',
        'Sub_category': '',
        'Condition_Grade': '',
        'Condition_Description': '',
        'Accessories': '',
        'Retail_Price': '',
        'Recommended_Selling_Price': '',
        'Chinese_Description': '',
        'Height': '',
        'Width': '',
        'Depth': '',
        'Serial_Number': '',
        'URLs': '',
        'Image_Count': '',
        'Folder_Path': '',
        'Date_Added': '',
        'Description_File': ''
    }
    
    # Handle JSON response
    if isinstance(description, dict):
        if 'error' in description:
            return info  # Return empty info if there's an error
        
        # Map JSON fields to CSV fields
        info['SKU'] = description.get('sku', '')
        info['Reference_Number'] = description.get('reference_number', '')
        info['Brand'] = description.get('brand', '')
        info['Model'] = description.get('model', '')
        info['Material'] = description.get('material', '')
        info['Color'] = description.get('color', '')
        info['Size'] = description.get('size', '')
        info['Year_of_Production'] = description.get('year_of_production', '')
        info['Category'] = description.get('category', '')
        info['Sub_category'] = description.get('sub_category', '')
        info['Condition_Grade'] = description.get('condition_grade', '')
        info['Condition_Description'] = description.get('condition_description', '')
        info['Accessories'] = str(description.get('accessories', [])) if isinstance(description.get('accessories'), list) else description.get('accessories', '')
        info['Retail_Price'] = description.get('estimated_price_range', '')
        info['Recommended_Selling_Price'] = description.get('recommended_selling_price', '')
        
        # Add additional JSON fields that might be useful
        info['Height'] = description.get('height', '')
        info['Width'] = description.get('width', '')
        info['Depth'] = description.get('depth', '')
        info['Serial_Number'] = description.get('serial_number', '')
        info['URLs'] = str(description.get('urls', [])) if isinstance(description.get('urls'), list) else description.get('urls', '')
        
        return info
    
    # Handle string response (legacy support)
    if isinstance(description, str):
        lines = description.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('SKU:'):
                info['SKU'] = line.replace('SKU:', '').strip()
            elif line.startswith('Reference Number:'):
                info['Reference_Number'] = line.replace('Reference Number:', '').strip()
            elif line.startswith('Brand:'):
                info['Brand'] = line.replace('Brand:', '').strip()
            elif line.startswith('Model:'):
                info['Model'] = line.replace('Model:', '').strip()
            elif line.startswith('Material:'):
                info['Material'] = line.replace('Material:', '').strip()
            elif line.startswith('Color:'):
                info['Color'] = line.replace('Color:', '').strip()
            elif line.startswith('Size:'):
                info['Size'] = line.replace('Size:', '').strip()
            elif line.startswith('Year of Production:'):
                info['Year_of_Production'] = line.replace('Year of Production:', '').strip()
            elif line.startswith('Category:'):
                info['Category'] = line.replace('Category:', '').strip()
            elif line.startswith('Sub-category:'):
                info['Sub_category'] = line.replace('Sub-category:', '').strip()
            elif line.startswith('Condition Grade:'):
                info['Condition_Grade'] = line.replace('Condition Grade:', '').strip()
            elif line.startswith('Condition Description:'):
                info['Condition_Description'] = line.replace('Condition Description:', '').strip()
            elif line.startswith('Accessories:'):
                info['Accessories'] = line.replace('Accessories:', '').strip()
            elif line.startswith('Retail Price:'):
                info['Retail_Price'] = line.replace('Retail Price:', '').strip()
            elif line.startswith('Recommended Selling Price:'):
                info['Recommended_Selling_Price'] = line.replace('Recommended Selling Price:', '').strip()
    
    return info

def add_product_to_csv(csv_path: str, product_info: dict, chinese_description: str, 
                      image_count: int, folder_path: str, description_file: str):
    """Add a new product row to the CSV file"""
    # Add additional information
    product_info['Chinese_Description'] = chinese_description
    product_info['Image_Count'] = str(image_count)
    product_info['Folder_Path'] = folder_path
    product_info['Date_Added'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    product_info['Description_File'] = description_file
    
    # Append to CSV
    with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'SKU', 'Reference_Number', 'Brand', 'Model', 'Material', 'Color', 
            'Size', 'Year_of_Production', 'Category', 'Sub_category', 
            'Condition_Grade', 'Condition_Description', 'Accessories',
            'Retail_Price', 'Recommended_Selling_Price', 'Chinese_Description',
            'Height', 'Width', 'Depth', 'Serial_Number', 'URLs',
            'Image_Count', 'Folder_Path', 'Date_Added', 'Description_File'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow(product_info)

def auto_update_csv_inventory(local_folder: str, product_description: dict, chinese_description: str, 
                            image_count: int, folder_path: str, description_file: str):
    """Automatically update CSV inventory with new product, checking for duplicates"""
    csv_path = get_csv_path(local_folder)
    
    # Create CSV if it doesn't exist
    create_csv_if_not_exists(csv_path)
    
    # Read existing inventory to check for duplicates
    existing_products = []
    if os.path.exists(csv_path):
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            existing_products = list(reader)
    
    # Check for duplicate SKU
    sku = product_description.get('sku', '')
    for product in existing_products:
        if product.get('SKU') == sku:
            return {
                "success": False,
                "error": f"SKU {sku} already exists in inventory. Cannot overwrite existing product.",
                "existing_product": product
            }
    
    # Check for duplicate reference number
    reference_number = product_description.get('reference_number', '')
    for product in existing_products:
        if product.get('Reference_Number') == reference_number:
            return {
                "success": False,
                "error": f"Reference Number {reference_number} already exists in inventory. Cannot overwrite existing product.",
                "duplicate_reference": product
            }
    
    # Extract product information for CSV
    product_info = extract_product_info_from_description(product_description)
    
    # Add new product to CSV
    add_product_to_csv(csv_path, product_info, chinese_description, image_count, folder_path, description_file)
    
    return {
        "success": True,
        "message": f"Product {sku} successfully added to inventory CSV",
        "csv_path": csv_path,
        "total_products": len(existing_products) + 1
    }

def get_existing_skus(csv_path: str) -> set:
    """Get all existing SKUs from the CSV file"""
    existing_skus = set()
    if os.path.exists(csv_path):
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row.get('SKU'):
                    existing_skus.add(row['SKU'])
    return existing_skus

def save_to_local_folder(sku: str, image_data: list, description: str, output_file: str, local_folder: str, 
                        chinese_description: str = "", reference_number: str = ""):
    """Save files to local folder with SKU-based naming and CSV tracking"""
    try:
        # Create folder path
        folder_path = os.path.join(local_folder, sku)
        os.makedirs(folder_path, exist_ok=True)
        
        saved_files = []
        
        # Save description file with SKU-based naming
        description_filename = f"{sku}_description.txt"
        description_path = os.path.join(folder_path, description_filename)
        
        # Handle both string and JSON descriptions
        if isinstance(description, dict):
            # Save JSON as formatted text
            with open(description_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(description, indent=2, ensure_ascii=False))
        else:
            # Save string description as-is
            with open(description_path, 'w', encoding='utf-8') as f:
                f.write(description)
        
        saved_files.append({
            'name': description_filename,
            'path': description_path,
            'type': 'description'
        })
        
        # Save images from stored data
        for i, img_data in enumerate(image_data, 1):
            # Determine file extension based on image data
            if img_data.startswith(b'\xff\xd8\xff'):
                file_ext = '.jpg'
            elif img_data.startswith(b'\x89PNG'):
                file_ext = '.png'
            elif img_data.startswith(b'BM'):
                file_ext = '.bmp'
            elif img_data.startswith(b'II') or img_data.startswith(b'MM'):
                file_ext = '.tiff'
            elif img_data.startswith(b'RIFF') and img_data[8:12] == b'WEBP':
                file_ext = '.webp'
            else:
                file_ext = '.jpg'  # Default to jpg
            
            # Create new filename with SKU format
            new_filename = f"{sku}_{i}{file_ext}"
            new_path = os.path.join(folder_path, new_filename)
            
            # Write image data to file
            with open(new_path, "wb") as f:
                f.write(img_data)
            
            saved_files.append({
                'name': new_filename,
                'path': new_path,
                'type': 'image'
            })
        
        # CSV tracking - use automatic update function
        csv_result = auto_update_csv_inventory(local_folder, description, chinese_description, len(image_data), folder_path, description_filename)
        
        if not csv_result["success"]:
            return csv_result  # Return error if CSV update failed
        
        return {
            "success": True,
            "folder_path": folder_path,
            "folder_name": sku,
            "saved_files": saved_files,
            "total_files": len(saved_files),
            "csv_updated": True,
            "csv_message": csv_result["message"],
            "total_products": csv_result["total_products"]
        }
        
    except Exception as e:
        return {"error": f"Local save error: {str(e)}"}

def main():
    st.title("👜 SKU Generator")
    st.markdown("Generate detailed product descriptions from images using AI")
    
    # Initialize session state for storing generated description
    if 'generated_description' not in st.session_state:
        st.session_state.generated_description = ""
    if 'generated_sku' not in st.session_state:
        st.session_state.generated_sku = ""
    if 'image_paths' not in st.session_state:
        st.session_state.image_paths = []
    if 'image_data' not in st.session_state:
        st.session_state.image_data = []
    if 'show_review' not in st.session_state:
        st.session_state.show_review = False
    if 'ordered_images' not in st.session_state:
        st.session_state.ordered_images = []
    if 'show_order_info' not in st.session_state:
        st.session_state.show_order_info = False
    if 'show_preview' not in st.session_state:
        st.session_state.show_preview = False
    if 'selected_image_idx' not in st.session_state:
        st.session_state.selected_image_idx = None
    if 'confirm_remove_all' not in st.session_state:
        st.session_state.confirm_remove_all = False
    if 'drag_mode' not in st.session_state:
        st.session_state.drag_mode = False
    if 'uploader_key' not in st.session_state:
        st.session_state.uploader_key = 'default'
    
    # Debug: Show current session state
    if st.checkbox("🔍 Debug: Show Session State"):
        st.json({
            "ordered_images_count": len(st.session_state.ordered_images),
            "selected_image_idx": st.session_state.selected_image_idx,
            "confirm_remove_all": st.session_state.confirm_remove_all,
            "drag_mode": st.session_state.drag_mode,
            "uploader_key": st.session_state.uploader_key
        })
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # API Key input
        api_key = st.text_input(
            "Gemini API Key",
            type="password",
            help="Enter your Google Gemini API key"
        )
        
        # Reference number input
        reference_number = st.text_input(
            "Reference Number",
            value="JK01450072402",
            help="Enter the product reference number"
        )
        
        # Chinese description input
        chinese_description = st.text_area(
            "Chinese Description",
            height=100,
            help="Enter Chinese description of the bag (type, condition, etc.)",
            placeholder="例如：香奈儿 Le Boy 小号黑色小羊皮包包，成色很好，轻微使用痕迹..."
        )
        

        
        # Local folder save option
        save_to_folder = st.checkbox(
            "Save to Local Folder",
            value=False,
            help="Save renamed images and description to a local folder"
        )
        
        # Local folder path input
        local_folder = ""
        if save_to_folder:
            local_folder = st.text_input(
                "Local Folder Path",
                value=os.path.expanduser("~/Desktop/SKU_Generator"),
                help="Path to save the files (e.g., ~/Desktop/SKU_Generator)"
            )
            
            # Check if folder exists or can be created
            if local_folder:
                try:
                    os.makedirs(local_folder, exist_ok=True)
                    st.success(f"✅ Folder ready: {local_folder}")
                except Exception as e:
                    st.error(f"❌ Cannot create folder: {str(e)}")
        
        st.markdown("---")
        st.markdown("### Instructions")
        st.markdown("""
        1. Upload product images
        2. Enter Chinese description
        3. Configure Gemini API key
        4. Click 'Generate Description'
        5. Review and edit the description
        6. Save to local folder when satisfied
        7. Download the result (auto-named with SKU)
        """)
        
        # CSV Inventory Section
        if save_to_folder and local_folder:
            st.markdown("---")
            st.markdown("### 📊 Inventory Management")
            
            csv_path = get_csv_path(local_folder)
            if os.path.exists(csv_path):
                # Show inventory stats
                existing_skus = get_existing_skus(csv_path)
                st.info(f"📈 **Inventory Status:** {len(existing_skus)} products tracked")
                
                # Download CSV button
                if st.button("📥 Download Inventory CSV"):
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        csv_data = f.read()
                    st.download_button(
                        label="💾 Download CSV File",
                        data=csv_data,
                        file_name="sku_inventory.csv",
                        mime="text/csv"
                    )
                
                # Show recent entries
                if st.checkbox("👁️ Show Recent Entries"):
                    try:
                        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                            reader = csv.DictReader(csvfile)
                            rows = list(reader)
                            
                            if rows:
                                st.markdown("**📋 Recent Products:**")
                                # Show last 5 entries
                                for i, row in enumerate(rows[-5:], 1):
                                    st.markdown(f"**{i}.** {row.get('SKU', 'N/A')} - {row.get('Brand', 'N/A')} {row.get('Model', 'N/A')}")
                                    st.markdown(f"   📅 {row.get('Date_Added', 'N/A')} | 📸 {row.get('Image_Count', 'N/A')} images")
                            else:
                                st.info("No products in inventory yet.")
                    except Exception as e:
                        st.error(f"Error reading CSV: {str(e)}")
            else:
                st.info("📊 Inventory CSV will be created when you save your first product.")

    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📸 Upload Images")
        
        # File uploader with reset capability
        uploader_key = st.session_state.get('uploader_key', 'default')
        uploaded_files = st.file_uploader(
            "Choose product images",
            type=['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp'],
            accept_multiple_files=True,
            help="Upload multiple images of the product (supports JPG, PNG, BMP, TIFF, WebP)",
            key=uploader_key
        )
        
        # Add a reset uploader button
        if uploaded_files:
            col_reset, col_info = st.columns([1, 3])
            with col_reset:
                if st.button("🔄 Reset Uploader", help="Clear the file uploader to start fresh", type="secondary"):
                    st.session_state.uploader_key = f"reset_{datetime.now().timestamp()}"
                    st.session_state.ordered_images.clear()
                    st.session_state.selected_image_idx = None
                    st.session_state.confirm_remove_all = False
                    st.session_state.drag_mode = False
                    st.success("✅ File uploader has been reset!")
            with col_info:
                st.info("💡 Use 'Reset Uploader' to clear files and start over, or 'Remove All Images' to clear the grid but keep uploader state.")
        
        if uploaded_files:
            st.success(f"Uploaded {len(uploaded_files)} images")
            
            # Update ordered images when new files are uploaded
            if len(uploaded_files) != len(st.session_state.ordered_images):
                st.session_state.ordered_images = list(uploaded_files)
            
            # Image Grid Display and Reordering
            st.subheader("🖼️ Image Grid & Reordering")
            st.markdown("**Click on images to reorder them. Images are processed in the order shown below.**")
            
            # Remove All Images button in drag and drop area
            col_remove_all = st.columns([2, 1])
            
            with col_remove_all[0]:
                if st.button("🗑️ Remove All Images", help="Remove all images from the grid AND reset the file uploader", type="secondary"):
                    st.write(f"Debug: Current images count: {len(st.session_state.ordered_images)}")
                    if len(st.session_state.ordered_images) > 0:
                        if st.session_state.get('confirm_remove_all', False):
                            # User confirmed - remove all images
                            st.session_state.ordered_images.clear()
                            st.session_state.selected_image_idx = None
                            st.session_state.confirm_remove_all = False
                            st.session_state.drag_mode = False
                            # Reset the file uploader by changing its key
                            st.session_state.uploader_key = f"reset_{datetime.now().timestamp()}"
                            st.success("✅ All images removed successfully! File uploader has been reset.")
                            # Don't rerun - let the page refresh naturally
                        else:
                            # First click - show confirmation
                            st.session_state.confirm_remove_all = True
                            st.warning("⚠️ Click 'Remove All Images' again to confirm removing all images!")
                            # Don't rerun - let the page refresh naturally
                    else:
                        st.warning("⚠️ No images to remove")
            
            with col_remove_all[1]:
                if st.button("🧪 Test Session State", help="Test if session state is working"):
                    st.write(f"Test: Images count = {len(st.session_state.ordered_images)}")
                    st.write(f"Test: Selected index = {st.session_state.selected_image_idx}")
                    st.write(f"Test: Confirm remove = {st.session_state.confirm_remove_all}")
            
            # Display current order info if requested
            if st.session_state.get('show_order_info', False):
                st.info(f"📋 **Current Processing Order:** {', '.join([f'{i+1}.{f.name}' for i, f in enumerate(st.session_state.ordered_images)])}")
            
            # Show image count and debug info
            col_debug1, col_debug2 = st.columns([1, 1])
            
            with col_debug1:
                st.info(f"📸 **Total Images:** {len(st.session_state.ordered_images)}")
            
            with col_debug2:
                if st.session_state.selected_image_idx is not None:
                    st.info(f"🎯 **Selected:** {st.session_state.selected_image_idx + 1}")
                else:
                    st.info("🎯 **Selected:** None")
            
            # Warning if no images left
            if len(st.session_state.ordered_images) == 0:
                st.warning("⚠️ **No images uploaded.** Please upload images to continue.")
                return
            
            # Image Grid Display - Drag & Drop Simulation
            st.markdown("**🖼️ Image Grid (4 per row) - Drag & Drop Style Interface**")
            st.markdown("""
            **How to use (simulates drag & drop):**
            - **🎯 Pick Up**: Click image to select (gets elevated with shadow)
            - **📥 Drop**: Click destination to move image there
            - **🗑️ Remove All**: Use button above to remove all images at once
            """)
            
            # Initialize interaction state
            if 'selected_image_idx' not in st.session_state:
                st.session_state.selected_image_idx = None
            if 'drag_mode' not in st.session_state:
                st.session_state.drag_mode = False
            
            # Show selected image info with better visual feedback
            if st.session_state.selected_image_idx is not None:
                # Check if selected index is still valid after any removals
                if st.session_state.selected_image_idx < len(st.session_state.ordered_images):
                    selected_name = st.session_state.ordered_images[st.session_state.selected_image_idx].name
                    st.success(f"🎯 **PICKED UP:** Image {st.session_state.selected_image_idx + 1} - {selected_name}")
                    st.markdown("*Now click on another image to move it there, or click the same image to put it down*")
                    st.session_state.drag_mode = True
                else:
                    # Selected index is no longer valid, clear it
                    st.session_state.selected_image_idx = None
                    st.session_state.drag_mode = False
            else:
                st.session_state.drag_mode = False
            
            # Calculate grid layout dynamically (after any removals)
            images_per_row = 4
            total_images = len(st.session_state.ordered_images)
            num_rows = (total_images + images_per_row - 1) // images_per_row  # Ceiling division
            
            # Display images in grid with safety checks
            for row in range(num_rows):
                # Create columns for this row
                row_cols = st.columns(images_per_row)
                
                for col_idx in range(images_per_row):
                    image_idx = row * images_per_row + col_idx
                    
                    # Safety check: ensure index is still valid
                    if image_idx < len(st.session_state.ordered_images):
                        uploaded_file = st.session_state.ordered_images[image_idx]
                        
                        with row_cols[col_idx]:
                            # Enhanced visual feedback for drag & drop
                            is_selected = st.session_state.selected_image_idx == image_idx
                            is_drag_mode = st.session_state.drag_mode
                            
                            # Determine styling based on state
                            if is_selected:
                                # Picked up image - elevated appearance
                                border_color = "3px solid #4CAF50"
                                background_color = "#E8F5E8"
                                shadow = "0 8px 16px rgba(0,0,0,0.3)"
                                transform = "translateY(-5px)"
                            elif is_drag_mode and not is_selected:
                                # Drop target - subtle highlight
                                border_color = "2px dashed #2196F3"
                                background_color = "#F0F8FF"
                                shadow = "0 2px 8px rgba(33,150,243,0.2)"
                                transform = "none"
                            else:
                                # Normal state
                                border_color = "1px solid #ddd"
                                background_color = "#FFFFFF"
                                shadow = "0 2px 4px rgba(0,0,0,0.1)"
                                transform = "none"
                            
                            # Create enhanced container with drag & drop styling
                            st.markdown(f"""
                            <div style="
                                border: {border_color};
                                border-radius: 12px;
                                padding: 12px;
                                margin: 6px;
                                background-color: {background_color};
                                text-align: center;
                                cursor: pointer;
                                box-shadow: {shadow};
                                transform: {transform};
                                transition: all 0.3s ease;
                                position: relative;
                            ">
                            """, unsafe_allow_html=True)
                            
                            # Display image with enhanced caption
                            image = Image.open(uploaded_file)
                            caption_text = f"**{image_idx + 1}.** {uploaded_file.name[:20]}{'...' if len(uploaded_file.name) > 20 else ''}"
                            
                            if is_selected:
                                caption_text += " 🎯"
                            elif is_drag_mode and not is_selected:
                                caption_text += " 📥"
                            
                            st.image(
                                image, 
                                caption=caption_text, 
                                use_container_width=True
                            )
                            
                            # Action button integrated into image
                            if st.button(f"{'📥 Drop Here' if is_drag_mode and not is_selected else '🎯 Pick Up' if not is_selected else '🔄 Put Down'}", 
                                        key=f"action_{image_idx}", 
                                        help=f"{'Drop selected image here' if is_drag_mode and not is_selected else 'Select this image' if not is_selected else 'Deselect this image'}"):
                                
                                if not is_selected and not is_drag_mode:
                                    # Pick up this image
                                    st.session_state.selected_image_idx = image_idx
                                    st.rerun()
                                
                                elif is_selected:
                                    # Put down the image (deselect)
                                    st.session_state.selected_image_idx = None
                                    st.rerun()
                                
                                elif is_drag_mode and not is_selected:
                                    # Drop the selected image here
                                    idx1 = st.session_state.selected_image_idx
                                    idx2 = image_idx
                                    
                                    # Move the image to new position
                                    item = st.session_state.ordered_images.pop(idx1)
                                    st.session_state.ordered_images.insert(idx2, item)
                                    
                                    # Clear selection
                                    st.session_state.selected_image_idx = None
                                    # Don't rerun - let the page refresh naturally
                            

                            
                            st.markdown("</div>", unsafe_allow_html=True)
            
            # Preview section if requested
            if st.session_state.get('show_preview', False):
                st.markdown("---")
                st.markdown("**👁️ Processing Preview (Images will be analyzed in this order):**")
                
                # Show a compact preview of the order
                preview_text = " → ".join([f"{i+1}.{f.name[:15]}{'...' if len(f.name) > 15 else ''}" for i, f in enumerate(st.session_state.ordered_images)])
                st.info(f"📋 **Order:** {preview_text}")
                
                # Show processing flow
                st.markdown("**🔄 Processing Flow:**")
                for i, uploaded_file in enumerate(st.session_state.ordered_images):
                    st.markdown(f"{i+1}. **{uploaded_file.name}** → AI Analysis → SKU Generation")
    
    with col2:
        st.header("⚙️ Generation")
        
        if st.button("🚀 Generate Description", type="primary", disabled=not (uploaded_files and api_key)):
            if not uploaded_files:
                st.error("Please upload at least one image")
                return
            if not api_key:
                st.error("Please enter your API key")
                return
            
            try:
                with st.spinner("Processing images with AI..."):
                    # Create temporary directory for images
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Save uploaded files to temp directory using ordered images
                        image_paths = []
                        image_data = [] # Store image data in session state
                        for uploaded_file in st.session_state.ordered_images:
                            temp_path = os.path.join(temp_dir, uploaded_file.name)
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            image_paths.append(temp_path)
                            # Read image data and store in session state
                            image_data.append(uploaded_file.getvalue())
                        
                        # Store image paths and data in session state for later use
                        st.session_state.image_paths = image_paths
                        st.session_state.image_data = image_data
                        
                        # Initialize SKU Generator
                        generator = SKUGenerator(model_type="gemini", api_key=api_key)
                        
                        # Create enhanced prompt with Chinese description
                        chinese_context = ""
                        if chinese_description:
                            chinese_context = f"""

CHINESE DESCRIPTION PROVIDED:
{chinese_description}

Please use this Chinese description to enhance your analysis and provide more accurate details about the bag type, condition, and specifications."""
                        
                        # Process with default enhanced prompt
                        formatted_prompt = get_enhanced_prompt().format(
                            chinese_context=chinese_context
                        )
                        description = generator.process_with_gemini_enhanced(image_paths, reference_number, chinese_context, formatted_prompt)
                        
                        # Store generated description in session state
                        st.session_state.generated_description = description
                        st.session_state.generated_sku = extract_sku_from_description(description)
                        st.session_state.show_review = True
                        
                        st.success("✅ Description generated successfully!")
                        st.rerun()
                        
            except Exception as e:
                st.error(f"❌ Error generating description: {str(e)}")
                st.exception(e)
        
        # Show review and edit section if description was generated
        if st.session_state.show_review and st.session_state.generated_description:
            st.markdown("---")
            st.header("📝 Review & Edit Description")
            
            if st.session_state.generated_sku:
                st.info(f"🏷️ **Generated SKU:** {st.session_state.generated_sku}")
            
            # Handle JSON vs string description display
            if isinstance(st.session_state.generated_description, dict):
                # JSON response - display in a structured format
                st.subheader("📊 Generated Product Information")
                
                # Display SKU
                if st.session_state.generated_sku:
                    edited_sku = st.text_input(
                        "SKU (Editable)",
                        value=st.session_state.generated_sku,
                        help="Edit the SKU if needed. This will be used for file naming and CSV tracking."
                    )
                    
                    # Update the SKU in the generated description if it was changed
                    if edited_sku != st.session_state.generated_sku:
                        st.session_state.generated_sku = edited_sku
                        if isinstance(st.session_state.generated_description, dict):
                            st.session_state.generated_description['sku'] = edited_sku
                
                # Display JSON data in a readable format
                json_display = json.dumps(st.session_state.generated_description, indent=2, ensure_ascii=False)
                edited_json = st.text_area(
                    "Edit Product Information (JSON format)",
                    value=json_display,
                    height=400,
                    help="Review and modify the JSON data. SKU will remain unchanged."
                )
                
                # Try to parse edited JSON
                try:
                    edited_description = json.loads(edited_json)
                    # Preserve the SKU
                    if st.session_state.generated_sku:
                        edited_description['sku'] = st.session_state.generated_sku
                    st.session_state.generated_description = edited_description
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON format. Please check your edits.")
                    edited_description = st.session_state.generated_description
                
            else:
                # String response (legacy support)
                # Split description into SKU line and content
                lines = st.session_state.generated_description.split('\n')
                sku_line = ""
                description_content = []
                
                for line in lines:
                    if line.startswith("SKU:"):
                        sku_line = line
                    else:
                        description_content.append(line)
                
                # Display SKU line as read-only
                st.text_input(
                    "SKU (Read-only)",
                    value=sku_line,
                    disabled=True,
                    help="SKU is automatically generated and cannot be edited"
                )
                
                # Editable text area for the description content only
                content_text = '\n'.join(description_content).strip()
                edited_content = st.text_area(
                    "Edit Product Description (SKU excluded)",
                    value=content_text,
                    height=400,
                    help="Review and modify the description content. SKU will remain unchanged."
                )
                
                # Reconstruct the full description with original SKU and edited content
                edited_description = f"{sku_line}\n{edited_content}" if sku_line else edited_content
                
                # Update session state with edited description
                st.session_state.generated_description = edited_description
            
            # Action buttons
            col_actions1, col_actions2 = st.columns(2)
            
            with col_actions1:
                # Download button
                if st.session_state.generated_sku:
                    output_filename = f"{st.session_state.generated_sku}_description.txt"
                else:
                    output_filename = "generated_sku.txt"
                
                st.download_button(
                    label="📥 Download Description",
                    data=json.dumps(edited_description, indent=2, ensure_ascii=False),
                    file_name=output_filename,
                    mime="text/plain"
                )
            
            with col_actions2:
                # Save to local folder button (only if enabled)
                if save_to_folder and local_folder and st.session_state.generated_sku:
                    if st.button("📁 Save to Local Folder", type="primary"):
                        with st.spinner("Saving to local folder..."):
                            # Use the current SKU (which may have been edited)
                            current_sku = st.session_state.generated_sku
                            save_result = save_to_local_folder(
                                current_sku, 
                                st.session_state.image_data, 
                                edited_description,  # Pass the JSON dict directly
                                output_filename, 
                                local_folder,
                                chinese_description,
                                reference_number
                            )
                            if save_result.get("success"):
                                st.success(f"✅ Saved to local folder!")
                                st.info(f"📁 Folder: {save_result['folder_path']}")
                                st.info(f"📄 Files saved: {save_result['total_files']}")
                                for file in save_result['saved_files']:
                                    if file['type'] == 'image':
                                        st.info(f"📸 Image: {file['name']}")
                                    elif file['type'] == 'description':
                                        st.info(f"📄 Description: {file['name']}")
                                
                                # CSV tracking confirmation
                                if save_result.get("csv_updated"):
                                    st.success(f"📊 **{save_result.get('csv_message', 'Product added to inventory CSV!')}**")
                                    st.info(f"📈 **Total Products in Inventory:** {save_result.get('total_products', 'N/A')}")
                                
                                # Show folder structure
                                st.markdown("**📁 Folder Structure:**")
                                
                                # Determine file extensions for display
                                extensions = []
                                for img_data in st.session_state.image_data:
                                    if img_data.startswith(b'\xff\xd8\xff'):
                                        extensions.append('.jpg')
                                    elif img_data.startswith(b'RIFF') and img_data[8:12] == b'WEBP':
                                        extensions.append('.webp')
                                    elif img_data.startswith(b'\x89PNG'):
                                        extensions.append('.png')
                                    elif img_data.startswith(b'BM'):
                                        extensions.append('.bmp')
                                    elif img_data.startswith(b'II') or img_data.startswith(b'MM'):
                                        extensions.append('.tiff')
                                    else:
                                        extensions.append('.jpg')
                                
                                structure_lines = [f"{save_result['folder_name']}/"]
                                structure_lines.append(f"├── {st.session_state.generated_sku}_description.txt")
                                
                                for i, ext in enumerate(extensions, 1):
                                    if i == len(extensions):
                                        structure_lines.append(f"└── {st.session_state.generated_sku}_{i}{ext}")
                                    else:
                                        structure_lines.append(f"├── {st.session_state.generated_sku}_{i}{ext}")
                                
                                st.code('\n'.join(structure_lines))
                                
                                # Clear all data for next product
                                st.markdown("---")
                                st.success("🎉 **Product processed successfully! Ready for next product.**")
                                
                                # Clear session state for fresh start
                                st.session_state.show_review = False
                                st.session_state.generated_description = ""
                                st.session_state.generated_sku = ""
                                st.session_state.image_paths = []
                                st.session_state.image_data = []
                                st.session_state.ordered_images = []
                                st.session_state.show_order_info = False
                                st.session_state.show_preview = False
                                st.session_state.selected_image_idx = None
                                st.session_state.confirm_remove_all = False
                                st.session_state.drag_mode = False
                                
                                # Clear file uploader by rerunning
                                st.rerun()
                            else:
                                st.error(f"❌ Save failed: {save_result['error']}")
                elif save_to_folder and not st.session_state.generated_sku:
                    st.warning("⚠️ Cannot save: SKU not found in description")
                elif save_to_folder and not local_folder:
                    st.warning("⚠️ Cannot save: No folder path specified")
                elif not save_to_folder:
                    st.info("💡 Enable 'Save to Local Folder' in sidebar to save files")
            
            # Reset button
            if st.button("🔄 Generate New Description"):
                st.session_state.show_review = False
                st.session_state.generated_description = ""
                st.session_state.generated_sku = ""
                st.session_state.image_paths = []
                st.session_state.image_data = []
                st.session_state.ordered_images = []
                st.session_state.show_order_info = False
                st.session_state.show_preview = False
                st.session_state.selected_image_idx = None
                st.session_state.confirm_remove_all = False
                st.session_state.drag_mode = False
                st.rerun()
        
        # Show help information
        st.markdown("---")
        st.markdown("### 💡 Tips")
        st.markdown("""
        - **Best results**: Upload clear, high-quality images from multiple angles
        - **Image order**: Use the reorder buttons to arrange images in your preferred order
        - **Chinese description**: Provide detailed info about bag type, condition, material
        - **Gemini API Key**: Get Gemini key from [makersuite.google.com](https://makersuite.google.com/app/apikey)
        - **Supported formats**: JPG, PNG, BMP, TIFF, WebP
        - **Review & Edit**: Check the generated description and make modifications before saving
        - **File naming**: Output files are automatically named using the generated SKU
        - **Local folder**: Files are automatically saved with SKU-based naming when enabled
        """)

if __name__ == "__main__":
    main() 
