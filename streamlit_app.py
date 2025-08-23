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
from google_drive_integration import GoogleDriveIntegration, GOOGLE_DRIVE_AVAILABLE

# =============================================================================
# CONSTANTS AND CONFIGURATION
# =============================================================================

# CSV field names - defined once to avoid duplication
CSV_FIELDS = [
    'SKU', 'Reference_Number', 'Brand', 'Model', 'Material', 'Color', 
    'Size', 'Year_of_Production', 'Category', 'Sub_category', 'Pattern',
    'Condition_Grade', 'Condition_Description', 'Accessories',
    'Retail_Price', 'Recommended_Selling_Price', 'Chinese_Description',
    'Height', 'Width', 'Depth', 'Serial_Number', 'URLs',
    'Image_Count', 'Folder_Path', 'Date_Added', 'Description_File'
]

# Image type options for user selection
IMAGE_TYPE_OPTIONS = [
    "",  # Empty/default option
    "front",
    "back", 
    "inside",
    "hardware",
    "serial_number",
    "custom"
]

# Page configuration
st.set_page_config(
    page_title="SKU Generator",
    page_icon="👜",
    layout="wide"
)

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def extract_sku_from_description(description) -> str:
    """Extract SKU from the generated description (supports both string and JSON)"""
    if isinstance(description, dict):
        return description.get('sku') if 'sku' in description else None
    return None

def get_csv_path(local_folder: str) -> str:
    """Get the path to the CSV file in the local folder"""
    return os.path.join(local_folder, "sku_inventory.csv")

def create_csv_if_not_exists(csv_path: str):
    """Create CSV file with headers if it doesn't exist"""
    if not os.path.exists(csv_path):
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDS)
            writer.writeheader()

def get_file_extension(image_data: bytes) -> str:
    """Determine file extension based on image data"""
    if image_data.startswith(b'\xff\xd8\xff'):
        return '.jpg'
    elif image_data.startswith(b'\x89PNG'):
        return '.png'
    elif image_data.startswith(b'BM'):
        return '.bmp'
    elif image_data.startswith(b'II') or image_data.startswith(b'MM'):
        return '.tiff'
    elif image_data.startswith(b'RIFF') and image_data[8:12] == b'WEBP':
        return '.webp'
    else:
        return '.jpg'  # Default to jpg

def create_empty_product_info() -> dict:
    """Create an empty product info dictionary with all CSV fields"""
    return {field: '' for field in CSV_FIELDS}

def render_image_type_selector(image_idx: int, uploaded_file) -> str:
    """Render an image type selector for a specific image"""
    # Create a unique key based on filename only (not position)
    image_key = uploaded_file.name
    
    # Get current image type from session state
    current_type = st.session_state.image_types.get(image_key, "")
    
    # Create the selector
    selected_type = st.selectbox(
        "Image Type:",
        options=IMAGE_TYPE_OPTIONS,
        index=IMAGE_TYPE_OPTIONS.index(current_type) if current_type in IMAGE_TYPE_OPTIONS else 0,
        key=f"type_selector_{image_key}",
        help="Select the type of this image (front, back, inside, hardware, serial number, or custom)"
    )
    
    # Update session state using filename as key
    st.session_state.image_types[image_key] = selected_type
    
    return selected_type

# =============================================================================
# CSV OPERATIONS
# =============================================================================

def extract_product_info_from_description(description) -> dict:
    """Extract structured product information from the description"""
    info = create_empty_product_info()
    
    if isinstance(description, dict) and 'error' not in description:
        # Map JSON fields to CSV fields
        field_mapping = {
            'sku': 'SKU',
            'reference_number': 'Reference_Number',
            'brand': 'Brand',
            'model': 'Model',
            'material': 'Material',
            'color': 'Color',
            'size': 'Size',
            'year_of_production': 'Year_of_Production',
            'category': 'Category',
            'sub_category': 'Sub_category',
            'condition_grade': 'Condition_Grade',
            'condition_description': 'Condition_Description',
            'estimated_price_range': 'Retail_Price',
            'recommended_selling_price': 'Recommended_Selling_Price',
            'height': 'Height',
            'width': 'Width',
            'depth': 'Depth',
            'serial_number': 'Serial_Number'
        }
        
        for json_field, csv_field in field_mapping.items():
            value = description.get(json_field, '')
            if json_field == 'accessories' and isinstance(value, list):
                value = str(value)
            elif json_field == 'urls' and isinstance(value, list):
                value = str(value)
            info[csv_field] = value
    
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
        writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDS)
        writer.writerow(product_info)

