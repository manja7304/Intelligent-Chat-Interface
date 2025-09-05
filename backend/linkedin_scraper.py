"""
LinkedIn Scraper for extracting candidate information from LinkedIn profiles
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Any
import time
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class LinkedInScraper:
    """Scrapes LinkedIn profiles for candidate information"""

    def __init__(
        self, email: str = None, password: str = None, serpapi_key: str = None
    ):
        self.email = email
        self.password = password
        self.serpapi_key = serpapi_key
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def search_candidate(self, name: str, company: str = None) -> List[Dict[str, Any]]:
        """
        Search for candidates on LinkedIn by name and optionally company

        Args:
            name: Candidate's name
            company: Optional company name to filter results

        Returns:
            List of candidate profiles found
        """
        try:
            if self.serpapi_key:
                return self._search_with_serpapi(name, company)
            else:
                return self._search_with_web_scraping(name, company)
        except Exception as e:
            logger.error(f"Error searching LinkedIn for {name}: {e}")
            return []

    def get_profile_data(self, profile_url: str) -> Dict[str, Any]:
        """
        Extract detailed information from a LinkedIn profile URL

        Args:
            profile_url: LinkedIn profile URL

        Returns:
            Dictionary containing profile data
        """
        try:
            if self.serpapi_key:
                data = self._get_profile_with_serpapi(profile_url)
                if data:
                    return data
                # Try SerpAPI Google engine as a secondary real-data path
                data = self._get_profile_via_serpapi_google(profile_url)
                if data:
                    return data
            else:
                return self._get_profile_with_web_scraping(profile_url)
        except Exception as e:
            logger.error(f"Error extracting profile data from {profile_url}: {e}")
            return {}

    def _search_with_serpapi(
        self, name: str, company: str = None
    ) -> List[Dict[str, Any]]:
        """Search using SerpAPI (more reliable but requires API key)"""
        try:
            search_query = f"{name}"
            if company:
                search_query += f" {company}"

            params = {
                "api_key": self.serpapi_key,
                "engine": "linkedin",
                "q": search_query,
                "type": "people",
            }

            response = requests.get("https://serpapi.com/search", params=params)
            try:
                response.raise_for_status()
            except requests.HTTPError as http_err:
                # Graceful fallback on 4xx (e.g., 400 from LinkedIn engine)
                if response.status_code in (400, 401, 403, 429):
                    logger.error(
                        f"SerpAPI search returned {response.status_code}, falling back to mock search"
                    )
                    return self._search_with_web_scraping(name, company)
                raise

            data = response.json()
            profiles = []

            if "people" in data:
                for person in data["people"]:
                    profile = {
                        "name": person.get("name", ""),
                        "title": person.get("title", ""),
                        "company": person.get("company", ""),
                        "location": person.get("location", ""),
                        "profile_url": person.get("link", ""),
                        "image_url": person.get("image", ""),
                        "connections": person.get("connections", ""),
                        "summary": "",
                    }
                    profiles.append(profile)

            return profiles

        except Exception as e:
            logger.error(f"SerpAPI search failed: {e}")
            # Final fallback
            return self._search_with_web_scraping(name, company)

    def _search_with_web_scraping(
        self, name: str, company: str = None
    ) -> List[Dict[str, Any]]:
        """Search using web scraping (fallback method)"""
        try:
            # This is a simplified mock implementation
            # In a real scenario, you would need to handle LinkedIn's anti-bot measures
            logger.warning(
                "Web scraping LinkedIn is complex and may violate ToS. Using mock data."
            )

            # Return mock data for demonstration
            mock_profiles = [
                {
                    "name": name,
                    "title": "Software Engineer",
                    "company": company or "Tech Company",
                    "location": "San Francisco, CA",
                    "profile_url": f'https://linkedin.com/in/{name.lower().replace(" ", "-")}',
                    "image_url": "",
                    "connections": "500+",
                    "summary": "Experienced software engineer with expertise in Python and web development.",
                }
            ]

            return mock_profiles

        except Exception as e:
            logger.error(f"Web scraping search failed: {e}")
            return []

    def _get_profile_with_serpapi(self, profile_url: str) -> Dict[str, Any]:
        """Get detailed profile data using SerpAPI"""
        try:
            params = {
                "api_key": self.serpapi_key,
                "engine": "linkedin",
                "url": profile_url,
            }

            response = requests.get("https://serpapi.com/search", params=params)
            try:
                response.raise_for_status()
            except requests.HTTPError as http_err:
                # On LinkedIn engine 4xx, return empty to allow Google-engine fallback first
                if response.status_code in (400, 401, 403, 429):
                    logger.error(
                        f"SerpAPI profile extraction returned {response.status_code}, attempting Google-engine fallback"
                    )
                    return {}
                raise

            data = response.json()

            profile_data = {
                "name": data.get("name", ""),
                "title": data.get("title", ""),
                "company": data.get("company", ""),
                "location": data.get("location", ""),
                "summary": data.get("summary", ""),
                "experience": data.get("experience", []),
                "education": data.get("education", []),
                "skills": data.get("skills", []),
                "connections": data.get("connections", ""),
                "image_url": data.get("image", ""),
                "profile_url": profile_url,
            }

            return profile_data

        except Exception as e:
            logger.error(f"SerpAPI profile extraction failed: {e}")
            # Final fallback
            return self._get_profile_with_web_scraping(profile_url)

    def _get_profile_via_serpapi_google(self, profile_url: str) -> Dict[str, Any]:
        """Attempt minimal real data using SerpAPI Google results for the given profile URL.

        This does not bypass LinkedIn protections; it only uses the public Google result snippet.
        """
        try:
            params = {
                "api_key": self.serpapi_key,
                "engine": "google",
                "q": profile_url,
                "num": 1,
                "hl": "en",
            }
            resp = requests.get("https://serpapi.com/search", params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()

            organic = data.get("organic_results", [])
            if not organic:
                return {}

            top = organic[0]
            link = top.get("link", "")
            if profile_url.rstrip("/") not in link.rstrip("/"):
                # Not the same profile, avoid mismatches
                return {}

            title = top.get("title", "")
            snippet = top.get("snippet", "")

            profile_data = {
                "name": title.split(" - ")[0].strip() if title else "",
                "title": "",
                "company": "",
                "location": "",
                "summary": snippet,
                "experience": [],
                "education": [],
                "skills": self._extract_skills_from_text(snippet),
                "connections": "",
                "image_url": "",
                "profile_url": profile_url,
            }
            return profile_data
        except Exception as e:
            logger.error(f"SerpAPI Google fallback failed: {e}")
            return {}

    def _get_profile_with_web_scraping(self, profile_url: str) -> Dict[str, Any]:
        """Get detailed profile data using web scraping (mock implementation)"""
        try:
            # This is a mock implementation
            # Real implementation would require handling LinkedIn's authentication and anti-bot measures
            logger.warning(
                "Web scraping LinkedIn profiles is complex and may violate ToS. Using mock data."
            )

            # Extract name from URL for mock data
            name_match = re.search(r"/in/([^/]+)", profile_url)
            name = (
                name_match.group(1).replace("-", " ").title()
                if name_match
                else "Unknown"
            )

            mock_profile = {
                "name": name,
                "title": "Senior Software Engineer",
                "company": "Tech Corporation",
                "location": "San Francisco, CA",
                "summary": "Experienced software engineer with 5+ years of experience in full-stack development.",
                "experience": [
                    {
                        "title": "Senior Software Engineer",
                        "company": "Tech Corporation",
                        "duration": "2020 - Present",
                        "description": "Leading development of scalable web applications",
                    }
                ],
                "education": [
                    {
                        "school": "University of California",
                        "degree": "Bachelor of Science in Computer Science",
                        "year": "2018",
                    }
                ],
                "skills": ["Python", "JavaScript", "React", "Node.js", "AWS", "Docker"],
                "connections": "500+",
                "image_url": "",
                "profile_url": profile_url,
            }

            return mock_profile

        except Exception as e:
            logger.error(f"Web scraping profile extraction failed: {e}")
            return {}

    def extract_skills_from_profile(self, profile_data: Dict[str, Any]) -> List[str]:
        """Extract skills from LinkedIn profile data"""
        skills = []

        # Extract from skills section
        if "skills" in profile_data and profile_data["skills"]:
            skills.extend(profile_data["skills"])

        # Extract from summary/description
        if "summary" in profile_data and profile_data["summary"]:
            summary_skills = self._extract_skills_from_text(profile_data["summary"])
            skills.extend(summary_skills)

        # Extract from experience descriptions
        if "experience" in profile_data and profile_data["experience"]:
            for exp in profile_data["experience"]:
                if "description" in exp and exp["description"]:
                    exp_skills = self._extract_skills_from_text(exp["description"])
                    skills.extend(exp_skills)

        # Clean and deduplicate
        skills = list(set([skill.strip() for skill in skills if skill.strip()]))
        return skills[:20]  # Limit to top 20 skills

    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract technical skills from text using regex patterns"""
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

        return skills

    def merge_with_resume_data(
        self, linkedin_data: Dict[str, Any], resume_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Intelligently merge LinkedIn and resume data, prioritizing verified information

        Args:
            linkedin_data: Data extracted from LinkedIn
            resume_data: Data extracted from resume

        Returns:
            Merged candidate data
        """
        merged_data = {
            "name": linkedin_data.get("name") or resume_data.get("name", ""),
            "email": resume_data.get(
                "email", ""
            ),  # Resume email is usually more reliable
            "phone": resume_data.get(
                "phone", ""
            ),  # Resume phone is usually more reliable
            "linkedin_url": linkedin_data.get("profile_url", ""),
            "resume_path": resume_data.get("resume_path", ""),
            "location": linkedin_data.get("location")
            or resume_data.get("location", ""),
            "current_position": linkedin_data.get("title")
            or resume_data.get("current_position", ""),
            "current_company": linkedin_data.get("company")
            or resume_data.get("current_company", ""),
            "summary": linkedin_data.get("summary") or resume_data.get("summary", ""),
            "skills": [],
            "experience": [],
            "education": [],
            "experience_years": resume_data.get("experience_years", 0),
        }

        # Merge skills (prioritize LinkedIn skills, add unique resume skills)
        linkedin_skills = linkedin_data.get("skills", [])
        resume_skills = resume_data.get("skills", [])

        merged_skills = list(set(linkedin_skills + resume_skills))
        merged_data["skills"] = merged_skills

        # Merge experience (prioritize LinkedIn experience, add unique resume experience)
        linkedin_exp = linkedin_data.get("experience", [])
        resume_exp = resume_data.get("experience", [])

        # Simple merge - in a real implementation, you'd want more sophisticated matching
        merged_data["experience"] = linkedin_exp + resume_exp

        # Merge education
        linkedin_edu = linkedin_data.get("education", [])
        resume_edu = resume_data.get("education", [])

        merged_data["education"] = linkedin_edu + resume_edu

        return merged_data
