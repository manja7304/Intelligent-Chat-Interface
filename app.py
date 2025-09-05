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

# Theme and CSS (supports light/dark modes)
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False


def inject_theme_css():
    bg = "#0e1117" if st.session_state.dark_mode else "#ffffff"
    text = "#e0e0e0" if st.session_state.dark_mode else "#111111"
    card_bg = "#161a23" if st.session_state.dark_mode else "#fafafa"
    border = "#2a2f3a" if st.session_state.dark_mode else "#dddddd"
    primary = "#7aa2f7" if st.session_state.dark_mode else "#1f77b4"
    user_bg = "#1f3a5a" if st.session_state.dark_mode else "#e3f2fd"
    assistant_bg = "#1a1e27" if st.session_state.dark_mode else "#f5f5f5"

    st.markdown(
        f"""
<style>
    :root {{
        --bg: {bg};
        --text: {text};
        --card: {card_bg};
        --border: {border};
        --primary: {primary};
        --user-bg: {user_bg};
        --assistant-bg: {assistant_bg};
    }}
    .main-header {{
        font-size: 2.5rem;
        font-weight: bold;
        color: var(--primary);
        text-align: center;
        margin-bottom: 2rem;
    }}
    .stApp {{ background-color: var(--bg); color: var(--text); }}
    .chat-message {{
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        max-width: 80%;
        color: var(--text);
    }}
    .user-message {{
        background-color: var(--user-bg);
        margin-left: auto;
        text-align: right;
    }}
    .assistant-message {{
        background-color: var(--assistant-bg);
        margin-right: auto;
    }}
    .success-message {{
        background-color: #1b3c26;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        margin: 1rem 0;
    }}
    .error-message {{
        background-color: #3a1e20;
        border-left: 4px solid #f44336;
        padding: 1rem;
        margin: 1rem 0;
    }}
    .candidate-card {{
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: var(--card);
    }}
    .skill-tag {{
        background-color: var(--primary);
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin: 0.2rem;
        display: inline-block;
    }}
</style>
""",
        unsafe_allow_html=True,
    )


inject_theme_css()


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
    dark_mode = st.toggle("Dark mode", value=st.session_state.dark_mode)
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        inject_theme_css()
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

# Tabs: Chat, Upload, Candidates
chat_tab, upload_tab, candidates_tab = st.tabs(
    ["💬 Chat", "📁 Upload", "👥 Candidates"]
)

