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
import re
from functools import lru_cache

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


@st.cache_data(show_spinner=False)
def cached_parse_resume(file_path: str) -> Dict[str, Any]:
    parser = ResumeParser()
    return parser.parse_resume(file_path)


@st.cache_data(show_spinner=False)
def cached_linkedin_profile(url: str) -> Dict[str, Any]:
    scraper = LinkedInScraper(
        email=os.getenv("LINKEDIN_EMAIL", ""),
        password=os.getenv("LINKEDIN_PASSWORD", ""),
        serpapi_key=os.getenv("SERPAPI_KEY", ""),
    )
    return scraper.get_profile_data(url)


try:
    from email_validator import validate_email as _ev_validate, EmailNotValidError
except Exception:
    _ev_validate = None
    EmailNotValidError = Exception

try:
    import phonenumbers as _phonenumbers
except Exception:
    _phonenumbers = None


def _validate_email(email: Any) -> str:
    """Return a valid email or empty string if invalid."""
    if not isinstance(email, str):
        return ""
    email = email.strip()
    if _ev_validate:
        try:
            return _ev_validate(email, check_deliverability=False).email
        except EmailNotValidError:
            return ""
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return email if re.match(pattern, email) else ""


def _normalize_phone(phone: Any) -> str:
    """Normalize phone using phonenumbers when available; fallback to digits check."""
    if not isinstance(phone, str):
        phone = str(phone) if phone is not None else ""
    phone = phone.strip()
    if _phonenumbers:
        try:
            # Try parsing without region; then fallback to IN/US common regions as examples
            for region in [None, "IN", "US", "GB"]:
                try:
                    num = (
                        _phonenumbers.parse(phone, region)
                        if region
                        else _phonenumbers.parse(phone)
                    )
                    if _phonenumbers.is_possible_number(
                        num
                    ) and _phonenumbers.is_valid_number(num):
                        return _phonenumbers.format_number(
                            num, _phonenumbers.PhoneNumberFormat.E164
                        )
                except Exception:
                    continue
        except Exception:
            pass
    digits = re.sub(r"[^0-9+]", "", phone)
    if digits.count("+") > 1:
        digits = digits.replace("+", "")
    just_digits = re.sub(r"[^0-9]", "", digits)
    return digits if len(just_digits) >= 7 else ""


def _normalize_skills(skills: Any) -> List[str]:
    """Ensure skills is a clean list of distinct, title-cased tokens, removing obvious non-skills."""
    normalized: List[str] = []
    if isinstance(skills, str):
        # split on commas or semicolons
        parts = re.split(r"[;,]", skills)
    elif isinstance(skills, list):
        parts = skills
    else:
        parts = []

    seen = set()
    stopwords = {
        "and",
        "or",
        "the",
        "a",
        "an",
        "service",
        "university",
        "hands",
        "years",
        "experience",
        "skill",
        "skills",
    }
    for part in parts:
        if not isinstance(part, str):
            part = str(part)
        token = part.strip()
        if not token:
            continue
        # drop obviously non-skill numeric tokens
        if re.fullmatch(r"[0-9.]+", token):
            continue
        if token.strip().lower() in stopwords:
            continue
        # keep common tech casing (e.g., AWS, SQL, NLP)
        preserve_upper = {"AWS", "SQL", "NLP", "API", "CI/CD", "HTML", "CSS"}
        token_cased = token if token.upper() in preserve_upper else token.title()
        if token_cased.lower() not in seen:
            seen.add(token_cased.lower())
            normalized.append(token_cased)
    return normalized


def _clamp_experience_years(value: Any, min_years: int = 0, max_years: int = 60) -> int:
    """Convert to int and clamp to a realistic range."""
    try:
        if isinstance(value, str):
            # extract first integer in the string
            m = re.search(r"-?\d+", value)
            value = int(m.group(0)) if m else 0
        else:
            value = int(value)
    except Exception:
        value = 0
    return max(min_years, min(max_years, value))


