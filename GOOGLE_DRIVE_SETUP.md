# Google Drive Integration Setup Guide

This guide will help you set up Google Drive API integration for the SKU Generator, allowing you to:
- Upload all files to Google Drive with organized folder structure
- Automatically sync CSV inventory to Google Sheets
- Access your inventory from anywhere

## Prerequisites

1. **Google Account** with access to Google Drive and Google Sheets
2. **Python environment** with the required packages installed
3. **Google Cloud Project** (free tier available)

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter a project name (e.g., "SKU Generator")
4. Click "Create"

## Step 2: Enable Google Drive API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Google Drive API"
3. Click on it and click "Enable"
4. Search for "Google Sheets API"
5. Click on it and click "Enable"

## Step 3: Create Credentials

You have two options for authentication:

### Option A: OAuth 2.0 Client (Recommended for personal use)

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Choose "Desktop application"
4. Give it a name (e.g., "SKU Generator Desktop")
5. Click "Create"
6. Download the JSON file and rename it to `credentials.json`
7. Place it in your SKU Generator folder

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

## Step 6: Configure Google Drive Settings

In the Streamlit app sidebar:

1. **Enable Google Drive Upload** - Check this to enable Google Drive features
2. **Google API Credentials Path** - Path to your `credentials.json` file
3. **Sync CSV to Google Sheets** - Automatically sync inventory to Google Sheets
4. **Google Sheets Name** - Name for your inventory spreadsheet

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

## Support

If you encounter issues:
1. Check the error messages in the Streamlit app
2. Verify your Google Cloud Project setup
3. Ensure all required packages are installed
4. Check your internet connection and Google account status

The Google Drive integration will make your SKU Generator much more powerful and professional! 🚀