with chat_tab:
    st.header("Chat Interface")

    # Display chat messages with avatars
    if hasattr(st.session_state, "messages"):
        for message in st.session_state.messages:
            avatar = "🧑" if message["role"] == "user" else "🤖"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input(
        "Ask me about candidates, upload a resume, or search LinkedIn..."
    ):
        if not hasattr(st.session_state, "messages"):
            st.session_state.messages = []
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🤖"):
            response = process_user_input(
                prompt, db_manager, resume_parser, linkedin_scraper, ai_form_filler
            )
            st.markdown(response)

    # Current Candidate + Forms inside Chat tab for quick actions
    if (
        hasattr(st.session_state, "current_candidate")
        and st.session_state.current_candidate
    ):
        st.markdown("---")
        st.subheader("👤 Current Candidate")

        candidate = st.session_state.current_candidate
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Name:** {candidate.get('name', 'N/A')}")
            st.write(f"**Email:** {candidate.get('email', 'N/A')}")
            st.write(f"**Phone:** {candidate.get('phone', 'N/A')}")
            st.write(f"**Location:** {candidate.get('location', 'N/A')}")
        with col2:
            st.write(
                f"**Current Position:** {candidate.get('current_position', 'N/A')}"
            )
            st.write(f"**Current Company:** {candidate.get('current_company', 'N/A')}")
            st.write(f"**Experience:** {candidate.get('experience_years', 0)} years")
            st.write(f"**LinkedIn:** {candidate.get('linkedin_url', 'N/A')}")
        with col3:
            skills = candidate.get("skills", [])
            if skills:
                for skill in skills[:10]:
                    st.markdown(
                        f'<span class="skill-tag">{skill}</span>',
                        unsafe_allow_html=True,
                    )
            else:
                st.write("No skills extracted")

        st.markdown("---")
        st.subheader("📋 Generate HR Forms")
        g1, g2 = st.columns(2)
        with g1:
            if st.button("📝 Standard HR Form", use_container_width=True):
                if ai_form_filler and config.OPENAI_API_KEY:
                    with st.spinner("Generating HR form..."):
                        try:
                            filled_form = ai_form_filler.generate_standard_hr_form(
                                candidate
                            )
                            form_id = db_manager.save_generated_form(
                                candidate["id"], "standard_hr_form", filled_form
                            )
                            st.session_state.generated_form = filled_form
                            st.success("Generated standard HR form ✅")
                        except Exception as e:
                            st.error(f"Error generating form: {e}")
                else:
                    st.error("OpenAI API key required for form generation")
        with g2:
            if st.button("🎯 Interview Form", use_container_width=True):
                if ai_form_filler and config.OPENAI_API_KEY:
                    with st.spinner("Generating interview form..."):
                        try:
                            filled_form = ai_form_filler.generate_interview_form(
                                candidate
                            )
                            form_id = db_manager.save_generated_form(
                                candidate["id"], "interview_assessment", filled_form
                            )
                            st.session_state.generated_form = filled_form
                            st.success("Generated interview form ✅")
                        except Exception as e:
                            st.error(f"Error generating form: {e}")
                else:
                    st.error("OpenAI API key required for form generation")

        if (
            hasattr(st.session_state, "generated_form")
            and st.session_state.generated_form
        ):
            st.markdown("---")
            st.subheader("📄 Generated Form")
            form = st.session_state.generated_form
            e1, e2, e3 = st.columns(3)
            with e1:
                if st.button("📄 Export to PDF"):
                    try:
                        os.makedirs("exports", exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"exports/hr_form_{candidate['name'].replace(' ', '_')}_{timestamp}.pdf"
                        ai_form_filler.export_form_to_pdf(form, filename)
                        st.success(f"Exported to PDF: {filename}")
                    except Exception as e:
                        st.error(f"Error exporting to PDF: {e}")
            with e2:
                if st.button("📊 Export to Excel"):
                    try:
                        os.makedirs("exports", exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"exports/hr_form_{candidate['name'].replace(' ', '_')}_{timestamp}.xlsx"
                        ai_form_filler.export_form_to_excel(form, filename)
                        st.success(f"Exported to Excel: {filename}")
                    except Exception as e:
                        st.error(f"Error exporting to Excel: {e}")
            with e3:
                if st.button("📋 Copy as JSON"):
                    st.code(json.dumps(form, indent=2))
            for section_name, section_data in form.items():
                if section_name.startswith("_"):
                    continue
                with st.expander(f"📋 {section_name.replace('_', ' ').title()}"):
                    for field_name, field_value in section_data.items():
                        if field_value:
                            st.write(
                                f"**{field_name.replace('_', ' ').title()}:** {field_value}"
                            )

with upload_tab:
    st.header("Upload & Import")
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
                        file_path = f"data/{uploaded_file.name}"
                        os.makedirs("data", exist_ok=True)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        candidate_data = resume_parser.parse_resume(file_path)
                        candidate_id = db_manager.add_candidate(candidate_data)
                        candidate_data["id"] = candidate_id
                        st.session_state.current_candidate = candidate_data
                        if not hasattr(st.session_state, "messages"):
                            st.session_state.messages = []
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": f"✅ Parsed resume for **{candidate_data['name']}**!",
                            }
                        )
                        st.success("Resume parsed and candidate saved ✅")
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
                            candidate_id = db_manager.add_candidate(linkedin_data)
                            linkedin_data["id"] = candidate_id
                            st.session_state.current_candidate = linkedin_data
                            if not hasattr(st.session_state, "messages"):
                                st.session_state.messages = []
                            st.session_state.messages.append(
                                {
                                    "role": "assistant",
                                    "content": f"✅ Extracted LinkedIn data for **{linkedin_data['name']}**!",
                                }
                            )
                            st.success("LinkedIn data imported ✅")
                        else:
                            st.error("Could not extract data from LinkedIn profile")
                    except Exception as e:
                        st.error(f"Error extracting LinkedIn data: {e}")
            else:
                st.warning("Please enter a LinkedIn profile URL")

with candidates_tab:
    st.header("All Candidates")
    try:
        candidates = db_manager.get_all_candidates()
        if candidates:
            grid_cols = 3
            rows = (len(candidates) + grid_cols - 1) // grid_cols
            idx = 0
            for r in range(rows):
                cols = st.columns(grid_cols)
                for c in range(grid_cols):
                    if idx >= len(candidates):
                        break
                    cand = candidates[idx]
                    with cols[c]:
                        with st.container():
                            st.markdown(
                                '<div class="candidate-card">', unsafe_allow_html=True
                            )
                            st.write(f"**{cand['name']}**")
                            st.write(
                                f"{cand.get('current_position', 'N/A')} at {cand.get('current_company', 'N/A')}"
                            )
                            skills = cand.get("skills", [])
                            if skills:
                                st.write(
                                    f"Skills: {', '.join(skills[:3])}{'...' if len(skills) > 3 else ''}"
                                )
                            if st.button("Select", key=f"select_{cand['id']}"):
                                st.session_state.current_candidate = cand
                                (
                                    st.switch_page("app.py")
                                    if hasattr(st, "switch_page")
                                    else None
                                )
                            st.markdown("</div>", unsafe_allow_html=True)
                    idx += 1
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
