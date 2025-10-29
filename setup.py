
"""
Face Recognition Setup Script for Employee Clocking System
"""

import os
import subprocess
import sys

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ["encodings", "logs", "training_images"]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"📁 Directory already exists: {directory}")

def test_face_recognition():
    """Test if face_recognition library works"""
    try:
        import face_recognition
        import cv2
        import numpy as np
        print("Face recognition libraries imported successfully!")
        return True
    except ImportError as e:
        print(f"Error importing libraries: {e}")
        return False

def main():
    """Main setup function"""
    print("Setting up Face Recognition for Employee Clocking System")
    print("=" * 60)
    
    # Create directories
    create_directories()
    
    # Install requirements
    if not install_requirements():
        print("Setup failed during package installation")
        return False
    
    # Test imports
    if not test_face_recognition():
        print("Setup failed during library testing")
        return False

    
    return True

if __name__ == "__main__":
    main()