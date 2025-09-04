"""
Test script for the Intelligent Chat Interface
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")

    try:
        import streamlit as st

        print("✅ Streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
        return False

    try:
        import openai

        print("✅ OpenAI imported successfully")
    except ImportError as e:
        print(f"❌ OpenAI import failed: {e}")
        return False

    try:
        import pdfplumber

        print("✅ pdfplumber imported successfully")
    except ImportError as e:
        print(f"❌ pdfplumber import failed: {e}")
        return False

    try:
        import spacy

        print("✅ spaCy imported successfully")
    except ImportError as e:
        print(f"❌ spaCy import failed: {e}")
        return False

    try:
        from backend.database_manager import DatabaseManager

        print("✅ DatabaseManager imported successfully")
    except ImportError as e:
        print(f"❌ DatabaseManager import failed: {e}")
        return False

    try:
        from backend.resume_parser import ResumeParser

        print("✅ ResumeParser imported successfully")
    except ImportError as e:
        print(f"❌ ResumeParser import failed: {e}")
        return False

    try:
        from backend.linkedin_scraper import LinkedInScraper

        print("✅ LinkedInScraper imported successfully")
    except ImportError as e:
        print(f"❌ LinkedInScraper import failed: {e}")
        return False

    try:
        from backend.ai_form_filler import AIFormFiller

        print("✅ AIFormFiller imported successfully")
    except ImportError as e:
        print(f"❌ AIFormFiller import failed: {e}")
        return False

    return True


def test_database():
    """Test database initialization"""
    print("\nTesting database...")

    try:
        from backend.database_manager import DatabaseManager

        # Create a test database
        db_manager = DatabaseManager("test_database.db")
        print("✅ Database initialized successfully")

        # Test adding a candidate
        test_candidate = {
            "name": "Test Candidate",
            "email": "test@example.com",
            "phone": "555-1234",
            "skills": ["Python", "JavaScript"],
            "experience_years": 3,
        }

        candidate_id = db_manager.add_candidate(test_candidate)
        print(f"✅ Test candidate added with ID: {candidate_id}")

        # Test retrieving candidate
        retrieved = db_manager.get_candidate(candidate_id)
        if retrieved and retrieved["name"] == "Test Candidate":
            print("✅ Candidate retrieval successful")
        else:
            print("❌ Candidate retrieval failed")
            return False

        # Clean up test database
        os.remove("test_database.db")
        print("✅ Test database cleaned up")

        return True

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def test_resume_parser():
    """Test resume parser functionality"""
    print("\nTesting resume parser...")

    try:
        from backend.resume_parser import ResumeParser

        parser = ResumeParser()
        print("✅ ResumeParser initialized successfully")

        # Test with sample resume text
        sample_text = """
        John Doe
        Software Engineer
        john.doe@email.com | (555) 123-4567
        
        SKILLS
        Python, JavaScript, React, Node.js, AWS
        
        EXPERIENCE
        Senior Software Engineer at TechCorp (2020-Present)
        Software Engineer at StartupXYZ (2018-2020)
        """

        # Test text parsing
        parsed_data = parser._parse_text(sample_text)

        if parsed_data["name"] == "John Doe" and "Python" in parsed_data["skills"]:
            print("✅ Resume parsing successful")
        else:
            print("❌ Resume parsing failed")
            return False

        return True

    except Exception as e:
        print(f"❌ Resume parser test failed: {e}")
        return False


def test_linkedin_scraper():
    """Test LinkedIn scraper functionality"""
    print("\nTesting LinkedIn scraper...")

    try:
        from backend.linkedin_scraper import LinkedInScraper

        scraper = LinkedInScraper()
        print("✅ LinkedInScraper initialized successfully")

        # Test skill extraction
        test_text = "Experienced Python developer with React and AWS skills"
        skills = scraper._extract_skills_from_text(test_text)

        if "Python" in skills and "React" in skills:
            print("✅ Skill extraction successful")
        else:
            print("❌ Skill extraction failed")
            return False

        return True

    except Exception as e:
        print(f"❌ LinkedIn scraper test failed: {e}")
        return False


def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")

    try:
        import config

        # Check if config attributes exist
        required_attrs = ["OPENAI_API_KEY", "APP_TITLE", "APP_VERSION"]
        for attr in required_attrs:
            if hasattr(config, attr):
                print(f"✅ Config attribute {attr} found")
            else:
                print(f"❌ Config attribute {attr} missing")
                return False

        return True

    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False


def test_directories():
    """Test required directories exist"""
    print("\nTesting directories...")

    required_dirs = ["data", "exports", "logs", "backend"]

    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✅ Directory {dir_name} exists")
        else:
            print(f"❌ Directory {dir_name} missing")
            return False

    return True


def main():
    """Run all tests"""
    print("🧪 Running Intelligent Chat Interface Tests\n")

    tests = [
        ("Import Tests", test_imports),
        ("Directory Tests", test_directories),
        ("Config Tests", test_config),
        ("Database Tests", test_database),
        ("Resume Parser Tests", test_resume_parser),
        ("LinkedIn Scraper Tests", test_linkedin_scraper),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running {test_name}")
        print("=" * 50)

        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")

    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")
    print("=" * 50)

    if passed == total:
        print("🎉 All tests passed! The application is ready to use.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
