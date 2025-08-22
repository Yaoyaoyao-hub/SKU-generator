# 🚀 Google Drive Integration Setup Guide

This comprehensive guide will help you set up Google Drive API integration for the SKU Generator, allowing you to:
- 📁 Upload all files to Google Drive with organized folder structure
- 📊 Automatically sync CSV inventory to Google Sheets
- 🌐 Access your inventory from anywhere
- ☁️ Secure cloud backup of all your product data

## 📋 Prerequisites

1. **Google Account** with access to Google Drive and Google Sheets
2. **Python environment** with the required packages installed
3. **Google Cloud Project** (free tier available - no credit card required)
4. **SKU Generator app** installed and working locally

## 🎯 Quick Start Checklist

- [ ] Create Google Cloud Project
- [ ] Enable Google Drive & Sheets APIs
- [ ] Create credentials.json file
- [ ] Place credentials.json in correct folder
- [ ] Install required packages
- [ ] Test connection in Streamlit app

## Step 1: Create Google Cloud Project

### Detailed Instructions:

1. **Open Google Cloud Console**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Sign in with your Google account

2. **Create New Project**
   - Click "Select a project" (top of the page, next to "Google Cloud")
   - Click "NEW PROJECT" button
   - Enter a project name (e.g., "SKU Generator" or "My-SKU-App")
   - Leave Organization as "No organization" (unless you have a business account)
   - Click "CREATE"
   - Wait for the project to be created (usually takes 10-30 seconds)

3. **Select Your Project**
   - Make sure your new project is selected (check the project name at the top)
   - If not selected, click the project dropdown and select your project

## Step 2: Enable Required APIs

### Enable Google Drive API:

