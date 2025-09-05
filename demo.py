import asyncio
from playwright.async_api import async_playwright


async def capture_screenshots(base_url: str = "http://localhost:8501") -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        # Home page
        await page.goto(base_url, wait_until="networkidle")
        await page.screenshot(path="assets/screenshots/home.png", full_page=True)

        # Optional: navigate to chat area if anchor exists
        # Streamlit doesn't expose routes, but we can scroll for a broader view
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.screenshot(path="assets/screenshots/chat.png", full_page=True)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(capture_screenshots())

#!/usr/bin/env python3
"""
Demo script for the Intelligent Chat Interface
This script demonstrates the core functionality without the Streamlit UI
"""
import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def demo_resume_parsing():
    """Demonstrate resume parsing functionality"""
    print("🔍 Demo: Resume Parsing")
    print("-" * 30)

    try:
        from backend.resume_parser import ResumeParser

        parser = ResumeParser()

        # Use sample resume text
        sample_text = """
        JOHN SMITH
        Software Engineer
        john.smith@email.com | (555) 123-4567 | San Francisco, CA
        LinkedIn: linkedin.com/in/johnsmith | GitHub: github.com/johnsmith

        PROFESSIONAL SUMMARY
        Experienced software engineer with 5+ years of experience in full-stack development. 
        Specialized in Python, JavaScript, and cloud technologies.

        TECHNICAL SKILLS
        Programming Languages: Python, JavaScript, Java, C++, SQL
        Frameworks: React, Node.js, Django, Flask, Spring Boot
        Cloud Platforms: AWS, Azure, Google Cloud Platform
        Databases: PostgreSQL, MongoDB, Redis, MySQL

        PROFESSIONAL EXPERIENCE
        Senior Software Engineer | TechCorp Inc. | 2020 - Present
        • Led development of microservices architecture serving 1M+ users
        • Implemented CI/CD pipelines reducing deployment time by 60%
        • Technologies: Python, React, AWS, Docker, Kubernetes

        Software Engineer | StartupXYZ | 2018 - 2020
        • Developed full-stack web applications using Python and JavaScript
        • Built REST APIs and integrated third-party services
        • Technologies: Django, React, PostgreSQL, Redis

        EDUCATION
        Bachelor of Science in Computer Science
        University of California, Berkeley | 2013 - 2017
        """

        parsed_data = parser._parse_text(sample_text)

        print(f"Name: {parsed_data['name']}")
        print(f"Email: {parsed_data['email']}")
        print(f"Phone: {parsed_data['phone']}")
        print(f"Skills: {', '.join(parsed_data['skills'][:5])}")
        print(f"Experience: {parsed_data['experience_years']} years")
        print(f"Current Position: {parsed_data['current_position']}")
        print(f"Current Company: {parsed_data['current_company']}")

        return parsed_data

    except Exception as e:
        print(f"❌ Error in resume parsing demo: {e}")
        return None


def demo_database_operations(candidate_data):
    """Demonstrate database operations"""
    print("\n💾 Demo: Database Operations")
    print("-" * 30)

    try:
        from backend.database_manager import DatabaseManager

        # Use test database
        db_manager = DatabaseManager("demo_database.db")

        # Add candidate
        candidate_id = db_manager.add_candidate(candidate_data)
        print(f"✅ Added candidate with ID: {candidate_id}")

        # Retrieve candidate
        retrieved = db_manager.get_candidate(candidate_id)
        print(f"✅ Retrieved candidate: {retrieved['name']}")

        # Search candidates
        search_results = db_manager.search_candidates("Python")
        print(f"✅ Found {len(search_results)} candidates with 'Python' skills")

        # Clean up
        os.remove("demo_database.db")
        print("✅ Demo database cleaned up")

        return candidate_id

    except Exception as e:
        print(f"❌ Error in database demo: {e}")
        return None


def demo_linkedin_scraping():
    """Demonstrate LinkedIn scraping functionality"""
    print("\n🔗 Demo: LinkedIn Scraping")
    print("-" * 30)

    try:
        from backend.linkedin_scraper import LinkedInScraper

        scraper = LinkedInScraper()

        # Test skill extraction
        test_text = "Experienced Python developer with React, AWS, and Docker skills"
        skills = scraper._extract_skills_from_text(test_text)

        print(f"✅ Extracted skills: {', '.join(skills)}")

        # Test profile data merging
        linkedin_data = {
            "name": "John Smith",
            "title": "Senior Software Engineer",
            "company": "TechCorp Inc.",
            "location": "San Francisco, CA",
            "skills": ["Python", "React", "AWS", "Docker"],
            "summary": "Experienced software engineer with expertise in full-stack development.",
        }

        resume_data = {
            "name": "John Smith",
            "email": "john.smith@email.com",
            "phone": "(555) 123-4567",
            "skills": ["Python", "JavaScript", "Django", "PostgreSQL"],
            "experience_years": 5,
        }

        merged_data = scraper.merge_with_resume_data(linkedin_data, resume_data)

        print(f"✅ Merged data for: {merged_data['name']}")
        print(f"   Combined skills: {', '.join(merged_data['skills'])}")
        print(f"   Experience: {merged_data['experience_years']} years")

        return merged_data

    except Exception as e:
        print(f"❌ Error in LinkedIn scraping demo: {e}")
        return None


