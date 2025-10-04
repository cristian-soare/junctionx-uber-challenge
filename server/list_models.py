#!/usr/bin/env python3
"""List available Gemini models."""

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def list_models():
    """List available Gemini models."""
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("❌ Please set your GEMINI_API_KEY in .env file")
        return
    
    genai.configure(api_key=gemini_api_key)
    
    print("🔍 Available Gemini models:")
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"✅ {model.name}")
        else:
            print(f"❌ {model.name} (does not support generateContent)")

if __name__ == "__main__":
    list_models()