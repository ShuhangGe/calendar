#!/usr/bin/env python3
"""
Quick start script for Calendar Assistant
"""

import os
import sys
import subprocess

def main():
    print("🚀 Starting Calendar Assistant...")
    
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    
    if not os.path.exists(backend_dir):
        print("❌ Backend directory not found!")
        sys.exit(1)
    
    os.chdir(backend_dir)
    
    print(f"📂 Working directory: {os.getcwd()}")
    
    # Check if requirements are installed
    try:
        import fastapi
        import uvicorn
        print("✅ Dependencies appear to be installed")
    except ImportError:
        print("⚠️  Missing dependencies. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Start the application
    print("\n🌟 Calendar Assistant is starting...")
    print("📱 Web interface will be available at: http://localhost:8000")
    print("📚 API documentation will be available at: http://localhost:8000/docs")
    print("\n🔧 To stop the server, press Ctrl+C")
    print("-" * 60)
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Calendar Assistant stopped. Goodbye!")

if __name__ == "__main__":
    main() 