def auto_update_csv_inventory(local_folder: str, product_description: dict, chinese_description: str, 
                            image_count: int, folder_path: str, description_file: str):
    """Automatically update CSV inventory with new product, checking for duplicates"""
    csv_path = get_csv_path(local_folder)
    create_csv_if_not_exists(csv_path)
    
    # Read existing inventory to check for duplicates
    existing_products = []
    if os.path.exists(csv_path):
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            existing_products = list(reader)
    
    # Check for duplicates
    sku = product_description.get('sku', '')
    reference_number = product_description.get('reference_number', '')
    
    for product in existing_products:
        if product.get('SKU') == sku:
            return {
                "success": False,
                "error": f"SKU {sku} already exists in inventory. Cannot overwrite existing product.",
                "existing_product": product
            }
        if product.get('Reference_Number') == reference_number:
            return {
                "success": False,
                "error": f"Reference Number {reference_number} already exists in inventory. Cannot overwrite existing product.",
                "duplicate_reference": product
            }
    
    # Extract product information and add to CSV
    product_info = extract_product_info_from_description(product_description)
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

# =============================================================================
# FILE OPERATIONS
# =============================================================================

def save_to_local_folder(sku: str, image_data: list, description: str, output_file: str, local_folder: str, 
                        chinese_description: str = "", reference_number: str = "", ordered_images=None):
    """Save files to local folder with SKU-based naming and CSV tracking"""
    try:
        # Create folder path (convert SKU to lowercase)
        folder_path = os.path.join(local_folder, sku.lower())
        os.makedirs(folder_path, exist_ok=True)
        
        saved_files = []
        
        # Save description file (convert SKU to lowercase)
        description_filename = f"{sku.lower()}_description.json"
        description_path = os.path.join(folder_path, description_filename)
        
        if isinstance(description, dict):
            with open(description_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(description, indent=2, ensure_ascii=False))
        else:
            with open(description_path, 'w', encoding='utf-8') as f:
                f.write(description)
        
        saved_files.append({
            'name': description_filename,
            'path': description_path,
            'type': 'description'
        })
        
        # Save images in the correct order
        if ordered_images and len(ordered_images) > 0:
            # Create mapping from filename to image data using the current ordered_images
            # This ensures we have the correct data for each image in the current order
            image_data_map = {}
            
            # Map each ordered image to its corresponding image data
            for i, ordered_file in enumerate(ordered_images):
                if i < len(image_data):
                    image_data_map[ordered_file.name] = image_data[i]
            
            # Save images in the order specified by ordered_images
            for i, ordered_file in enumerate(ordered_images, 1):
                if ordered_file.name in image_data_map:
                    img_data = image_data_map[ordered_file.name]
                    file_ext = get_file_extension(img_data)
                    
                    # Get image type for this image using the filename as the key
                    image_type = st.session_state.image_types.get(ordered_file.name, "")
                    
                    # Create filename with image type if specified (convert to lowercase)
                    if image_type:
                        new_filename = f"{sku.lower()}_{i}_{image_type.lower()}{file_ext}"
                    else:
                        new_filename = f"{sku.lower()}_{i}{file_ext}"
                    
                    new_path = os.path.join(folder_path, new_filename)
                    
                    with open(new_path, "wb") as f:
                        f.write(img_data)
                    
                    saved_files.append({
                        'name': new_filename,
                        'path': new_path,
                        'type': 'image'
                    })

        
        # Update CSV inventory
        csv_result = auto_update_csv_inventory(local_folder, description, chinese_description, len(image_data), folder_path, description_filename)
        
        if not csv_result["success"]:
            return csv_result
        
        return {
            "success": True,
            "folder_path": folder_path,
            "folder_name": sku.lower(),
            "saved_files": saved_files,
            "total_files": len(saved_files),
            "csv_updated": True,
            "csv_message": csv_result["message"],
            "total_products": csv_result["total_products"]
        }
        
    except Exception as e:
        return {"error": f"Local save error: {str(e)}"}

# =============================================================================
# SESSION STATE MANAGEMENT
# =============================================================================