def normalize_candidate_data(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize candidate fields in-place and return the dict."""
    if not isinstance(candidate, dict):
        return {}
    candidate["email"] = _validate_email(candidate.get("email"))
    candidate["phone"] = _normalize_phone(candidate.get("phone"))
    candidate["skills"] = _normalize_skills(candidate.get("skills", []))
    candidate["experience_years"] = _clamp_experience_years(
        candidate.get("experience_years", 0)
    )
    # Basic name cleanup
    if isinstance(candidate.get("name"), str):
        candidate["name"] = candidate["name"].strip()
    return candidate


def score_candidate_fit(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Score candidate against predefined ML/NLP/LLM criteria and return breakdown.

    Returns a dict with keys: total, bucket_scores, details, recommendation.
    """
    if not isinstance(candidate, dict):
        return {
            "total": 0,
            "bucket_scores": {},
            "details": [],
            "recommendation": "Not a fit",
        }

    # Weights per rubric
    weights = {
        "core": 40,
        "nlp_llm": 25,
        "problem_comm": 15,
        "systems": 15,
        "bonus": 5,
    }

    # Helper getters
    skills = set([s.lower() for s in candidate.get("skills", []) if isinstance(s, str)])
    text_blobs = []
    for k in ["summary", "work_experience", "experience", "projects", "education"]:
        v = candidate.get(k)
        if isinstance(v, str):
            text_blobs.append(v.lower())
        elif isinstance(v, list):
            text_blobs.extend([str(x).lower() for x in v])
    text_all = "\n".join(text_blobs)

    # Core skills (40)
    core_pts = 0
    core_max = weights["core"]
    # Python
    if "python" in skills or "python" in text_all:
        core_pts += 10
    # Frameworks
    frameworks_hit = 0
    for fw in ["tensorflow", "pytorch", "scikit-learn", "sklearn"]:
        if fw in skills or fw in text_all:
            frameworks_hit += 1
    core_pts += min(frameworks_hit, 2) * 5  # up to 10
    # Data prep/model eval
    for kw in [
        "feature engineering",
        "preprocessing",
        "data preprocessing",
        "cross-validation",
        "model evaluation",
        "metrics",
    ]:
        if kw in text_all:
            core_pts += 5
            break
    # Software development practices
    for kw in ["unit test", "pytest", "ci", "cd", "packag", "docker"]:
        if kw in text_all:
            core_pts += 5
            break
    core_pts = min(core_pts, core_max)

    # NLP/LLM (25)
    nlp_pts = 0
    nlp_max = weights["nlp_llm"]
    # NLP libs
    nlp_lib_hit = 0
    for lib in ["spacy", "nltk", "hugging face", "transformers"]:
        if lib in skills or lib in text_all:
            nlp_lib_hit += 1
    nlp_pts += min(nlp_lib_hit, 2) * 4  # up to 8
    # LLM experience
    for kw in [
        "gpt",
        "bert",
        "t5",
        "llm",
        "prompt engineering",
        "fine-tuning",
        "finetuning",
        "deployment",
    ]:
        if kw in text_all:
            nlp_pts += 12
            break
    # Text pipelines mention
    for kw in ["tokenization", "ner", "classification", "text processing"]:
        if kw in text_all:
            nlp_pts += 5
            break
    nlp_pts = min(nlp_pts, nlp_max)

    # Problem solving & communication (15)
    pc_pts = 0
    pc_max = weights["problem_comm"]
    for kw in [
        "analytical",
        "problem-solving",
        "problem solving",
        "root cause",
        "design doc",
        "presentation",
        "communication",
    ]:
        if kw in text_all:
            pc_pts += 8
            break
    for kw in ["communication", "written", "verbal", "stakeholder"]:
        if kw in text_all:
            pc_pts += 7
            break
    pc_pts = min(pc_pts, pc_max)

    # Systems & tooling (15)
    sys_pts = 0
    sys_max = weights["systems"]
    for kw in ["aws", "azure", "gcp"]:
        if kw in skills or kw in text_all:
            sys_pts += 6
            break
    for kw in ["git", "github", "gitlab", "version control"]:
        if kw in skills or kw in text_all:
            sys_pts += 4
            break
    for kw in ["cybersecurity", "security", "owasp"]:
        if kw in text_all:
            sys_pts += 5
            break
    sys_pts = min(sys_pts, sys_max)

    # Bonus (5)
    bonus_pts = 0
    for kw in [
        "transformer",
        "attention mechanism",
        "attention mechanisms",
        "research",
        "coursework",
    ]:
        if kw in text_all:
            bonus_pts = 5
            break

    total = core_pts + nlp_pts + pc_pts + sys_pts + bonus_pts
    if total >= 85:
        rec = "Strong fit"
    elif total >= 70:
        rec = "Fit"
    elif total >= 55:
        rec = "Borderline"
    else:
        rec = "Not a fit"

    return {
        "total": int(total),
        "bucket_scores": {
            "core": int(core_pts),
            "nlp_llm": int(nlp_pts),
            "problem_comm": int(pc_pts),
            "systems": int(sys_pts),
            "bonus": int(bonus_pts),
        },
        "details": [
            "Scored based on keywords in skills/experience/summary.",
            "Tuned for Python/ML/NLP/LLM roles.",
        ],
        "recommendation": rec,
    }


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
        # Choose provider based on configuration
        provider = getattr(config, "AI_PROVIDER", "openai")
        model = getattr(config, "DEFAULT_MODEL", "gpt-3.5-turbo")
        ollama_host = getattr(config, "OLLAMA_HOST", "http://127.0.0.1:11434")
        # OpenRouter settings
        openrouter_api_key = getattr(config, "OPENROUTER_API_KEY", "")
        openrouter_model = getattr(config, "OPENROUTER_MODEL", "openrouter/auto")
        openrouter_api_url = getattr(
            config,
            "OPENROUTER_API_URL",
            "https://openrouter.ai/api/v1/chat/completions",
        )
        openrouter_site_url = getattr(
            config, "OPENROUTER_SITE_URL", "http://localhost:8501"
        )
        openrouter_app_title = getattr(
            config, "OPENROUTER_APP_TITLE", "Intelligent Chat Interface"
        )
        ai_form_filler = AIFormFiller(
            api_key=config.OPENAI_API_KEY,
            model=model,
            provider=provider,
            ollama_host=ollama_host,
            openrouter_api_key=openrouter_api_key,
            openrouter_model=openrouter_model,
            openrouter_api_url=openrouter_api_url,
            openrouter_site_url=openrouter_site_url,
            openrouter_app_title=openrouter_app_title,
        )

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

    # Provider configuration display
    st.subheader("Configuration")
    st.write(f"**AI Provider:** {getattr(config, 'AI_PROVIDER', 'openai').title()}")
    _provider_name = getattr(config, "AI_PROVIDER", "openai")
    if _provider_name == "openai":
        if config.OPENAI_API_KEY:
            st.caption("OpenAI API key loaded from environment.")
        else:
            st.warning(
                "OpenAI API key not found. Set OPENAI_API_KEY in your .env file."
            )
    elif _provider_name == "ollama":
        st.caption(
            f"Using Ollama at {getattr(config, 'OLLAMA_HOST', 'http://127.0.0.1:11434')} with model {getattr(config, 'OLLAMA_MODEL', 'llama3.1:8b-instruct')}"
        )
    elif _provider_name == "openrouter":
        if getattr(config, "OPENROUTER_API_KEY", ""):
            st.caption("OpenRouter API key loaded from environment.")
            st.caption(
                f"OpenRouter model: {getattr(config, 'OPENROUTER_MODEL', 'openrouter/auto')}"
            )
        else:
            st.warning(
                "OpenRouter API key not found. Set OPENROUTER_API_KEY in your .env file."
            )

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
        # First try command-based actions; if not matched, fall back to LLM chat
        response = process_user_input(
            prompt, db_manager, resume_parser, linkedin_scraper, ai_form_filler
        )
        if response and response.strip():
            st.markdown(response)
        else:
            try:
                system_prompt = (
                    "You are an HR assistant. Answer concisely and professionally."
                )
                llm_reply = ai_form_filler.chat(prompt, system_prompt)
                st.markdown(llm_reply or "(No response)")
            except Exception as e:
                st.markdown(f"Error: {e}")

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
                    candidate_data = cached_parse_resume(file_path)
                    candidate_data = normalize_candidate_data(candidate_data)

                    # Add to database
                    candidate_id = db_manager.add_candidate(candidate_data)
                    candidate_data["id"] = candidate_id

                    st.session_state.current_candidate = candidate_data
                    if not hasattr(st.session_state, "messages"):
                        st.session_state.messages = []
                    top_skills = (
                        ", ".join(candidate_data.get("skills", [])[:5]) or "N/A"
                    )
                    email_str = candidate_data.get("email") or "N/A"
                    phone_str = candidate_data.get("phone") or "N/A"
                    years = candidate_data.get("experience_years", 0)
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": (
                                f"✅ Resume parsed for **{candidate_data['name']}**.\n\n"
                                f"- Email: {email_str}\n"
                                f"- Phone: {phone_str}\n"
                                f"- Top skills: {top_skills}\n"
                                f"- Experience: {years} year{'s' if years != 1 else ''}"
                            ),
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
                    linkedin_data = cached_linkedin_profile(linkedin_url)
                    linkedin_data = normalize_candidate_data(linkedin_data)
                    # If we already have a current candidate (likely from resume), merge
                    if (
                        hasattr(st.session_state, "current_candidate")
                        and st.session_state.current_candidate
                    ):
                        merged = linkedin_scraper.merge_with_resume_data(
                            linkedin_data, st.session_state.current_candidate
                        )
                        linkedin_data = normalize_candidate_data(merged)

                    if linkedin_data:
                        # Add to database
                        candidate_id = db_manager.add_candidate(linkedin_data)
                        linkedin_data["id"] = candidate_id

                        st.session_state.current_candidate = linkedin_data
                        if not hasattr(st.session_state, "messages"):
                            st.session_state.messages = []
                        top_skills = (
                            ", ".join(linkedin_data.get("skills", [])[:5]) or "N/A"
                        )
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": (
                                    f"✅ LinkedIn data added for **{linkedin_data['name']}**.\n\n"
                                    f"- Title: {linkedin_data.get('title', 'N/A')}\n"
                                    f"- Company: {linkedin_data.get('company', 'N/A')}\n"
                                    f"- Location: {linkedin_data.get('location', 'N/A')}\n"
                                    f"- Top skills: {top_skills}"
                                ),
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

        # Delete current candidate button
        if st.button("🗑️ Delete This Candidate", type="secondary"):
            try:
                ok = db_manager.delete_candidate(candidate.get("id"))
                if ok:
                    st.success("Candidate deleted")
                    st.session_state.current_candidate = None
                    st.rerun()
                else:
                    st.error("Failed to delete candidate")
            except Exception as e:
                st.error(f"Error deleting candidate: {e}")

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
            provider_name = getattr(config, "AI_PROVIDER", "openai")
            has_ai = (
                (provider_name == "openai" and bool(config.OPENAI_API_KEY))
                or provider_name == "ollama"
                or (
                    provider_name == "openrouter"
                    and bool(getattr(config, "OPENROUTER_API_KEY", ""))
                )
            )
            if ai_form_filler and has_ai:
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
                st.error(
                    "AI provider not configured. Set OPENAI_API_KEY, or configure Ollama/OpenRouter."
                )

    with col2:
        if st.button("🎯 Generate Interview Form", use_container_width=True):
            provider_name = getattr(config, "AI_PROVIDER", "openai")
            has_ai = (
                (provider_name == "openai" and bool(config.OPENAI_API_KEY))
                or provider_name == "ollama"
                or (
                    provider_name == "openrouter"
                    and bool(getattr(config, "OPENROUTER_API_KEY", ""))
                )
            )
            if ai_form_filler and has_ai:
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
                st.error(
                    "AI provider not configured. Set OPENAI_API_KEY, or configure Ollama/OpenRouter."
                )

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
                # Some AI responses may return strings for sections; handle gracefully
                if not isinstance(section_data, dict):
                    st.write(section_data)
                else:
                    for field_name, field_value in section_data.items():
                        if field_value:
                            st.write(
                                f"**{field_name.replace('_', ' ').title()}:** {field_value}"
                            )

    # Candidate Fit Assessment
    st.markdown("---")
    st.header("✅ Candidate Fit Assessment")

    assess_col1, assess_col2 = st.columns([1, 1])
    with assess_col1:
        if st.button("🧮 Assess Fit", use_container_width=True):
            try:
                result = score_candidate_fit(candidate)
                st.session_state.candidate_fit = result
                st.success("Assessment generated.")
            except Exception as e:
                st.error(f"Error scoring candidate: {e}")

    with assess_col2:
        if st.button("💾 Export Assessment JSON", use_container_width=True):
            try:
                result = st.session_state.get("candidate_fit")
                if result:
                    os.makedirs("exports", exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"exports/fit_assessment_{candidate['name'].replace(' ', '_')}_{timestamp}.json"
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(result, f, indent=2)
                    st.success(f"Saved assessment to {filename}")
                else:
                    st.info("Run assessment first.")
            except Exception as e:
                st.error(f"Error exporting assessment: {e}")

    if st.session_state.get("candidate_fit"):
        fit = st.session_state["candidate_fit"]
        st.subheader(f"Overall Score: {fit['total']} / 100 — {fit['recommendation']}")
        bs = fit.get("bucket_scores", {})
        st.write(
            f"Core: {bs.get('core', 0)} | NLP/LLM: {bs.get('nlp_llm', 0)} | Problem/Comm: {bs.get('problem_comm', 0)} | Systems: {bs.get('systems', 0)} | Bonus: {bs.get('bonus', 0)}"
        )
        with st.expander("Details"):
            for line in fit.get("details", []):
                st.write(f"- {line}")

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

                        if st.button(
                            f"Delete", key=f"delete_{candidate['id']}", type="secondary"
                        ):
                            try:
                                ok = db_manager.delete_candidate(candidate["id"])
                                if ok:
                                    st.success("Deleted")
                                    st.rerun()
                                else:
                                    st.error("Delete failed")
                            except Exception as e:
                                st.error(f"Error deleting candidate: {e}")

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
        Built with ❤️ using Streamlit and {('OpenAI' if getattr(config, 'AI_PROVIDER', 'openai') == 'openai' else ('Ollama' if getattr(config, 'AI_PROVIDER', 'openai') == 'ollama' else 'OpenRouter'))}
    </div>
    """,
    unsafe_allow_html=True,
)
