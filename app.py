"""
Intelligent Chat Interface for HR Candidate Profiling
Main Streamlit application
"""

import streamlit as st
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd

# Import backend modules
from backend.database_manager import DatabaseManager
from backend.resume_parser import ResumeParser
from backend.linkedin_scraper import LinkedInScraper
from backend.ai_form_filler import AIFormFiller
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Initialize session state early
if "messages" not in st.session_state:
    st.session_state.messages = []
if "candidates" not in st.session_state:
    st.session_state.candidates = []
if "current_candidate" not in st.session_state:
    st.session_state.current_candidate = None

# Page configuration
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern UI
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        max-width: 80%;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: auto;
        text-align: right;
    }
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: auto;
    }
    .success-message {
        background-color: #e8f5e8;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        margin: 1rem 0;
    }
    .candidate-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #fafafa;
    }
    .skill-tag {
        background-color: #1f77b4;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin: 0.2rem;
        display: inline-block;
    }
</style>
""",
    unsafe_allow_html=True,
)


def process_user_input(
    prompt: str,
    db_manager: DatabaseManager,
    resume_parser: ResumeParser,
    linkedin_scraper: LinkedInScraper,
    ai_form_filler: AIFormFiller,
) -> str:
    """Process user input and generate appropriate response"""

    prompt_lower = prompt.lower()

    # Search for candidates
    if any(
        keyword in prompt_lower
        for keyword in ["search", "find", "look for", "candidates"]
    ):
        try:
            # Extract search query
            search_query = (
                prompt.replace("search", "")
                .replace("find", "")
                .replace("look for", "")
                .strip()
            )
            if not search_query:
                search_query = prompt

            candidates = db_manager.search_candidates(search_query)

            if candidates:
                response = f"Found {len(candidates)} candidate(s) matching '{search_query}':\n\n"
                for i, candidate in enumerate(
                    candidates[:5], 1
                ):  # Show first 5 results
                    response += f"{i}. **{candidate['name']}** - {candidate.get('current_position', 'N/A')} at {candidate.get('current_company', 'N/A')}\n"
                    response += (
                        f"   Skills: {', '.join(candidate.get('skills', [])[:5])}\n\n"
                    )
            else:
                response = f"No candidates found matching '{search_query}'. Try uploading a resume or searching LinkedIn."

            return response

        except Exception as e:
            return f"Error searching candidates: {e}"

    # Generate forms
    elif any(keyword in prompt_lower for keyword in ["form", "generate", "create"]):
        if (
            hasattr(st.session_state, "current_candidate")
            and st.session_state.current_candidate
        ):
            try:
                if "interview" in prompt_lower:
                    form = ai_form_filler.generate_interview_form(
                        st.session_state.current_candidate
                    )
                    form_type = "interview assessment"
                else:
                    form = ai_form_filler.generate_standard_hr_form(
                        st.session_state.current_candidate
                    )
                    form_type = "standard HR"

                st.session_state.generated_form = form
                return f"✅ Generated {form_type} form for {st.session_state.current_candidate['name']}!"

            except Exception as e:
                return f"Error generating form: {e}"
        else:
            return "Please select a candidate first by uploading a resume or searching LinkedIn."

    # General help
    elif any(
        keyword in prompt_lower for keyword in ["help", "what can you do", "commands"]
    ):
        return """
        🤖 **I can help you with:**
        
        📁 **Resume Processing:**
        - Upload PDF resumes and extract candidate information
        - Parse skills, experience, education, and contact details
        
        🔗 **LinkedIn Integration:**
        - Extract candidate data from LinkedIn profiles
        - Merge LinkedIn and resume data intelligently
        
        📋 **Form Generation:**
        - Generate standard HR forms
        - Create interview assessment forms
        - Export forms to PDF or Excel
        
        🔍 **Candidate Search:**
        - Search through your candidate database
        - Find candidates by name, skills, or company
        
        **Try saying:**
        - "Search for Python developers"
        - "Generate a form for the current candidate"
        - "Show me all candidates"
        """

    # Default response
    else:
        return """
        I'm here to help you manage candidate information and generate HR forms! 
        
        You can:
        - Upload a resume (PDF)
        - Enter a LinkedIn profile URL
        - Search for candidates
        - Generate HR forms
        - Ask for help
        
        What would you like to do?
        """


# Initialize components
@st.cache_resource
def initialize_components():
    """Initialize all backend components"""
    try:
        db_manager = DatabaseManager()
        resume_parser = ResumeParser()
        linkedin_scraper = LinkedInScraper(
            email=config.LINKEDIN_EMAIL,
            password=config.LINKEDIN_PASSWORD,
            serpapi_key=config.SERPAPI_KEY,
        )
        ai_form_filler = AIFormFiller(api_key=config.OPENAI_API_KEY)

        return db_manager, resume_parser, linkedin_scraper, ai_form_filler
    except Exception as e:
        st.error(f"Error initializing components: {e}")
        return None, None, None, None


# Main header
st.markdown(f'<h1 class="main-header">{config.APP_TITLE}</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🤖 AI Assistant")
    st.markdown("---")

    # API Key configuration
    st.subheader("Configuration")
    openai_key = st.text_input(
        "OpenAI API Key",
        value=config.OPENAI_API_KEY,
        type="password",
        help="Enter your OpenAI API key to enable AI features",
    )

    if openai_key != config.OPENAI_API_KEY:
        config.OPENAI_API_KEY = openai_key
        st.success("API key updated!")

    st.markdown("---")

    # Quick actions
    st.subheader("Quick Actions")
    if st.button("📊 View All Candidates"):
        st.session_state.show_candidates = True

    if st.button("📝 Generate Sample Form"):
        st.session_state.generate_sample = True

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Initialize components
db_manager, resume_parser, linkedin_scraper, ai_form_filler = initialize_components()

if db_manager is None:
    st.error("Failed to initialize application. Please check your configuration.")
    st.stop()

# Main chat interface
st.header("💬 Chat Interface")

# Display chat messages
if hasattr(st.session_state, "messages"):
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input(
    "Ask me about candidates, upload a resume, or search LinkedIn..."
):
    # Add user message to chat history
    if not hasattr(st.session_state, "messages"):
        st.session_state.messages = []
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Process the user input
    with st.chat_message("assistant"):
        response = process_user_input(
            prompt, db_manager, resume_parser, linkedin_scraper, ai_form_filler
        )
        st.markdown(response)

# File upload section
st.markdown("---")
st.header("📁 File Upload")

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader(
        "Upload Resume (PDF)",
        type=["pdf"],
        help="Upload a candidate's resume in PDF format",
    )

    if uploaded_file is not None:
        if st.button("🔍 Parse Resume"):
            with st.spinner("Parsing resume..."):
                try:
                    # Save uploaded file
                    file_path = f"data/{uploaded_file.name}"
                    os.makedirs("data", exist_ok=True)

                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # Parse resume
                    candidate_data = resume_parser.parse_resume(file_path)

                    # Add to database
                    candidate_id = db_manager.add_candidate(candidate_data)
                    candidate_data["id"] = candidate_id

                    st.session_state.current_candidate = candidate_data
                    if not hasattr(st.session_state, "messages"):
                        st.session_state.messages = []
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": f"✅ Successfully parsed resume for **{candidate_data['name']}**!\n\n**Extracted Information:**\n- Email: {candidate_data.get('email', 'N/A')}\n- Phone: {candidate_data.get('phone', 'N/A')}\n- Skills: {', '.join(candidate_data.get('skills', [])[:5])}\n- Experience: {candidate_data.get('experience_years', 0)} years",
                        }
                    )

                    st.rerun()

                except Exception as e:
                    st.error(f"Error parsing resume: {e}")

with col2:
    linkedin_url = st.text_input(
        "LinkedIn Profile URL",
        placeholder="https://linkedin.com/in/username",
        help="Enter a LinkedIn profile URL to extract candidate information",
    )

    if st.button("🔗 Extract LinkedIn Data"):
        if linkedin_url:
            with st.spinner("Extracting LinkedIn data..."):
                try:
                    linkedin_data = linkedin_scraper.get_profile_data(linkedin_url)

                    if linkedin_data:
                        # Add to database
                        candidate_id = db_manager.add_candidate(linkedin_data)
                        linkedin_data["id"] = candidate_id

                        st.session_state.current_candidate = linkedin_data
                        if not hasattr(st.session_state, "messages"):
                            st.session_state.messages = []
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": f"✅ Successfully extracted LinkedIn data for **{linkedin_data['name']}**!\n\n**Profile Information:**\n- Title: {linkedin_data.get('title', 'N/A')}\n- Company: {linkedin_data.get('company', 'N/A')}\n- Location: {linkedin_data.get('location', 'N/A')}\n- Skills: {', '.join(linkedin_data.get('skills', [])[:5])}",
                            }
                        )

                        st.rerun()
                    else:
                        st.error("Could not extract data from LinkedIn profile")

                except Exception as e:
                    st.error(f"Error extracting LinkedIn data: {e}")
        else:
            st.warning("Please enter a LinkedIn profile URL")

# Candidate management section
if (
    hasattr(st.session_state, "current_candidate")
    and st.session_state.current_candidate
):
    st.markdown("---")
    st.header("👤 Current Candidate")

    candidate = st.session_state.current_candidate

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Personal Information")
        st.write(f"**Name:** {candidate.get('name', 'N/A')}")
        st.write(f"**Email:** {candidate.get('email', 'N/A')}")
        st.write(f"**Phone:** {candidate.get('phone', 'N/A')}")
        st.write(f"**Location:** {candidate.get('location', 'N/A')}")

    with col2:
        st.subheader("Professional Information")
        st.write(f"**Current Position:** {candidate.get('current_position', 'N/A')}")
        st.write(f"**Current Company:** {candidate.get('current_company', 'N/A')}")
        st.write(f"**Experience:** {candidate.get('experience_years', 0)} years")
        st.write(f"**LinkedIn:** {candidate.get('linkedin_url', 'N/A')}")

    with col3:
        st.subheader("Skills")
        skills = candidate.get("skills", [])
        if skills:
            for skill in skills[:10]:  # Show first 10 skills
                st.markdown(
                    f'<span class="skill-tag">{skill}</span>', unsafe_allow_html=True
                )
        else:
            st.write("No skills extracted")

    # Form generation
    st.markdown("---")
    st.header("📋 Generate HR Forms")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📝 Generate Standard HR Form", use_container_width=True):
            if ai_form_filler and config.OPENAI_API_KEY:
                with st.spinner("Generating HR form..."):
                    try:
                        filled_form = ai_form_filler.generate_standard_hr_form(
                            candidate
                        )

                        # Save to database
                        form_id = db_manager.save_generated_form(
                            candidate["id"], "standard_hr_form", filled_form
                        )

                        st.session_state.generated_form = filled_form
                        st.success("✅ Standard HR form generated successfully!")

                    except Exception as e:
                        st.error(f"Error generating form: {e}")
            else:
                st.error("OpenAI API key required for form generation")

    with col2:
        if st.button("🎯 Generate Interview Form", use_container_width=True):
            if ai_form_filler and config.OPENAI_API_KEY:
                with st.spinner("Generating interview form..."):
                    try:
                        filled_form = ai_form_filler.generate_interview_form(candidate)

                        # Save to database
                        form_id = db_manager.save_generated_form(
                            candidate["id"], "interview_assessment", filled_form
                        )

                        st.session_state.generated_form = filled_form
                        st.success("✅ Interview form generated successfully!")

                    except Exception as e:
                        st.error(f"Error generating form: {e}")
            else:
                st.error("OpenAI API key required for form generation")

    # Display generated form
    if hasattr(st.session_state, "generated_form") and st.session_state.generated_form:
        st.markdown("---")
        st.header("📄 Generated Form")

        form = st.session_state.generated_form

        # Export options
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📄 Export to PDF"):
                try:
                    os.makedirs("exports", exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"exports/hr_form_{candidate['name'].replace(' ', '_')}_{timestamp}.pdf"

                    ai_form_filler.export_form_to_pdf(form, filename)
                    st.success(f"✅ Form exported to PDF: {filename}")

                except Exception as e:
                    st.error(f"Error exporting to PDF: {e}")

        with col2:
            if st.button("📊 Export to Excel"):
                try:
                    os.makedirs("exports", exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"exports/hr_form_{candidate['name'].replace(' ', '_')}_{timestamp}.xlsx"

                    ai_form_filler.export_form_to_excel(form, filename)
                    st.success(f"✅ Form exported to Excel: {filename}")

                except Exception as e:
                    st.error(f"Error exporting to Excel: {e}")

        with col3:
            if st.button("📋 Copy as JSON"):
                st.code(json.dumps(form, indent=2))

        # Display form content
        for section_name, section_data in form.items():
            if section_name.startswith("_"):
                continue

            with st.expander(f"📋 {section_name.replace('_', ' ').title()}"):
                for field_name, field_value in section_data.items():
                    if field_value:
                        st.write(
                            f"**{field_name.replace('_', ' ').title()}:** {field_value}"
                        )

# Candidates overview
if hasattr(st.session_state, "show_candidates") and getattr(
    st.session_state, "show_candidates", False
):
    st.markdown("---")
    st.header("👥 All Candidates")

    try:
        candidates = db_manager.get_all_candidates()

        if candidates:
            for candidate in candidates:
                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        st.write(f"**{candidate['name']}**")
                        st.write(
                            f"*{candidate.get('current_position', 'N/A')} at {candidate.get('current_company', 'N/A')}*"
                        )
                        st.write(
                            f"📧 {candidate.get('email', 'N/A')} | 📱 {candidate.get('phone', 'N/A')}"
                        )

                    with col2:
                        skills = candidate.get("skills", [])
                        if skills:
                            st.write(
                                f"**Skills:** {', '.join(skills[:3])}{'...' if len(skills) > 3 else ''}"
                            )

                    with col3:
                        if st.button(f"Select", key=f"select_{candidate['id']}"):
                            st.session_state.current_candidate = candidate
                            st.rerun()

                    st.markdown("---")
        else:
            st.info(
                "No candidates found. Upload a resume or search LinkedIn to get started."
            )

    except Exception as e:
        st.error(f"Error loading candidates: {e}")

# Footer
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        {config.APP_TITLE} v{config.APP_VERSION} | 
        Built with ❤️ using Streamlit and OpenAI
    </div>
    """,
    unsafe_allow_html=True,
)