1. **Navigate to API Library**
   - In the left sidebar, click "APIs & Services" → "Library"
   - Or use this direct link: [API Library](https://console.cloud.google.com/apis/library)

2. **Enable Google Drive API**
   - In the search box, type "Google Drive API"
   - Click on "Google Drive API" (by Google)
   - Click the blue "ENABLE" button
   - Wait for confirmation (green checkmark appears)

### Enable Google Sheets API:

3. **Enable Google Sheets API**
   - Go back to the API Library (click "Library" in the left sidebar)
   - In the search box, type "Google Sheets API"
   - Click on "Google Sheets API" (by Google)
   - Click the blue "ENABLE" button
   - Wait for confirmation (green checkmark appears)

✅ **Both APIs should now show as "Enabled" in your APIs & Services dashboard**

## Step 3: Create Credentials

You have two options for authentication:

### Option A: OAuth 2.0 Client (Recommended for personal use)

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Choose "Desktop application"
4. Give it a name (e.g., "SKU Generator Desktop")
5. Click "Create"
6. Download the JSON file and rename it to `credentials.json`
7. **Place it in your SKU Generator folder** (see file placement instructions below)

### Option B: Service Account (Recommended for business/automation)

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Give it a name (e.g., "SKU Generator Service")
4. Click "Create and Continue"
5. Skip role assignment (click "Continue")
6. Click "Done"
7. Click on the created service account
8. Go to "Keys" tab
9. Click "Add Key" → "Create new key"
10. Choose "JSON" format
11. Download the JSON file and rename it to `credentials.json`
12. **Place it in your SKU Generator folder** (see file placement instructions below)

## 📁 Where to Store Your credentials.json File

### **IMPORTANT: File Placement is Critical!**

After downloading your `credentials.json` file, you **MUST** place it in the correct location for the app to find it.

### **Step-by-Step File Placement:**

1. **Find Your SKU Generator Folder**
   - This is the folder where you have your `streamlit_app.py` file
   - It's the same folder where you run the `streamlit run streamlit_app.py` command

2. **Place credentials.json in the Root SKU Generator Folder**
   ```
   Your-SKU-Generator-Folder/
   ├── streamlit_app.py
   ├── generate_sku.py
   ├── prompts.py
   ├── requirements.txt
   ├── credentials.json  ← PUT IT HERE!
   ├── venv/             (if you have a virtual environment)
   └── other files...
   ```

3. **File Structure Example:**
   ```
   /Users/yourname/SKU-generator/
   ├── streamlit_app.py
   ├── credentials.json  ← Place here!
   └── other files...
   ```

### **❌ DON'T Put It Here:**
   - ❌ Inside the `venv/` folder
   - ❌ In a subfolder
   - ❌ On your Desktop (unless that's where your SKU Generator folder is)
   - ❌ In Downloads folder

### **✅ DO Put It Here:**
   - ✅ Same folder as `streamlit_app.py`
   - ✅ Same folder where you run the `streamlit` command
   - ✅ Root level of your SKU Generator project

### **How to Verify Correct Placement:**

1. **Check your current working directory:**
   ```bash
   # If you're in the SKU Generator folder, run:
   ls -la
   # You should see both streamlit_app.py and credentials.json
   ```

2. **Or check in File Explorer/Finder:**
   - Navigate to your SKU Generator folder
   - You should see both files in the same folder

### **Visual File Structure Verification:**

```
✅ CORRECT - credentials.json in root folder:
SKU-generator/
├── streamlit_app.py
├── credentials.json  ← ✅ HERE!
├── generate_sku.py
├── requirements.txt
└── venv/
    └── ...

❌ WRONG - credentials.json in wrong location:
SKU-generator/
├── streamlit_app.py
├── generate_sku.py
├── requirements.txt
├── venv/
│   └── credentials.json  ← ❌ WRONG!
└── ...
```

### **Step-by-Step Verification Process:**

1. **Open your file manager** (File Explorer on Windows, Finder on Mac)
2. **Navigate to your SKU Generator folder**
3. **Look for these files in the same folder:**
   - `streamlit_app.py` ✅
   - `credentials.json` ✅
   - `generate_sku.py` ✅
   - `requirements.txt` ✅
4. **If you see `credentials.json` in a subfolder or `venv/` folder, move it to the root level**

### Option B: Service Account (Recommended for business/automation)

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Give it a name (e.g., "SKU Generator Service")
4. Click "Create and Continue"
5. Skip role assignment (click "Continue")
6. Click "Done"
7. Click on the created service account
8. Go to "Keys" tab
9. Click "Add Key" → "Create new key"
10. Choose "JSON" format
11. Download the JSON file and rename it to `credentials.json`
12. Place it in your SKU Generator folder

## Step 4: Install Required Packages

Run the following command in your terminal:

```bash
pip install -r requirements.txt
```

This will install:
- `google-auth` - Google authentication
- `google-auth-oauthlib` - OAuth 2.0 flow
- `google-auth-httplib2` - HTTP client
- `google-api-python-client` - Google API client
- `gspread` - Google Sheets integration
- `oauth2client` - OAuth 2.0 client

## Step 5: First Run Authentication

### For OAuth 2.0 Client (Option A):
1. Start the Streamlit app
2. In the sidebar, check "Enable Google Drive Upload"
3. Enter the path to your `credentials.json` file
4. The first time you use Google Drive features, a browser window will open
5. Sign in with your Google account
6. Grant permissions to the app
7. A `token.json` file will be created automatically

### For Service Account (Option B):
1. Start the Streamlit app
2. In the sidebar, check "Enable Google Drive Upload"
3. Enter the path to your `credentials.json` file
4. **Important**: Share your Google Drive folder with the service account email
   - The email will be shown in the app when you enable Google Drive
   - Go to your Google Drive and share the folder with this email
   - Give it "Editor" permissions
5. No browser authentication needed - works automatically

## Step 6: Configure Google Drive Settings in the App

### **In the Streamlit App Sidebar:**

1. **Enable Google Drive Upload** - Check this checkbox to enable Google Drive features
2. **Google API Credentials Path** - Enter the path to your `credentials.json` file
3. **Sync CSV to Google Sheets** - Check this to automatically sync inventory to Google Sheets
4. **Google Sheets Name** - Enter a name for your inventory spreadsheet (e.g., "SKU_Inventory")

### **Credentials Path Examples:**

#### **If credentials.json is in the same folder as the app:**
```
./credentials.json
```
or just:
```
credentials.json
```

#### **If using absolute path (Windows):**
```
C:\Users\YourName\SKU-generator\credentials.json
```

#### **If using absolute path (Mac/Linux):**
```
/Users/YourName/SKU-generator/credentials.json
```

### **Quick Setup (Recommended):**
1. Place `credentials.json` in the same folder as `streamlit_app.py`
2. In the app, enter: `credentials.json` (just the filename)
3. The app will automatically find it

### **Troubleshooting Credentials Path:**
- **"File not found" error**: Check that the path is correct and the file exists
- **"Permission denied"**: Make sure the file is readable
- **"Invalid credentials"**: Verify the file is a valid JSON from Google Cloud Console

## Authentication Methods Comparison

### OAuth 2.0 Client (Option A)
- ✅ **Personal use** - Perfect for individual users
- ✅ **Easy setup** - Browser-based authentication
- ✅ **User consent** - You control the permissions
- ❌ **Browser required** - First-time setup needs browser
- ❌ **Token refresh** - May need re-authentication

### Service Account (Option B)
- ✅ **Business use** - Perfect for automation and teams
- ✅ **No browser** - Works completely automatically
- ✅ **Always available** - No token expiration issues
- ❌ **Setup complexity** - Requires sharing folders manually
- ❌ **Security** - More powerful permissions (use carefully)

**Recommendation**: Use OAuth 2.0 for personal use, Service Account for business/automation.

## How It Works

### File Upload Structure
```
Google Drive/
└── SKU_Generator/
    ├── [SKU_NAME_1]/
    │   ├── [SKU]_description.json
    │   ├── [SKU]_1.jpg
    │   ├── [SKU]_2.jpg
    │   └── [SKU]_3.jpg
    ├── [SKU_NAME_2]/
    │   ├── [SKU]_description.json
    │   ├── [SKU]_1.jpg
    │   └── [SKU]_2.jpg
    ├── [SKU_NAME_3]/
    │   ├── [SKU]_description.json
    │   └── [SKU]_1.jpg
    └── 📊 [SPREADSHEET_NAME].xlsx
        └── Inventory worksheet with all SKU data
```

### Google Sheets Integration
- Creates a new spreadsheet with your inventory data
- Automatically syncs when new products are added
- Formatted with headers and professional styling
- Accessible from any device with internet

## Troubleshooting

### Common Issues

1. **"Google Drive libraries not installed"**
   - Run: `pip install -r requirements.txt`

2. **"No credentials.json found"**
   - Make sure you downloaded the credentials file from Google Cloud Console
   - Place it in your SKU Generator folder

3. **"Failed to connect to Google Drive"**
   - Check your internet connection
   - Verify the credentials.json file is correct
   - Make sure you've enabled the APIs in Google Cloud Console

4. **"Permission denied"**
   - Make sure you granted permissions during the OAuth flow
   - Delete `token.json` and re-authenticate

### File Permissions

- The app creates folders and uploads files to your Google Drive
- You have full control over all uploaded files
- Files are organized by SKU for easy management

## Security Notes

- `credentials.json` contains your app's OAuth 2.0 credentials
- `token.json` contains your personal access tokens
- Keep these files secure and don't share them
- You can revoke access anytime in your Google Account settings

## Benefits

✅ **Cloud Backup** - All files safely stored in Google Drive
✅ **Easy Access** - Access inventory from any device
✅ **Professional Sheets** - Automated Google Sheets integration
✅ **Organized Structure** - Clean folder organization by SKU
✅ **Real-time Sync** - CSV data always up-to-date in Sheets
✅ **No Manual Work** - Everything happens automatically

## 🎯 Quick Reference: File Placement Summary

### **The Golden Rule:**
**`credentials.json` must be in the SAME folder as `streamlit_app.py`**

### **File Structure (What You Should See):**
```
Your-SKU-Generator-Folder/
├── streamlit_app.py          ← Main app file
├── credentials.json          ← PUT HERE! (same level)
├── generate_sku.py           ← SKU generation logic
├── requirements.txt          ← Python packages
└── venv/                     ← Virtual environment (don't put credentials here!)
```

### **Common Mistakes to Avoid:**
- ❌ **Don't put credentials.json in the venv/ folder**
- ❌ **Don't put credentials.json in a subfolder**
- ❌ **Don't leave credentials.json in Downloads**
- ❌ **Don't rename the file** (keep it as `credentials.json`)

## 🆘 Support & Troubleshooting

If you encounter issues:

### **1. Check File Placement First:**
- Verify `credentials.json` is in the same folder as `streamlit_app.py`
- Use the visual verification steps above

### **2. Common Error Messages:**
- **"File not found"** → Check file path in the app
- **"Invalid credentials"** → Re-download from Google Cloud Console
- **"Permission denied"** → Check file permissions

### **3. Still Having Issues?**
1. Check the error messages in the Streamlit app
2. Verify your Google Cloud Project setup
3. Ensure all required packages are installed
4. Check your internet connection and Google account status
5. Try deleting and re-downloading `credentials.json`

## 🎉 You're All Set!

Once you have:
- ✅ `credentials.json` in the correct folder
- ✅ Google Drive API enabled
- ✅ Google Sheets API enabled
- ✅ All packages installed

Your Google Drive integration will work perfectly! 🚀

**The app will automatically:**
- Upload product images and descriptions to Google Drive
- Create organized folders for each SKU
- Sync your inventory to Google Sheets
- Keep everything backed up in the cloud

Happy SKU generating! 📱✨