def demo_ai_form_generation(candidate_data):
    """Demonstrate AI form generation"""
    print("\n🤖 Demo: AI Form Generation")
    print("-" * 30)

    try:
        from backend.ai_form_filler import AIFormFiller

        # Check if OpenAI API key is available
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            print("⚠️  OpenAI API key not found. Using mock form generation.")

            # Create a mock form
            mock_form = {
                "personal_information": {
                    "full_name": candidate_data.get("name", "N/A"),
                    "email": candidate_data.get("email", "N/A"),
                    "phone": candidate_data.get("phone", "N/A"),
                    "location": candidate_data.get("location", "N/A"),
                },
                "professional_summary": {
                    "summary": candidate_data.get(
                        "summary", "Professional software engineer"
                    ),
                    "current_position": candidate_data.get(
                        "current_position", "Software Engineer"
                    ),
                    "current_company": candidate_data.get(
                        "current_company", "Tech Company"
                    ),
                    "experience_years": candidate_data.get("experience_years", 0),
                },
                "skills_assessment": {
                    "technical_skills": ", ".join(candidate_data.get("skills", []))
                },
            }

            print("✅ Mock form generated successfully")
            print(f"   Form sections: {list(mock_form.keys())}")

            return mock_form
        else:
            # Use real AI form generation
            ai_form_filler = AIFormFiller(api_key)

            # Load form template
            with open("data/sample_hr_form.json", "r") as f:
                form_template = json.load(f)

            filled_form = ai_form_filler.generate_hr_form(candidate_data, form_template)

            print("✅ AI-generated form created successfully")
            print(
                f"   Form type: {filled_form.get('_metadata', {}).get('form_type', 'Unknown')}"
            )

            return filled_form

    except Exception as e:
        print(f"❌ Error in AI form generation demo: {e}")
        return None


def demo_export_functionality(form_data):
    """Demonstrate export functionality"""
    print("\n📄 Demo: Export Functionality")
    print("-" * 30)

    try:
        from backend.ai_form_filler import AIFormFiller

        # Create a temporary AI form filler instance
        ai_form_filler = AIFormFiller(api_key=os.getenv("OPENAI_API_KEY", "dummy"))

        # Test PDF export
        try:
            os.makedirs("exports", exist_ok=True)
            pdf_path = "exports/demo_form.pdf"
            ai_form_filler.export_form_to_pdf(form_data, pdf_path)
            print(f"✅ PDF exported to: {pdf_path}")
        except Exception as e:
            print(f"⚠️  PDF export failed: {e}")

        # Test Excel export
        try:
            excel_path = "exports/demo_form.xlsx"
            ai_form_filler.export_form_to_excel(form_data, excel_path)
            print(f"✅ Excel exported to: {excel_path}")
        except Exception as e:
            print(f"⚠️  Excel export failed: {e}")

        # Test JSON export
        json_path = "exports/demo_form.json"
        with open(json_path, "w") as f:
            json.dump(form_data, f, indent=2)
        print(f"✅ JSON exported to: {json_path}")

    except Exception as e:
        print(f"❌ Error in export demo: {e}")


def main():
    """Main demo function"""
    print("🎬 Intelligent Chat Interface Demo")
    print("=" * 50)
    print("This demo showcases the core functionality of the system")
    print("without requiring the Streamlit UI.\n")

    # Demo 1: Resume Parsing
    candidate_data = demo_resume_parsing()
    if not candidate_data:
        print("❌ Demo failed at resume parsing stage")
        return

    # Demo 2: Database Operations
    candidate_id = demo_database_operations(candidate_data)
    if not candidate_id:
        print("❌ Demo failed at database operations stage")
        return

    # Demo 3: LinkedIn Scraping
    linkedin_data = demo_linkedin_scraping()
    if not linkedin_data:
        print("❌ Demo failed at LinkedIn scraping stage")
        return

    # Demo 4: AI Form Generation
    form_data = demo_ai_form_generation(candidate_data)
    if not form_data:
        print("❌ Demo failed at AI form generation stage")
        return

    # Demo 5: Export Functionality
    demo_export_functionality(form_data)

    print("\n" + "=" * 50)
    print("🎉 Demo completed successfully!")
    print("=" * 50)
    print("\nTo run the full application with UI:")
    print("  python run.py")
    print("  or")
    print("  streamlit run app.py")
    print("\nFor more information, see README.md")


if __name__ == "__main__":
    main()
