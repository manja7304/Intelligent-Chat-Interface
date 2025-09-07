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
from datetime import datetime

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
            parsed_data = self._post_process(parsed_data)
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
            "linkedin_url": "",
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
        parsed_data["linkedin_url"] = self._extract_linkedin_url(text)
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

    def _post_process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize and sanitize parsed fields (skills, experience years, name)."""
        # Name
        if isinstance(data.get("name"), str):
            data["name"] = data["name"].strip()

        # Skills cleanup
        data["skills"] = self._normalize_skills(data.get("skills", []))

        # Experience years clamp (0..60)
        try:
            years = int(data.get("experience_years", 0))
        except Exception:
            years = 0
        data["experience_years"] = max(0, min(60, years))
        return data

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
        # Defer deeper normalization to _normalize_skills
        return self._normalize_skills(skills)[:20]

    def _normalize_skills(self, skills: List[str]) -> List[str]:
        """Normalize skills list (casing, stopwords, aliases, dedup)."""
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
        preserve_upper = {"AWS", "SQL", "NLP", "API", "CI/CD", "HTML", "CSS"}
        aliases = {"js": "JavaScript", "py": "Python"}

        normalized: List[str] = []
        seen = set()
        for item in skills:
            token = (item or "").strip()
            if not token:
                continue
            low = token.lower()
            if low in aliases:
                token = aliases[low]
                low = token.lower()
            if low in stopwords:
                continue
            token_cased = token if token.upper() in preserve_upper else token.title()
            key = token_cased.lower()
            if key not in seen:
                seen.add(key)
                normalized.append(token_cased)
        return normalized

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
        """Extract work experience from text with improved patterns"""
        experience = []

        # Look for experience section with multiple possible headers
        exp_section = self._find_section(
            text,
            [
                "experience",
                "work history",
                "employment",
                "career",
                "professional experience",
                "work experience",
            ],
        )

        if exp_section:
            # Multiple patterns for different resume formats
            job_patterns = [
                # Pattern 1: Title | Company | Date
                r"([^|\n]+)\s*\|\s*([^|\n]+)\s*\|\s*([^|\n]+)",
                # Pattern 2: Title at Company (Date)
                r"([^@\n]+)\s+at\s+([^(]+)\s*\(([^)]+)\)",
                # Pattern 3: Company - Title (Date)
                r"([^-]+)\s*-\s*([^(]+)\s*\(([^)]+)\)",
                # Pattern 4: Title, Company, Date
                r"([^,\n]+),\s*([^,\n]+),\s*([^,\n]+)",
                # Pattern 5: Original pattern with dates
                r"([A-Za-z\s&,.-]+?)\s*[-–]\s*([A-Za-z\s&,.-]+?)\s*(\d{4})\s*[-–]\s*(\d{4}|present|current)",
                # Pattern 6: Simple title and company
                r"([A-Z][^|\n@,]+)\s*\n\s*([A-Z][^|\n@,]+)",
            ]

            for pattern in job_patterns:
                matches = re.finditer(
                    pattern, exp_section, re.MULTILINE | re.IGNORECASE
                )

                for match in matches:
                    groups = match.groups()
                    if len(groups) >= 2:
                        if len(groups) == 3:
                            # Pattern 1, 2, 3, 4
                            title = groups[0].strip()
                            company = groups[1].strip()
                            date_range = groups[2].strip()
                        elif len(groups) == 4:
                            # Pattern 5 (original)
                            company = groups[0].strip()
                            title = groups[1].strip()
                            start_date = groups[2].strip()
                            end_date = groups[3].strip()
                            date_range = f"{start_date} - {end_date}"
                        else:
                            # Pattern 6
                            title = groups[0].strip()
                            company = groups[1].strip()
                            date_range = ""

                        # Clean up extracted data
                        title = re.sub(r"[•\-\*]", "", title).strip()
                        company = re.sub(r"[•\-\*]", "", company).strip()
                        date_range = re.sub(r"[•\-\*]", "", date_range).strip()

                        # Skip if too short or contains unwanted text
                        if len(title) < 3 or len(company) < 3:
                            continue
                        if any(
                            word in title.lower()
                            for word in [
                                "experience",
                                "work",
                                "professional",
                                "employment",
                            ]
                        ):
                            continue

                        experience.append(
                            {
                                "title": title,
                                "company": company,
                                "date_range": date_range,
                            }
                        )

        # If no structured experience found, try to extract from general text
        if not experience:
            # Look for company names and job titles in the text
            company_patterns = [
                r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Inc|Corp|Ltd|LLC|Company|Technologies|Systems|Solutions)",
                r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Inc\.|Corp\.|Ltd\.|LLC\.)",
            ]

            for pattern in company_patterns:
                companies = re.findall(pattern, text)
                for company in companies[:3]:  # Limit to 3 companies
                    # Look for job titles near this company
                    company_context = re.search(
                        rf".{{0,200}}{re.escape(company)}.{{0,200}}",
                        text,
                        re.IGNORECASE,
                    )
                    if company_context:
                        context_text = company_context.group(0)
                        # Look for common job titles
                        job_titles = re.findall(
                            r"(?:Senior\s+)?(?:Software\s+)?(?:Engineer|Developer|Analyst|Manager|Consultant|Specialist)",
                            context_text,
                            re.IGNORECASE,
                        )
                        if job_titles:
                            experience.append(
                                {
                                    "title": job_titles[0],
                                    "company": company,
                                    "date_range": "",
                                }
                            )

        return experience

    def _extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information from text with improved patterns"""
        education = []

        # Look for education section with multiple possible headers
        edu_section = self._find_section(
            text,
            [
                "education",
                "academic",
                "qualifications",
                "academic background",
                "educational background",
            ],
        )

        if edu_section:
            # Multiple patterns for different education formats
            edu_patterns = [
                # Pattern 1: Degree from Institution (Year)
                r"([A-Za-z\s&,.-]+?)\s+from\s+([A-Za-z\s&,.-]+?)\s*\((\d{4})\)",
                # Pattern 2: Institution - Degree (Year)
                r"([A-Za-z\s&,.-]+?)\s*[-–]\s*([A-Za-z\s&,.-]+?)\s*(\d{4})",
                # Pattern 3: Degree, Institution, Year
                r"([A-Za-z\s&,.-]+?),\s*([A-Za-z\s&,.-]+?),\s*(\d{4})",
                # Pattern 4: Institution | Degree | Year
                r"([^|\n]+)\s*\|\s*([^|\n]+)\s*\|\s*([^|\n]+)",
                # Pattern 5: Simple degree and institution
                r"(Bachelor|Master|PhD|Doctorate|Associate|Certificate|Diploma)[^,\n]*,\s*([^,\n]+)",
                # Pattern 6: Institution (Year) - Degree
                r"([A-Za-z\s&,.-]+?)\s*\((\d{4})\)\s*[-–]\s*([A-Za-z\s&,.-]+)",
            ]

            for pattern in edu_patterns:
                matches = re.finditer(
                    pattern, edu_section, re.MULTILINE | re.IGNORECASE
                )

                for match in matches:
                    groups = match.groups()
                    if len(groups) >= 2:
                        if len(groups) == 3:
                            if (
                                pattern == edu_patterns[0]
                            ):  # Degree from Institution (Year)
                                degree = groups[0].strip()
                                institution = groups[1].strip()
                                year = groups[2].strip()
                            elif (
                                pattern == edu_patterns[5]
                            ):  # Institution (Year) - Degree
                                institution = groups[0].strip()
                                year = groups[1].strip()
                                degree = groups[2].strip()
                            else:  # Other 3-group patterns
                                institution = groups[0].strip()
                                degree = groups[1].strip()
                                year = groups[2].strip()
                        else:  # 2 groups
                            degree = groups[0].strip()
                            institution = groups[1].strip()
                            year = ""

                        # Clean up extracted data
                        degree = re.sub(r"[•\-\*]", "", degree).strip()
                        institution = re.sub(r"[•\-\*]", "", institution).strip()
                        year = re.sub(r"[•\-\*]", "", year).strip()

                        # Skip if too short or contains unwanted text
                        if len(degree) < 3 or len(institution) < 3:
                            continue
                        if any(
                            word in degree.lower()
                            for word in ["education", "academic", "qualifications"]
                        ):
                            continue

                        education.append(
                            {
                                "degree": degree,
                                "institution": institution,
                                "year": year,
                            }
                        )

        # If no structured education found, try to extract from general text
        if not education:
            # Look for common degree patterns
            degree_patterns = [
                r"(Bachelor|Master|PhD|Doctorate|Associate|Certificate|Diploma)[^,\n]*",
                r"(B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?|B\.?E\.?|M\.?E\.?)[^,\n]*",
            ]

            for pattern in degree_patterns:
                degrees = re.findall(pattern, text, re.IGNORECASE)
                for degree in degrees[:2]:  # Limit to 2 degrees
                    # Look for institution near this degree
                    degree_context = re.search(
                        rf".{{0,200}}{re.escape(degree)}.{{0,200}}", text, re.IGNORECASE
                    )
                    if degree_context:
                        context_text = degree_context.group(0)
                        # Look for common institution patterns
                        institutions = re.findall(
                            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:University|College|Institute|School)",
                            context_text,
                        )
                        if institutions:
                            education.append(
                                {
                                    "degree": degree,
                                    "institution": institutions[0],
                                    "year": "",
                                }
                            )

        return education

    def _extract_linkedin_url(self, text: str) -> str:
        """Extract LinkedIn profile URL with improved patterns"""
        linkedin_patterns = [
            r"linkedin\.com/in/[\w-]+",
            r"linkedin\.com/pub/[\w-]+",
            r"linkedin\.com/company/[\w-]+",
            r"https?://linkedin\.com/in/[\w-]+",
            r"https?://www\.linkedin\.com/in/[\w-]+",
            r"linkedin\.com/in/[\w-]+/?",
        ]

        for pattern in linkedin_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                url = match.group(0)
                # Ensure it starts with https://
                if not url.startswith("http"):
                    url = "https://" + url
                return url

        return ""

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
        """Calculate total years of experience from date ranges and year hints."""
        if not experience:
            return 0

        def parse_year(y: str) -> Optional[int]:
            try:
                return int(y)
            except Exception:
                return None

        month_map = {
            m.lower(): i
            for i, m in enumerate(
                [
                    "jan",
                    "feb",
                    "mar",
                    "apr",
                    "may",
                    "jun",
                    "jul",
                    "aug",
                    "sep",
                    "oct",
                    "nov",
                    "dec",
                ],
                start=1,
            )
        }

        def parse_date_fragment(s: str) -> Optional[datetime]:
            s = (s or "").strip().lower()
            if not s:
                return None
            # Try formats like Jan 2020, 2020, 2020-05
            year = None
            month = 1
            m = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", s)
            if m:
                month = month_map.get(m.group(1), 1)
            y = re.search(r"(19\d{2}|20\d{2})", s)
            if y:
                year = int(y.group(1))
            if year:
                try:
                    return datetime(year, month, 1)
                except Exception:
                    return None
            return None

        total_months = 0
        now = datetime.utcnow()
        for exp in experience:
            dr = exp.get("date_range", "")
            if dr:
                parts = re.split(r"\s*[-–]\s*", dr)
                start = parse_date_fragment(parts[0] if parts else "")
                end = parse_date_fragment(parts[1]) if len(parts) > 1 else None
                if end is None:
                    end = now
                if start and end and end > start:
                    months = (end.year - start.year) * 12 + (end.month - start.month)
                    if months > 0:
                        total_months += months

        years = total_months // 12
        return max(0, min(60, years))
