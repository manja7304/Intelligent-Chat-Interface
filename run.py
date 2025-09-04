#!/usr/bin/env python3
"""
Launch script for the Intelligent Chat Interface
"""
import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.10+"""
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def check_dependencies():
    """Check if required dependencies are installed"""
    # Package name -> import name mapping
    required_packages = {
        "streamlit": "streamlit",
        "openai": "openai",
        "pdfplumber": "pdfplumber",
        "spacy": "spacy",
        "beautifulsoup4": "bs4",  # beautifulsoup4 is imported as bs4
        "requests": "requests",
        "pandas": "pandas",
        "reportlab": "reportlab",
        "openpyxl": "openpyxl",
    }

    missing_packages = []

    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name} is installed")
        except ImportError:
            missing_packages.append(package_name)
            print(f"❌ {package_name} is missing")

    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements.txt")
        return False

    return True


def check_spacy_model():
    """Check if spaCy English model is installed"""
    try:
        import spacy

        nlp = spacy.load("en_core_web_sm")
        print("✅ spaCy English model is installed")
        return True
    except OSError:
        print("❌ spaCy English model is missing")
        print("Install it with: python -m spacy download en_core_web_sm")
        return False


def create_directories():
    """Create required directories if they don't exist"""
    directories = ["data", "exports", "logs"]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Directory {directory} ready")


def check_env_file():
    """Check if .env file exists"""
    if os.path.exists(".env"):
        print("✅ .env file found")
        return True
    else:
        print("⚠️  .env file not found")
        print("Create a .env file with your API keys")
        return False


def main():
    """Main launch function"""
    print("🚀 Intelligent Chat Interface Launcher")
    print("=" * 50)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies first")
        sys.exit(1)

    # Check spaCy model
    if not check_spacy_model():
        print("\n❌ Please install spaCy model first")
        sys.exit(1)

    # Create directories
    create_directories()

    # Check .env file
    check_env_file()

    print("\n" + "=" * 50)
    print("🎉 All checks passed! Starting the application...")
    print("=" * 50)

    # Launch Streamlit app
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app.py",
                "--server.port=8501",
                "--server.address=localhost",
            ]
        )
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error launching application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
