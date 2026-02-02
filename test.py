"""
Script to check available Gemini models for your API key
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def check_available_models():
    """Check and list all available Gemini models."""
    try:
        from google import genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            print("❌ Error: GEMINI_API_KEY not found in environment variables")
            return
        
        # Initialize client
        client = genai.Client(api_key=api_key)
        
        print("🔍 Fetching available Gemini models...\n")
        
        # List all available models
        models = client.models.list()
        
        print("✅ Available Models:")
        print("-" * 60)
        
        available_models = []
        for model in models:
            model_name = model.name
            # Extract just the model ID (e.g., "gemini-1.5-flash" from "models/gemini-1.5-flash")
            model_id = model_name.split('/')[-1] if '/' in model_name else model_name
            available_models.append(model_id)
            print(f"  • {model_id}")
        
        print("-" * 60)
        print(f"\n📊 Total models available: {len(available_models)}\n")
        
        # Show current model being used
        current_model = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
        print(f"🎯 Current model in use: {current_model}")
        
        if current_model in available_models:
            print("   ✅ Current model is available")
        else:
            print("   ⚠️  Current model might not be available")
        
        print("\n💡 To change the model, update GEMINI_MODEL in config.py")
        
    except ImportError:
        print("❌ Error: google-genai not installed")
        print("   Install it with: pip install google-genai")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check your GEMINI_API_KEY in .env file")
        print("   2. Make sure your API key is valid and has model access")
        print("   3. Check your internet connection")

if __name__ == '__main__':
    check_available_models()