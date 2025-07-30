#!/usr/bin/env python3
"""
Launcher for Streamlit SKU Generator App (Gemini API only)
"""

import subprocess
import sys
import os

def main():
    """Launch the Streamlit app"""
    try:
        # Check if streamlit is installed
        import streamlit
        print("✅ Streamlit is installed")
    except ImportError:
        print("❌ Streamlit not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
    
    # Check if required packages are installed
    try:
        import google.generativeai
        from PIL import Image
        print("✅ Google Generative AI and PIL are installed")
    except ImportError:
        print("❌ Required packages not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai", "pillow"])
    
    # Launch the app
    print("🚀 Launching SKU Generator Web App (Gemini API)...")
    print("📱 Open your browser to the URL shown below")
    print("🔗 The app will be available at: http://localhost:8501")
    print("⏹️  Press Ctrl+C to stop the app")
    print("-" * 50)
    
    # Run streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
        "--server.port", "8501",
        "--server.address", "localhost"
    ])

if __name__ == "__main__":
    main() 