def initialize_session_state():
    """Initialize all session state variables"""
    session_vars = {
        'generated_description': "",
        'generated_sku': "",
        'image_paths': [],
        'image_data': [],
        'show_review': False,
        'ordered_images': [],
        'ordered_images_for_saving': [],
        'image_types': {},  # Store image types for each image
        'show_order_info': False,
        'show_preview': False,
        'selected_image_idx': None,
        'confirm_remove_all': False,
        'drag_mode': False,
        'uploader_key': 'default',
        'uploaded_files': [],
        'enable_google_drive': False,
        'google_drive': None,
        'google_creds_path': None,
        'sync_to_sheets': True,
        'spreadsheet_name': f"SKU_Inventory"
    }
    
    for var, default_value in session_vars.items():
        if var not in st.session_state:
            st.session_state[var] = default_value

def reset_session_state():
    """Reset all session state variables"""
    reset_vars = [
        'show_review', 'generated_description', 'generated_sku', 'image_paths', 
        'image_data', 'ordered_images', 'ordered_images_for_saving', 'uploaded_files',
        'image_types', 'show_order_info', 'show_preview', 'selected_image_idx', 'confirm_remove_all', 
        'drag_mode'
    ]
    
    for var in reset_vars:
        if var in st.session_state:
            if var in ['ordered_images', 'ordered_images_for_saving', 'uploaded_files', 'image_paths', 'image_data', 'image_types']:
                st.session_state[var].clear()
            else:
                st.session_state[var] = False if var in ['show_review', 'show_order_info', 'show_preview', 'confirm_remove_all', 'drag_mode'] else None

# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_sidebar():
    """Render the sidebar with configuration options"""
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
            
            if local_folder:
                try:
                    os.makedirs(local_folder, exist_ok=True)
                    st.success(f"✅ Folder ready: {local_folder}")
                except Exception as e:
                    st.error(f"❌ Cannot create folder: {str(e)}")
        
        # Google Drive integration
        render_google_drive_section()
        
        # Instructions
        render_instructions()
        
        # CSV Inventory Section
        if save_to_folder and local_folder:
            render_csv_inventory_section(local_folder)
    
    # Return the configuration values
    return api_key, reference_number, chinese_description, save_to_folder, local_folder

def render_google_drive_section():
    """Render the Google Drive integration section"""
    st.markdown("---")
    st.markdown("### ☁️ Google Drive Integration")
    
    # Collapsible setup guide
    with st.expander("📚 Quick Setup Guide (Click to expand)", expanded=False):
        st.markdown("""
        **🚀 Quick Setup Steps:**
        
        1. **Create Google Cloud Project**
           - Go to [Google Cloud Console](https://console.cloud.google.com/)
           - Create new project → Enable Google Drive & Sheets APIs
        
        2. **Download credentials.json**
           - Go to APIs & Services → Credentials
           - Create OAuth 2.0 Client ID (Desktop app)
           - Download and rename to `credentials.json`
        
        3. **Place credentials.json**
           - Put it in the **same folder** as this app
           - Same level as `streamlit_app.py`
        
        4. **Enter path in app**
           - Use: `credentials.json` (just the filename)
        
        **📁 File Structure (What you should see):**
        ```
        Your-SKU-Folder/
        ├── streamlit_app.py
        ├── credentials.json  ← PUT HERE!
        └── other files...
        ```
        
        **❌ Common Mistakes:**
        - Don't put in `venv/` folder
        - Don't put in subfolders
        - Don't leave in Downloads
        
        **🔗 Full Guide:** See `GOOGLE_DRIVE_SETUP.md` for detailed instructions
        """)
        
        # Show what credentials.json should look like
        with st.expander("🔍 What should my credentials.json look like?", expanded=False):
            st.markdown("""
            **Your credentials.json should contain these fields:**
            
            ```json
            {
              "type": "service_account",
              "project_id": "your-project-name",
              "private_key_id": "abc123...",
              "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",
              "client_email": "your-service@your-project.iam.gserviceaccount.com",
              "client_id": "123456789...",
              "auth_uri": "https://accounts.google.com/o/oauth2/auth",
              "token_uri": "https://oauth2.googleapis.com/token",
              "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
              "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
            }
            ```
            
            **⚠️ Important:** Never share this file or commit it to version control!
            """)
    
    if not GOOGLE_DRIVE_AVAILABLE:
        st.warning("⚠️ Google Drive libraries not installed. Run: `pip install -r requirements.txt`")
    else:
        enable_google_drive = st.checkbox(
            "Enable Google Drive Upload",
            value=st.session_state.get('enable_google_drive', False),
            key='enable_google_drive',
            help="Upload files to Google Drive and sync CSV to Google Sheets"
        )
        
        if enable_google_drive:
            render_google_drive_config()
        else:
            if 'google_drive' in st.session_state:
                del st.session_state.google_drive

