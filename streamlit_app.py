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
from datetime import datetime
from generate_sku import SKUGenerator

# Page configuration
st.set_page_config(
    page_title="SKU Generator",
    page_icon="👜",
    layout="wide"
)

def extract_sku_from_description(description: str) -> str:
    """Extract SKU from the generated description"""
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
                'Image_Count', 'Folder_Path', 'Date_Added', 'Description_File'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

def extract_product_info_from_description(description: str) -> dict:
    """Extract structured product information from the description"""
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
        'Image_Count': '',
        'Folder_Path': '',
        'Date_Added': '',
        'Description_File': ''
    }
    
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
            'Image_Count', 'Folder_Path', 'Date_Added', 'Description_File'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow(product_info)

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
        
        # CSV tracking
        csv_path = get_csv_path(local_folder)
        create_csv_if_not_exists(csv_path)
        
        # Check if SKU already exists
        existing_skus = get_existing_skus(csv_path)
        if sku in existing_skus:
            return {
                "success": False,
                "error": f"SKU {sku} already exists in inventory. Please use a different reference number."
            }
        
        # Extract product information from description
        product_info = extract_product_info_from_description(description)
        
        # Add to CSV
        add_product_to_csv(csv_path, product_info, chinese_description, len(image_data), folder_path, description_filename)
        
        return {
            "success": True,
            "folder_path": folder_path,
            "folder_name": sku,
            "saved_files": saved_files,
            "total_files": len(saved_files),
            "csv_updated": True
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
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Choose product images",
            type=['jpg', 'jpeg', 'png', 'bmp', 'tiff'],
            accept_multiple_files=True,
            help="Upload multiple images of the product"
        )
        
        if uploaded_files:
            st.success(f"Uploaded {len(uploaded_files)} images")
            
            # Update ordered images when new files are uploaded
            if len(uploaded_files) != len(st.session_state.ordered_images):
                st.session_state.ordered_images = list(uploaded_files)
            
            # Image reordering interface
            st.subheader("🔄 Reorder Images")
            st.markdown("Arrange images in your preferred order for AI analysis.")
            
            # Display current order with better UX
            st.markdown("**📋 Current Image Order:**")
            
            # Create a more intuitive reordering interface
            for idx, uploaded_file in enumerate(st.session_state.ordered_images):
                col1_order, col2_order, col3_order = st.columns([1, 3, 1])
                
                with col1_order:
                    st.markdown(f"**{idx + 1}.**")
                
                with col2_order:
                    # Display image thumbnail
                    image = Image.open(uploaded_file)
                    st.image(image, caption=f"{uploaded_file.name}", width=150)
                
                with col3_order:
                    # Move buttons in a more compact layout
                    if idx > 0:
                        if st.button("⬆️", key=f"up_{idx}", help="Move up"):
                            st.session_state.ordered_images[idx], st.session_state.ordered_images[idx-1] = \
                                st.session_state.ordered_images[idx-1], st.session_state.ordered_images[idx]
                            st.rerun()
                    
                    if idx < len(st.session_state.ordered_images) - 1:
                        if st.button("⬇️", key=f"down_{idx}", help="Move down"):
                            st.session_state.ordered_images[idx], st.session_state.ordered_images[idx+1] = \
                                st.session_state.ordered_images[idx+1], st.session_state.ordered_images[idx]
                            st.rerun()
            
            # Reset and preview options
            col_reset, col_preview = st.columns(2)
            
            with col_reset:
                if st.button("🔄 Reset Order"):
                    st.session_state.ordered_images = list(uploaded_files)
                    st.rerun()
            
            with col_preview:
                if st.button("👁️ Preview All"):
                    st.markdown("**📸 Image Preview (Current Order):**")
                    preview_cols = st.columns(min(3, len(st.session_state.ordered_images)))
                    
                    for idx, uploaded_file in enumerate(st.session_state.ordered_images):
                        col_idx = idx % 3
                        with preview_cols[col_idx]:
                            image = Image.open(uploaded_file)
                            st.image(image, caption=f"Image {idx + 1}: {uploaded_file.name}", use_container_width=True)
    
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
                        
                        # Process with selected model
                        description = generator.process_with_gemini_enhanced(image_paths, reference_number, chinese_context)
                        
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
                    data=edited_description,
                    file_name=output_filename,
                    mime="text/plain"
                )
            
            with col_actions2:
                # Save to local folder button (only if enabled)
                if save_to_folder and local_folder and st.session_state.generated_sku:
                    if st.button("📁 Save to Local Folder", type="primary"):
                        with st.spinner("Saving to local folder..."):
                            save_result = save_to_local_folder(
                                st.session_state.generated_sku, 
                                st.session_state.image_data, 
                                edited_description, 
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
                                    st.success("📊 **Product added to inventory CSV!**")
                                
                                # Show folder structure
                                st.markdown("**📁 Folder Structure:**")
                                
                                # Determine file extensions for display
                                extensions = []
                                for img_data in st.session_state.image_data:
                                    if img_data.startswith(b'\xff\xd8\xff'):
                                        extensions.append('.jpg')
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
                st.rerun()
        
        # Show help information
        st.markdown("---")
        st.markdown("### 💡 Tips")
        st.markdown("""
        - **Best results**: Upload clear, high-quality images from multiple angles
        - **Image order**: Use the reorder buttons to arrange images in your preferred order
        - **Chinese description**: Provide detailed info about bag type, condition, material
        - **Gemini API Key**: Get Gemini key from [makersuite.google.com](https://makersuite.google.com/app/apikey)
        - **Supported formats**: JPG, PNG, BMP, TIFF
        - **Review & Edit**: Check the generated description and make modifications before saving
        - **File naming**: Output files are automatically named using the generated SKU
        - **Local folder**: Files are automatically saved with SKU-based naming when enabled
        """)

if __name__ == "__main__":
    main() 