#!/usr/bin/env python3
"""
Google Drive Integration for SKU Generator
Handles uploading files to Google Drive and syncing CSV to Google Sheets
"""

import os
import json
import csv
from typing import List, Dict, Optional
from datetime import datetime

# Google Drive imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
    from googleapiclient.errors import HttpError
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False
    print("Warning: Google Drive libraries not installed. Run: pip install -r requirements.txt")

class GoogleDriveIntegration:
    def __init__(self, credentials_path: str = None):
        """Initialize Google Drive integration"""
        self.credentials_path = credentials_path
        self.drive_service = None
        self.sheets_service = None
        self.gspread_client = None
        
        if GOOGLE_DRIVE_AVAILABLE:
            self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive and Sheets"""
        try:
            # Google Drive API authentication
            SCOPES = [
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/spreadsheets'
            ]
            
            creds = None
            token_path = 'token.json'
            
            # Check if we have valid credentials
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if self.credentials_path and os.path.exists(self.credentials_path):
                        # Try to determine if it's a service account or OAuth client
                        try:
                            with open(self.credentials_path, 'r') as f:
                                cred_data = json.load(f)
                            
                            if 'client_email' in cred_data and 'private_key' in cred_data:
                                # This is a service account credentials file
                                from google.oauth2 import service_account
                                creds = service_account.Credentials.from_service_account_file(
                                    self.credentials_path, scopes=SCOPES)
                            elif 'client_id' in cred_data and 'client_secret' in cred_data:
                                # This is an OAuth client credentials file
                                flow = InstalledAppFlow.from_client_secrets_file(
                                    self.credentials_path, SCOPES)
                                creds = flow.run_local_server(port=0)
                            else:
                                print("Warning: Credentials file format not recognized.")
                                return
                        except Exception as e:
                            print(f"Error reading credentials file: {e}")
                            return
                    else:
                        print("Warning: No credentials file found. Google Drive features will be disabled.")
                        return
                
                # Save credentials for next run (only for OAuth flow)
                if not hasattr(creds, 'service_account_email'):  # Not a service account
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
            
            # Build services
            self.drive_service = build('drive', 'v3', credentials=creds)
            self.sheets_service = build('sheets', 'v4', credentials=creds)
            
            # GSpread client for Google Sheets
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            try:
                if hasattr(creds, 'service_account_email'):
                    # Service account authentication
                    print("Using service account authentication for gspread")
                    self.gspread_client = gspread.service_account(filename=self.credentials_path)
                else:
                    # OAuth authentication
                    print("Using OAuth authentication for gspread")
                    self.gspread_client = gspread.authorize(creds)
                
                # Test the gspread client
                if self.gspread_client:
                    print("gspread client initialized successfully")
                    # Simple authentication test without listing all spreadsheetsc
                    try:
                        # Just test if we can create a temporary test spreadsheet
                        test_spreadsheet = self.gspread_client.create("TEST_AUTH")
                        # Use the correct method to delete the spreadsheet
                        try:
                            test_spreadsheet.delete()  # Try the old method first
                        except AttributeError:
                            # For newer gspread versions, use the client to delete
                            self.gspread_client.del_spreadsheet(test_spreadsheet.id)
                        print("Successfully authenticated with Google Sheets.")
                    except Exception as test_error:
                        print(f"Warning: gspread authentication test failed: {test_error}")
                else:
                    print("Warning: gspread client is None")
                    
            except Exception as gspread_error:
                print(f"Error initializing gspread client: {gspread_error}")
                self.gspread_client = None
                
        except Exception as e:
            print(f"Error authenticating with Google: {e}")
            import traceback
            traceback.print_exc()
            self.drive_service = None
            self.sheets_service = None
            self.gspread_client = None
    
    def find_folder_by_name(self, folder_name: str, parent_folder_id: str = None) -> Optional[str]:
        """Find a folder by name in Google Drive"""
        if not self.drive_service:
            return None
            
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"
            else:
                query += " and 'root' in parents"
            
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            if files:
                return files[0]['id']  # Return first matching folder
            return None
            
        except HttpError as error:
            print(f'Error finding folder: {error}')
            return None
    
    def create_folder(self, folder_name: str, parent_folder_id: str = None) -> Optional[str]:
        """Create a folder in Google Drive"""
        if not self.drive_service:
            return None
            
        try:
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                folder_metadata['parents'] = [parent_folder_id]
            
            folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            return folder.get('id')
        except HttpError as error:
            print(f'Error creating folder: {error}')
            return None
    
    def upload_file(self, file_path: str, folder_id: str = None, filename: str = None) -> Optional[str]:
        """Upload a file to Google Drive"""
        if not self.drive_service:
            return None
            
        try:
            if not filename:
                filename = os.path.basename(file_path)
            
            file_metadata = {
                'name': filename
            }
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaFileUpload(file_path, resumable=True)
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            return file.get('id')
        except HttpError as error:
            print(f'Error uploading file: {error}')
            return None
    
    def upload_file_from_data(self, file_data: bytes, filename: str, folder_id: str = None) -> Optional[str]:
        """Upload file data directly to Google Drive"""
        if not self.drive_service:
            return None
            
        try:
            from io import BytesIO
            
            file_metadata = {
                'name': filename
            }
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaIoBaseUpload(
                BytesIO(file_data),
                mimetype='application/octet-stream',
                resumable=True
            )
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            return file.get('id')
        except HttpError as error:
            print(f'Error uploading file data: {error}')
            return None
    
    def create_or_update_spreadsheet(self, spreadsheet_name: str, data: List[Dict], 
                                   sheet_name: str = "Inventory", optimize_folder_check: bool = True) -> Optional[str]:
        """Create or update a Google Spreadsheet with inventory data"""
        if not self.gspread_client:
            print("Error: gspread client not initialized")
            return None
            
        try:
            print(f"Attempting to create/update spreadsheet: {spreadsheet_name}")
            
            # Try to open existing spreadsheet
            try:
                print("Looking for existing spreadsheet...")
                spreadsheet = self.gspread_client.open(spreadsheet_name)
                print(f"Found existing spreadsheet: {spreadsheet.title}")
                
                # Only check folder location if we have drive service and optimization is enabled
                if self.drive_service and optimize_folder_check:
                    try:
                        # Find SKU_Generator main folder
                        main_folder_id = self.find_folder_by_name("SKU_Generator")
                        if main_folder_id:
                            # Check if spreadsheet is already in the folder
                            spreadsheet_id = spreadsheet.id
                            file_info = self.drive_service.files().get(
                                fileId=spreadsheet_id,
                                fields='parents'
                                ).execute()
                            
                            current_parents = file_info.get('parents', [])
                            if main_folder_id not in current_parents:
                                # Move the file to the SKU_Generator folder
                                file = self.drive_service.files().update(
                                    fileId=spreadsheet_id,
                                    addParents=main_folder_id,
                                    removeParents='root',
                                    fields='id, parents'
                                ).execute()
                                
                                print(f"Existing spreadsheet moved to SKU_Generator folder: {spreadsheet_id}")
                            else:
                                print(f"Spreadsheet already in SKU_Generator folder: {spreadsheet_id}")
                        else:
                            print("Warning: SKU_Generator folder not found for spreadsheet")
                    except Exception as move_error:
                        print(f"Warning: Could not check/move existing spreadsheet: {move_error}")
                
            except gspread.SpreadsheetNotFound:
                print("Creating new spreadsheet...")
                spreadsheet = self.gspread_client.create(spreadsheet_name)
                print(f"Created new spreadsheet: {spreadsheet.title}")
                
                # Move the new spreadsheet to SKU_Generator folder
                if self.drive_service:
                    try:
                        # Find or create SKU_Generator main folder
                        main_folder_id = self.find_folder_by_name("SKU_Generator")
                        if not main_folder_id:
                            main_folder_id = self.create_folder("SKU_Generator")
                        
                        if main_folder_id:
                            # Get the spreadsheet file ID from gspread
                            spreadsheet_id = spreadsheet.id
                            
                            # Move the file to the SKU_Generator folder
                            file = self.drive_service.files().update(
                                fileId=spreadsheet_id,
                                addParents=main_folder_id,
                                removeParents='root',
                                fields='id, parents'
                            ).execute()
                            
                            print(f"Spreadsheet moved to SKU_Generator folder: {spreadsheet_id}")
                        else:
                            print("Warning: Could not create SKU_Generator folder for spreadsheet")
                    except Exception as move_error:
                        print(f"Warning: Could not move spreadsheet to SKU_Generator folder: {move_error}")
                
            except Exception as e:
                print(f"Error accessing spreadsheet: {e}")
                return None
            
            # Get or create worksheet
            try:
                print("Looking for existing worksheet...")
                worksheet = spreadsheet.worksheet(sheet_name)
                print(f"Found existing worksheet: {worksheet.title}")
            except gspread.WorksheetNotFound:
                print("Creating new worksheet...")
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=30)
                print(f"Created new worksheet: {worksheet.title}")
            except Exception as e:
                print(f"Error accessing worksheet: {e}")
                return None
            
            # Clear existing data
            print("Clearing existing data...")
            worksheet.clear()
            
            # Prepare headers and data
            if data:
                headers = list(data[0].keys())
                rows = [headers]
                
                for row in data:
                    row_values = []
                    for header in headers:
                        value = row.get(header, '')
                        # Convert lists and complex objects to strings
                        if isinstance(value, (list, dict)):
                            value = json.dumps(value, ensure_ascii=False)
                        row_values.append(str(value))
                    rows.append(row_values)
                
                # Update worksheet
                print(f"Updating worksheet with {len(rows)} rows...")
                worksheet.update('A1', rows)
                
                # Format header row
                try:
                    worksheet.format('A1:Z1', {
                        'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
                        'textFormat': {'bold': True}
                    })
                    print("Header formatting applied")
                except Exception as format_error:
                    print(f"Warning: Header formatting failed: {format_error}")
            
            print(f"Spreadsheet updated successfully: {spreadsheet.url}")
            return spreadsheet.url
            
        except Exception as e:
            print(f'Error updating spreadsheet: {e}')
            import traceback
            traceback.print_exc()
            return None
    
    def quick_update_spreadsheet(self, spreadsheet_name: str, data: List[Dict], 
                                sheet_name: str = "Inventory") -> Optional[str]:
        """Quick update spreadsheet without folder optimization checks (faster, fewer API calls)"""
        if not self.gspread_client:
            print("Error: gspread client not initialized")
            return None
            
        try:
            print(f"Quick update of spreadsheet: {spreadsheet_name}")
            
            # Try to open existing spreadsheet
            try:
                spreadsheet = self.gspread_client.open(spreadsheet_name)
                print(f"Found existing spreadsheet: {spreadsheet.title}")
            except gspread.SpreadsheetNotFound:
                print("Creating new spreadsheet...")
                spreadsheet = self.gspread_client.create(spreadsheet_name)
                print(f"Created new spreadsheet: {spreadsheet.title}")
            
            # Get or create worksheet
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                print(f"Found existing worksheet: {worksheet.title}")
            except gspread.WorksheetNotFound:
                print("Creating new worksheet...")
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=30)
                print(f"Created new worksheet: {worksheet.title}")
            
            # Clear existing data and update
            print("Updating worksheet data...")
            worksheet.clear()
            
            if data:
                headers = list(data[0].keys())
                rows = [headers]
                
                for row in data:
                    row_values = []
                    for header in headers:
                        value = row.get(header, '')
                        if isinstance(value, (list, dict)):
                            value = json.dumps(value, ensure_ascii=False)
                        row_values.append(str(value))
                    rows.append(row_values)
                
                worksheet.update('A1', rows)
                print(f"Updated {len(rows)} rows successfully")
            
            return spreadsheet.url
            
        except Exception as e:
            print(f'Error in quick update: {e}')
            return None
    
    def smart_update_spreadsheet(self, spreadsheet_name: str, new_data: List[Dict], 
                                sheet_name: str = "Inventory") -> Optional[str]:
        """Smart update: only adds new rows, doesn't overwrite existing data"""
        if not self.gspread_client:
            print("Error: gspread client not initialized")
            return None
            
        try:
            print(f"Smart update of spreadsheet: {spreadsheet_name}")
            
            # Try to open existing spreadsheet
            try:
                spreadsheet = self.gspread_client.open(spreadsheet_name)
                print(f"Found existing spreadsheet: {spreadsheet.title}")
            except gspread.SpreadsheetNotFound:
                print("Creating new spreadsheet...")
                spreadsheet = self.gspread_client.create(spreadsheet_name)
                print(f"Created new spreadsheet: {spreadsheet.title}")
            
            # Get or create worksheet
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                print(f"Found existing worksheet: {worksheet.title}")
            except gspread.WorksheetNotFound:
                print("Creating new worksheet...")
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=30)
                print(f"Created new worksheet: {worksheet.title}")
            
            # Get existing data to check for duplicates
            try:
                existing_data = worksheet.get_all_records()
                existing_skus = set()
                if existing_data:
                    # Find the SKU column (could be 'SKU', 'sku', or similar)
                    sku_column = None
                    for col in existing_data[0].keys():
                        if 'sku' in col.lower():
                            sku_column = col
                            break
                    
                    if sku_column:
                        existing_skus = {str(row[sku_column]).strip() for row in existing_data if row[sku_column]}
                        print(f"Found {len(existing_skus)} existing SKUs in spreadsheet")
                    else:
                        print("Warning: No SKU column found in existing data")
                
            except Exception as e:
                print(f"Warning: Could not read existing data: {e}")
                existing_data = []
                existing_skus = set()
            
            # Filter out data that already exists
            new_rows = []
            added_count = 0
            skipped_count = 0
            
            if new_data:
                headers = list(new_data[0].keys())
                
                # Find SKU column in new data
                sku_column_new = None
                for col in headers:
                    if 'sku' in col.lower():
                        sku_column_new = col
                        break
                
                if sku_column_new:
                    for row in new_data:
                        sku_value = str(row.get(sku_column_new, '')).strip()
                        if sku_value and sku_value not in existing_skus:
                            # This is a new SKU, add it
                            row_values = []
                            for header in headers:
                                value = row.get(header, '')
                                if isinstance(value, (list, dict)):
                                    value = json.dumps(value, ensure_ascii=False)
                                row_values.append(str(value))
                            new_rows.append(row_values)
                            added_count += 1
                        else:
                            skipped_count += 1
                    
                    if new_rows:
                        # Add headers if this is a new spreadsheet
                        if not existing_data:
                            new_rows.insert(0, headers)
                        
                        # Find the next empty row
                        next_row = len(existing_data) + 2 if existing_data else 1  # +2 because existing_data doesn't include headers
                        
                        # Update the worksheet with new rows
                        worksheet.update(f'A{next_row}', new_rows)
                        print(f"Added {added_count} new rows, skipped {skipped_count} existing SKUs")
                    else:
                        print("No new SKUs to add - all data already exists in spreadsheet")
                else:
                    print("Warning: No SKU column found in new data")
            
            return spreadsheet.url
            
        except Exception as e:
            print(f'Error in smart update: {e}')
            import traceback
            traceback.print_exc()
            return None
    
    def upload_sku_to_drive(self, sku: str, local_sku_folder: str, 
                           chinese_description: str = "", reference_number: str = "") -> Dict:
        """Upload complete SKU folder to Google Drive"""
        if not self.drive_service:
            return {"success": False, "error": "Google Drive not authenticated"}
        
        try:
            # Use consistent main folder name (no timestamp)
            main_folder_name = "SKU_Generator"
            
            # Try to find existing main folder first
            main_folder_id = self.find_folder_by_name(main_folder_name)
            if not main_folder_id:
                # Create main folder only if it doesn't exist
                main_folder_id = self.create_folder(main_folder_name)
                if not main_folder_id:
                    return {"success": False, "error": "Failed to create main folder"}
                print(f"Created new main folder: {main_folder_name}")
            else:
                print(f"Using existing main folder: {main_folder_name}")
            
            # Check if SKU folder already exists
            existing_sku_folder_id = self.find_folder_by_name(sku, main_folder_id)
            if existing_sku_folder_id:
                print(f"SKU folder '{sku}' already exists, using existing folder")
                sku_folder_id = existing_sku_folder_id
            else:
                # Create SKU-specific folder under the main folder
                sku_folder_id = self.create_folder(sku, main_folder_id)
                if not sku_folder_id:
                    return {"success": False, "error": "Failed to create SKU folder"}
                print(f"Created new SKU folder: {sku}")
            
            uploaded_files = []
            
            # Upload all files from local SKU folder (local_sku_folder is already the full path)
            if os.path.exists(local_sku_folder):
                for filename in os.listdir(local_sku_folder):
                    file_path = os.path.join(local_sku_folder, filename)
                    if os.path.isfile(file_path):
                        file_id = self.upload_file(file_path, sku_folder_id)
                        if file_id:
                            uploaded_files.append({
                                'name': filename,
                                'drive_id': file_id,
                                'local_path': file_path
                            })
            
            # Create folder structure info
            folder_info = {
                'sku': sku,
                'reference_number': reference_number,
                'chinese_description': chinese_description,
                'upload_date': datetime.now().isoformat(),
                'files': uploaded_files,
                'folder_id': sku_folder_id,
                'main_folder_id': main_folder_id
            }
            
            # Save folder info as JSON
            folder_info_path = os.path.join(local_sku_folder, f"{sku}_description.json")
            with open(folder_info_path, 'w', encoding='utf-8') as f:
                json.dump(folder_info, f, indent=2, ensure_ascii=False)
            
            # Upload the folder info file
            self.upload_file(folder_info_path, sku_folder_id)
            
            return {
                "success": True,
                "message": f"SKU {sku} uploaded to Google Drive successfully",
                "main_folder_id": main_folder_id,
                "sku_folder_id": sku_folder_id,
                "uploaded_files": uploaded_files,
                "folder_info": folder_info
            }
            
        except Exception as e:
            return {"success": False, "error": f"Upload failed: {str(e)}"}
    
    def sync_csv_to_sheets(self, csv_path: str, spreadsheet_name: str = None) -> Dict:
        """Sync CSV data to Google Sheets"""
        if not self.gspread_client:
            return {"success": False, "error": "Google Sheets not authenticated"}
        
        try:
            # Read CSV data
            data = []
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                data = list(reader)
            
            if not data:
                return {"success": False, "error": "No data found in CSV"}
            
            # Use default spreadsheet name if none provided
            if not spreadsheet_name:
                spreadsheet_name = f"SKU_Inventory"
            
            # Use smart update method to only add new rows
            spreadsheet_url = self.smart_update_spreadsheet(spreadsheet_name, data)
            
            if spreadsheet_url:
                return {
                    "success": True,
                    "message": f"CSV synced to Google Sheets successfully",
                    "spreadsheet_url": spreadsheet_url,
                    "spreadsheet_name": spreadsheet_name,
                    "rows_synced": len(data)
                }
            else:
                return {"success": False, "error": "Failed to update Google Sheets"}
                
        except Exception as e:
            return {"success": False, "error": f"Sync failed: {str(e)}"}

def test_google_drive_integration():
    """Test function for Google Drive integration"""
    if not GOOGLE_DRIVE_AVAILABLE:
        print("Google Drive libraries not available. Install requirements first.")
        return
    
    # Test with credentials file (if available)
    credentials_path = 'credentials.json'  # User needs to provide this
    if os.path.exists(credentials_path):
        integration = GoogleDriveIntegration(credentials_path)
        print("Google Drive integration initialized successfully!")
        return integration
    else:
        print("No credentials.json found. Please set up Google Drive API credentials.")
        return None

if __name__ == "__main__":
    test_google_drive_integration()
