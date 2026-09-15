import sys
import os

try:
    from app.main import app
    print("FastAPI app imported successfully!")
except Exception as e:
    print(f"Error importing app: {e}")
