"""
Resume Parser for extracting information from PDF resumes
"""

import pdfplumber
import fitz  # PyMuPDF
import logging
import re
import spacy
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger(__name__)


class ResumeParser:
    """Parses PDF resumes and extracts structured information"""

    def __init__(self):
        self.nlp = None
        self._load_spacy_model()

    def _load_spacy_model(self):
        """Load spaCy model for NLP processing"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning(
                "spaCy model not found. Install with: python -m spacy download en_core_web_sm"
            )
            self.nlp = None

    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """
        Parse resume PDF and extract structured information

        Args:
            file_path: Path to the PDF resume file

        Returns:
            Dictionary containing extracted resume data
        """
        try:
            # Extract text using pdfplumber
            text = self._extract_text_pdfplumber(file_path)

            if not text.strip():
                # Fallback to PyMuPDF
                text = self._extract_text_pymupdf(file_path)

            if not text.strip():
                raise ValueError("Could not extract text from PDF")

            # Parse the extracted text
            parsed_data = self._parse_text(text)
            parsed_data["resume_path"] = file_path
            parsed_data["raw_text"] = text

            logger.info(f"Successfully parsed resume: {file_path}")
            return parsed_data

        except Exception as e:
            logger.error(f"Error parsing resume {file_path}: {e}")
            raise

    def _extract_text_pdfplumber(self, file_path: str) -> str:
        """Extract text using pdfplumber"""
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
            return ""

    def _extract_text_pymupdf(self, file_path: str) -> str:
        """Extract text using PyMuPDF as fallback"""
        try:
            text = ""
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            return text
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {e}")
            return ""

    def _parse_text(self, text: str) -> Dict[str, Any]:
        """Parse extracted text and extract structured information"""
        parsed_data = {
            "name": "",
            "email": "",
            "phone": "",
            "skills": [],
            "experience": [],
            "education": [],
            "current_position": "",
            "current_company": "",
            "experience_years": 0,
            "location": "",
            "summary": "",
        }

        # Extract contact information
        parsed_data["email"] = self._extract_email(text)
        parsed_data["phone"] = self._extract_phone(text)
        parsed_data["name"] = self._extract_name(text)

        # Extract skills
        parsed_data["skills"] = self._extract_skills(text)

        # Extract experience
        parsed_data["experience"] = self._extract_experience(text)
        parsed_data["experience_years"] = self._calculate_experience_years(
            parsed_data["experience"]
        )

        # Extract education
        parsed_data["education"] = self._extract_education(text)

        # Extract current position and company
        current_info = self._extract_current_position(text)
        parsed_data["current_position"] = current_info.get("position", "")
        parsed_data["current_company"] = current_info.get("company", "")

        # Extract location
        parsed_data["location"] = self._extract_location(text)

        # Extract summary/objective
        parsed_data["summary"] = self._extract_summary(text)

        return parsed_data

    def _extract_email(self, text: str) -> str:
        """Extract email address from text"""
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else ""

    def _extract_phone(self, text: str) -> str:
        """Extract phone number from text"""
        phone_patterns = [
            r"(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})",
            r"(\+?[0-9]{1,3}[-.\s]?)?\(?([0-9]{2,4})\)?[-.\s]?([0-9]{2,4})[-.\s]?([0-9]{2,4})",
        ]

        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                return "".join(phones[0]) if isinstance(phones[0], tuple) else phones[0]
        return ""

    def _extract_name(self, text: str) -> str:
        """Extract candidate name from text"""
        lines = text.split("\n")

        # Look for name in first few lines (usually at the top)
        for line in lines[:5]:
            line = line.strip()
            if line and not any(
                keyword in line.lower()
                for keyword in [
                    "email",
                    "phone",
                    "linkedin",
                    "github",
                    "portfolio",
                    "resume",
                    "cv",
                ]
            ):
                # Check if line looks like a name (2-4 words, title case)
                words = line.split()
                if 2 <= len(words) <= 4 and all(
                    word[0].isupper() for word in words if word
                ):
                    return line

        return ""

    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from text"""
        skills = []

        # Common technical skills patterns
        skill_patterns = [
            r"\b(?:Python|Java|JavaScript|C\+\+|C#|PHP|Ruby|Go|Rust|Swift|Kotlin)\b",
            r"\b(?:React|Angular|Vue|Node\.js|Django|Flask|Spring|Laravel|Express)\b",
            r"\b(?:AWS|Azure|GCP|Docker|Kubernetes|Jenkins|Git|GitHub|GitLab)\b",
            r"\b(?:SQL|MySQL|PostgreSQL|MongoDB|Redis|Elasticsearch)\b",
            r"\b(?:Machine Learning|AI|Data Science|TensorFlow|PyTorch|Pandas|NumPy)\b",
            r"\b(?:HTML|CSS|Bootstrap|SASS|LESS|Webpack|Babel)\b",
            r"\b(?:Agile|Scrum|DevOps|CI/CD|REST|API|Microservices)\b",
        ]

        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            skills.extend(matches)

        # Use spaCy for additional skill extraction if available
        if self.nlp:
            skills.extend(self._extract_skills_spacy(text))

        # Clean and deduplicate skills
        skills = list(set([skill.strip() for skill in skills if skill.strip()]))
        return skills[:20]  # Limit to top 20 skills

    def _extract_skills_spacy(self, text: str) -> List[str]:
        """Extract skills using spaCy NLP"""
        if not self.nlp:
            return []

        skills = []
        doc = self.nlp(text)

        # Extract technical terms and proper nouns
        for token in doc:
            if (
                token.pos_ in ["NOUN", "PROPN"]
                and len(token.text) > 2
                and token.text.isalpha()
                and not token.is_stop
            ):
                skills.append(token.text)

        return skills

    def _extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience from text"""
        experience = []

        # Look for experience section
        exp_section = self._find_section(
            text, ["experience", "work history", "employment", "career"]
        )

        if exp_section:
            # Simple regex to extract job entries
            job_pattern = r"([A-Za-z\s&,.-]+?)\s*[-–]\s*([A-Za-z\s&,.-]+?)\s*(\d{4})\s*[-–]\s*(\d{4}|present|current)"
            matches = re.findall(job_pattern, exp_section, re.IGNORECASE | re.MULTILINE)

            for match in matches:
                experience.append(
                    {
                        "company": match[0].strip(),
                        "position": match[1].strip(),
                        "start_date": match[2].strip(),
                        "end_date": match[3].strip(),
                    }
                )

        return experience

    def _extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information from text"""
        education = []

        # Look for education section
        edu_section = self._find_section(
            text, ["education", "academic", "qualifications"]
        )

        if edu_section:
            # Simple regex to extract education entries
            edu_pattern = r"([A-Za-z\s&,.-]+?)\s*[-–]\s*([A-Za-z\s&,.-]+?)\s*(\d{4})"
            matches = re.findall(edu_pattern, edu_section, re.IGNORECASE | re.MULTILINE)

            for match in matches:
                education.append(
                    {
                        "institution": match[0].strip(),
                        "degree": match[1].strip(),
                        "year": match[2].strip(),
                    }
                )

        return education

    def _extract_current_position(self, text: str) -> Dict[str, str]:
        """Extract current position and company"""
        current_info = {"position": "", "company": ""}

        # Look for current position indicators
        current_patterns = [
            r"current[ly]?\s*:?\s*([A-Za-z\s&,.-]+?)\s*at\s*([A-Za-z\s&,.-]+)",
            r"present[ly]?\s*:?\s*([A-Za-z\s&,.-]+?)\s*at\s*([A-Za-z\s&,.-]+)",
            r"([A-Za-z\s&,.-]+?)\s*[-–]\s*([A-Za-z\s&,.-]+?)\s*(present|current)",
        ]

        for pattern in current_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                current_info["position"] = match.group(1).strip()
                current_info["company"] = match.group(2).strip()
                break

        return current_info

    def _extract_location(self, text: str) -> str:
        """Extract location from text"""
        # Simple location extraction
        location_patterns = [
            r"([A-Za-z\s]+,\s*[A-Za-z\s]+)",
            r"([A-Za-z\s]+,\s*[A-Z]{2})",
            r"([A-Za-z\s]+,\s*[A-Za-z\s]+,\s*[A-Za-z\s]+)",
        ]

        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0].strip()

        return ""

    def _extract_summary(self, text: str) -> str:
        """Extract summary/objective section"""
        summary_section = self._find_section(
            text, ["summary", "objective", "profile", "about"]
        )

        if summary_section:
            # Take first few sentences
            sentences = summary_section.split(".")[:3]
            return ". ".join(sentences).strip()

        return ""

    def _find_section(self, text: str, section_names: List[str]) -> str:
        """Find a specific section in the resume text"""
        text_lower = text.lower()

        for section_name in section_names:
            pattern = rf"{section_name}[:\s]*\n(.*?)(?=\n[A-Z][A-Za-z\s]*:|$)"
            match = re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return ""

    def _calculate_experience_years(self, experience: List[Dict[str, str]]) -> int:
        """Calculate total years of experience"""
        if not experience:
            return 0

        total_years = 0
        current_year = 2024

        for exp in experience:
            try:
                start_year = int(exp.get("start_date", "0"))
                end_year = exp.get("end_date", "").lower()

                if end_year in ["present", "current", ""]:
                    end_year = current_year
                else:
                    end_year = int(end_year)

                years = end_year - start_year
                if years > 0:
                    total_years += years

            except (ValueError, TypeError):
                continue

        return max(0, total_years)