def render_google_drive_config():
    """Render Google Drive configuration options"""
    # Credentials path input with clear examples
    st.markdown("**🔑 Google API Credentials Path:**")
    
    # Path input options
    path_option = st.radio(
        "Choose how to specify your credentials:",
        ["📂 Custom path", "📤 Upload credentials file"],
        key="path_option"
    )
    
    if path_option == "📂 Custom path":
        google_credentials_path = st.text_input(
            "Enter full path to credentials.json:",
            value=st.session_state.get('google_credentials_path', ""),
            key='google_credentials_path',
            placeholder="e.g., C:\\Users\\YourName\\Desktop\\credentials.json",
            help="Full path to your credentials.json file"
        )
    else:  # Upload option
        uploaded_creds = st.file_uploader(
            "Upload your credentials.json file:",
            type=['json'],
            key='creds_uploader',
            help="Select your credentials.json file from Google Cloud Console"
        )
        
        if uploaded_creds:
            # Save the uploaded file temporarily
            temp_creds_path = "temp_credentials.json"
            with open(temp_creds_path, "wb") as f:
                f.write(uploaded_creds.getvalue())
            google_credentials_path = temp_creds_path
            st.success("✅ Credentials file uploaded successfully!")
            st.info("💡 **Note:** File will be used for this session. For permanent use, move it to the app folder.")
        else:
            google_credentials_path = ""
            st.info("📤 **Please upload your credentials.json file**")
    
    # Helpful tips based on path option
    if path_option == "📂 Custom path":
        if not google_credentials_path:
            st.info("💡 **Examples:**")
            st.code("Windows: C:\\Users\\YourName\\Desktop\\credentials.json\nMac/Linux: /Users/YourName/Desktop/credentials.json")
        elif not os.path.exists(google_credentials_path):
            st.warning("⚠️ **File not found.** Please check the path and make sure the file exists.")
    
    if google_credentials_path and os.path.exists(google_credentials_path):
        st.success("✅ Google credentials found!")
        
        # Store credentials path but don't initialize yet - wait for actual upload
        st.session_state.google_creds_path = google_credentials_path
        st.session_state.google_drive = None  # Will be initialized when needed
        
        st.info("💡 **Google Drive will be initialized when you click 'Upload to Google Drive'**")
        st.info("✅ **Ready to connect** - no APIs called yet")
    else:
        st.warning("⚠️ Please provide path to credentials.json file")
        st.session_state.google_drive = None
        
    # CSV to Google Sheets sync option
    sync_to_sheets = st.checkbox(
        "Sync CSV to Google Sheets",
        value=st.session_state.get('sync_to_sheets', True),
        key='sync_to_sheets',
        help="Automatically sync inventory CSV to Google Sheets"
    )
    
    # Spreadsheet name
    spreadsheet_name = st.text_input(
        "Google Sheets Name",
        value=st.session_state.get('spreadsheet_name', f"SKU_Inventory"),
        key='spreadsheet_name',
        help="Name for the Google Sheets spreadsheet"
    )

def render_instructions():
    """Render the instructions section"""
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

def render_csv_inventory_section(local_folder: str):
    """Render the CSV inventory management section"""
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

# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    st.title("👜 SKU Generator")
    st.markdown("Generate detailed product descriptions from images using AI")
    
    initialize_session_state()
    
    # Get sidebar configuration
    api_key, reference_number, chinese_description, save_to_folder, local_folder = render_sidebar()
    
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
                if st.button("🔄 Remove All Images", help="Clear the file uploader to start fresh", type="secondary"):
                    st.session_state.uploader_key = f"reset_{datetime.now().timestamp()}"
                    st.session_state.ordered_images.clear()
                    st.session_state.uploaded_files.clear()
                    st.session_state.image_types.clear()
                    st.session_state.selected_image_idx = None
                    st.session_state.confirm_remove_all = False
                    st.session_state.drag_mode = False
                    st.success("✅ All images have been removed!")
            with col_info:
                st.info("💡 Use 'Remove All Images' to clear files and start over, or 'Remove All Images' to clear the grid but keep uploader state.")
        
        if uploaded_files:
            st.success(f"Uploaded {len(uploaded_files)} images")
            
            # Store uploaded files in session state for reference
            st.session_state.uploaded_files = list(uploaded_files)
            
            # Update ordered images when new files are uploaded
            if len(uploaded_files) != len(st.session_state.ordered_images):
                st.session_state.ordered_images = list(uploaded_files)
            
            # Image Grid Display and Reordering
            st.subheader("🖼️ Image Grid & Reordering")
            # Image Grid Display - Drag & Drop Simulation
            st.markdown("**🖼️ Image Grid (4 per row) - Drag & Drop Style Interface**")
            st.markdown("""
            **How to use (simulates drag & drop):**
            - **🎯 Pick Up**: Click image to select (gets elevated with shadow)
            - **📥 Drop**: Click destination to move image there
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
                            
                            # Image type selector
                            image_type = render_image_type_selector(image_idx, uploaded_file)
                            
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
                        
                        # Also store the ordered files for reference in saving
                        st.session_state.ordered_images_for_saving = list(st.session_state.ordered_images)
                        
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
            # Handle JSON vs string description display
            if isinstance(st.session_state.generated_description, dict):
                # JSON response - display in a structured format
                st.subheader("📊 Generated Product Information")
                
                # Initialize edited_sku variable
                edited_sku = st.session_state.generated_sku
                
                # Display SKU
                if st.session_state.generated_sku:
                    edited_sku = st.text_input(
                        "SKU (Editable)",
                        value=st.session_state.generated_sku,
                        key="sku_editor",
                        help="Edit the SKU if needed. This will be used for file naming and CSV tracking."
                    )
                    
                    # Update the SKU in the generated description if it was changed
                    if edited_sku != st.session_state.generated_sku:
                        st.session_state.generated_sku = edited_sku
                        if isinstance(st.session_state.generated_description, dict):
                            st.session_state.generated_description['sku'] = edited_sku
                        st.success(f"✅ SKU updated to: {edited_sku}")
                    
                    # Update the JSON display to reflect the edited SKU
                    if isinstance(st.session_state.generated_description, dict):
                        # Create a copy of the description with the updated SKU
                        updated_description = st.session_state.generated_description.copy()
                        updated_description['sku'] = edited_sku
                        
                        # Update the JSON display
                        json_display = json.dumps(updated_description, indent=2, ensure_ascii=False)
                    else:
                        json_display = json.dumps(st.session_state.generated_description, indent=2, ensure_ascii=False)
                
                # Display JSON data in a readable format (with updated SKU if edited)
                st.info("💡 **Note:** The SKU field in the JSON will automatically update when you edit the SKU above.")
                edited_json = st.text_area(
                    "Edit Product Information (JSON format)",
                    value=json_display,
                    height=400,
                    help="Review and modify the JSON data. SKU field will automatically update when you change the SKU above."
                )
                
                # Try to parse edited JSON
                try:
                    edited_description = json.loads(edited_json)
                    # Preserve the edited SKU and update session state
                    if edited_sku:
                        edited_description['sku'] = edited_sku
                        st.session_state.generated_sku = edited_sku
                        st.session_state.generated_description = edited_description
                    else:
                        st.session_state.generated_description = edited_description
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON format. Please check your edits.")
                    edited_description = st.session_state.generated_description
                
            else:
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
            col_actions1, col_actions2, col_actions3 = st.columns(3)
            
            with col_actions1:
                # Download button
                # Use the edited SKU for the filename (convert to lowercase)
                current_sku_for_filename = edited_sku if 'edited_sku' in locals() else st.session_state.generated_sku
                if current_sku_for_filename:
                    output_filename = f"{current_sku_for_filename.lower()}_description.json"
                else:
                    output_filename = "generated_sku.json"
                
                st.download_button(
                    label="📥 Download Description",
                    data=json.dumps(edited_description, indent=2, ensure_ascii=False),
                    file_name=output_filename,
                    mime="application/json"
                )
            
            with col_actions2:
                # Save to local folder button (only if enabled)
                if save_to_folder and local_folder and st.session_state.generated_sku:
                    if st.button("📁 Save to Local Folder", type="primary"):
                        with st.spinner("Saving to local folder..."):
                            # Use the current SKU (which may have been edited)
                            current_sku = edited_sku if 'edited_sku' in locals() else st.session_state.generated_sku
                            save_result = save_to_local_folder(
                                current_sku, 
                                st.session_state.image_data, 
                                edited_description,  # Pass the JSON dict directly
                                output_filename, 
                                local_folder,
                                chinese_description,
                                reference_number,
                                st.session_state.get('ordered_images_for_saving', st.session_state.ordered_images)  # Use the ordered images from when processing started
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
                                
                                # Show the actual order that was saved
                                if st.session_state.ordered_images:
                                    st.info("📋 **Images saved in this order:**")
                                    for i, ordered_file in enumerate(st.session_state.ordered_images, 1):
                                        # Get image type for this image using filename-based lookup
                                        image_type = st.session_state.image_types.get(ordered_file.name, "")
                                        
                                        if image_type:
                                            st.markdown(f"   {i}. {ordered_file.name} → {image_type}")
                                        else:
                                            st.markdown(f"   {i}. {ordered_file.name}")
                                
                                # Show folder structure with image types
                                structure_lines = [f"{save_result['folder_name']}/"]
                                structure_lines.append(f"├── {current_sku.lower()}_description.json")
                                
                                for i, ordered_file in enumerate(st.session_state.ordered_images, 1):
                                    # Get image type and extension using filename-based lookup
                                    image_type = st.session_state.image_types.get(ordered_file.name, "")
                                    file_ext = get_file_extension(st.session_state.image_data[i-1])
                                    
                                    if image_type:
                                        filename = f"{current_sku.lower()}_{i}_{image_type.lower()}{file_ext}"
                                    else:
                                        filename = f"{current_sku.lower()}_{i}{file_ext}"
                                    
                                    if i == len(st.session_state.ordered_images):
                                        structure_lines.append(f"└── {filename}")
                                    else:
                                        structure_lines.append(f"├── {filename}")
                                
                                st.markdown("**📁 Folder Structure:**")
                                st.code('\n'.join(structure_lines))
                                
                                # Success message
                                st.markdown("---")
                                st.success("🎉 **Product saved successfully!**")
                                st.info("💡 You can now upload to Google Drive or continue editing. Use 'Generate New Description' to start over.")
                            else:
                                st.error(f"❌ Save failed: {save_result['error']}")
                elif save_to_folder and not st.session_state.generated_sku:
                    st.warning("⚠️ Cannot save: SKU not found in description")
                elif save_to_folder and not local_folder:
                    st.warning("⚠️ Cannot save: No folder path specified")
                elif not save_to_folder:
                    st.info("💡 Enable 'Save to Local Folder' in sidebar to save files")
            
            # Test Google Sheets connection button
            if st.session_state.get('enable_google_drive') and st.session_state.get('google_creds_path'):
                if st.button("🧪 Test Google Sheets Connection", type="secondary"):
                    with st.spinner("Initializing Google Drive..."):
                        try:
                            # Initialize Google Drive ONLY when user clicks test
                            if not st.session_state.get('google_drive'):
                                google_drive = GoogleDriveIntegration(st.session_state.google_creds_path)
                                st.session_state.google_drive = google_drive
                                st.success("✅ Google Drive initialized successfully!")
                            
                            # Now test the connection
                            with st.spinner("Testing Google Sheets connection..."):
                                test_result = st.session_state.google_drive.create_or_update_spreadsheet(
                                    "TEST_CONNECTION", 
                                    [{"test": "data", "status": "working"}]
                                )
                                if test_result:
                                    st.success("✅ Google Sheets connection working!")
                                    st.info(f"Test spreadsheet created: {test_result}")
                                else:
                                    st.error("❌ Google Sheets connection failed")
                        except Exception as e:
                            st.error(f"❌ **Google Drive initialization failed:** {str(e)}")
                            st.exception(e)
            
            with col_actions3:
                # Google Drive upload button (always visible, but only functional if enabled)
                if st.session_state.generated_sku:
                    if st.session_state.get('enable_google_drive'):
                        if st.session_state.get('google_creds_path'):
                            if st.button("☁️ Upload to Google Drive", type="secondary", disabled=False):
                                with st.spinner("Initializing Google Drive..."):
                                    try:
                                        # Initialize Google Drive ONLY when user clicks upload
                                        if not st.session_state.get('google_drive'):
                                            google_drive = GoogleDriveIntegration(st.session_state.google_creds_path)
                                            st.session_state.google_drive = google_drive
                                            st.success("✅ Google Drive initialized successfully!")
                                        
                                        # Now proceed with upload
                                        with st.spinner("Uploading to Google Drive..."):
                                            # Get the local folder path for the current SKU (use lowercase)
                                            current_sku = st.session_state.generated_sku
                                            sku_folder = os.path.join(local_folder, current_sku.lower()) if local_folder else None
                                            
                                            if sku_folder and os.path.exists(sku_folder):
                                                # Upload SKU folder to Google Drive
                                                drive_result = st.session_state.google_drive.upload_sku_to_drive(
                                                    current_sku, 
                                                    sku_folder, 
                                                    chinese_description, 
                                                    reference_number
                                                )
                                                
                                                if drive_result.get("success"):
                                                    st.success(f"✅ **{drive_result['message']}**")
                                                    st.info(f"📁 **Main Folder ID:** {drive_result['main_folder_id']}")
                                                    st.info(f"📁 **SKU Folder ID:** {drive_result['sku_folder_id']}")
                                                    st.info(f"📄 **Files Uploaded:** {len(drive_result['uploaded_files'])}")
                                                    
                                                    # Sync CSV to Google Sheets if enabled
                                                    if st.session_state.get('sync_to_sheets'):
                                                        csv_path = os.path.join(local_folder, "sku_inventory.csv")
                                                        if os.path.exists(csv_path):
                                                            with st.spinner("Syncing CSV to Google Sheets..."):
                                                                sheets_result = st.session_state.google_drive.sync_csv_to_sheets(
                                                                    csv_path, 
                                                                    st.session_state.get('spreadsheet_name', f"SKU_Inventory")
                                                                )
                                                                
                                                                if sheets_result.get("success"):
                                                                    st.success(f"📊 **{sheets_result['message']}**")
                                                                    st.info(f"📈 **Rows Synced:** {sheets_result['rows_synced']}")
                                                                    st.info(f"🔗 **Spreadsheet:** [Open in Google Sheets]({sheets_result['spreadsheet_url']})")
                                                                else:
                                                                    st.error(f"❌ **Sheets Sync Failed:** {sheets_result['error']}")
                                                        else:
                                                            st.warning("⚠️ CSV file not found. Cannot sync to Google Sheets.")
                                                    else:
                                                        st.info("💡 CSV sync to Google Sheets is disabled in sidebar settings.")
                                                else:
                                                    st.error(f"❌ **Drive Upload Failed:** {drive_result['error']}")
                                            else:
                                                st.error("❌ **Local folder not found.** Please save to local folder first.")
                                    except Exception as e:
                                        st.error(f"❌ **Google Drive initialization failed:** {str(e)}")
                                        st.exception(e)
                        else:
                            st.button("☁️ Upload to Google Drive", type="secondary", disabled=True, 
                                     help="Google Drive credentials not configured. Check sidebar configuration.")
                    else:
                        st.button("☁️ Upload to Google Drive", type="secondary", disabled=True, 
                                 help="Enable Google Drive in sidebar to use this feature.")
                else:
                    st.button("☁️ Upload to Google Drive", type="secondary", disabled=True, 
                             help="Generate a description first to enable Google Drive upload.")
            
            # Reset button
            if st.button("🔄 Generate New Description"):
                reset_session_state()
                st.rerun()
        
        # Show help information
        st.markdown("---")
        st.markdown("### 💡 Tips")
        st.markdown("""
        - **Best results**: Upload clear, high-quality images from multiple angles
        - **Image order**: Use the reorder buttons to arrange images in your preferred order
        - **Image types**: Select appropriate types (front, back, inside, hardware, serial number) for better organization
        - **Chinese description**: Provide detailed info about bag type, condition, material
        - **Gemini API Key**: Get Gemini key from [makersuite.google.com](https://makersuite.google.com/app/apikey)
        - **Supported formats**: JPG, PNG, BMP, TIFF, WebP
        - **Review & Edit**: Check the generated description and make modifications before saving
        - **File naming**: Output files are automatically named using the generated SKU and image types
        - **Local folder**: Files are automatically saved with SKU-based naming when enabled
        """)

if __name__ == "__main__":
    main() 
