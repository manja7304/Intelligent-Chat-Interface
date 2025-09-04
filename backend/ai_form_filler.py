"""
AI-powered form filler for generating HR forms based on candidate data
"""

import openai
import json
import logging
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class AIFormFiller:
    """Uses AI to intelligently fill HR forms based on candidate data"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        self.model = "gpt-3.5-turbo"
        self.max_tokens = 2000
        self.temperature = 0.7

        if api_key and api_key != "your_openai_api_key_here":
            try:
                self.client = openai.OpenAI(api_key=api_key)
            except Exception as e:
                # Fallback for older openai versions
                openai.api_key = api_key
                self.client = None

    def generate_hr_form(
        self, candidate_data: Dict[str, Any], form_template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate filled HR form based on candidate data and form template

        Args:
            candidate_data: Structured candidate information
            form_template: HR form template with fields and instructions

        Returns:
            Filled HR form data
        """
        try:
            # Check if API key is available
            if not self.api_key or self.api_key == "your_openai_api_key_here":
                logger.warning("OpenAI API key not provided, using fallback form")
                return self._create_fallback_form(form_template, candidate_data)

            # Prepare the prompt for AI
            prompt = self._create_form_filling_prompt(candidate_data, form_template)

            # Call OpenAI API
            if self.client:
                # New OpenAI client format
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert HR assistant that fills out forms based on candidate data. Be accurate and professional.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
                ai_response = response.choices[0].message.content
            else:
                # Fallback for older openai versions
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert HR assistant that fills out forms based on candidate data. Be accurate and professional.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
                ai_response = response.choices[0].message.content

            # Parse the AI response
            filled_form = self._parse_ai_response(ai_response, form_template)

            # Add metadata
            filled_form["_metadata"] = {
                "generated_at": datetime.now().isoformat(),
                "candidate_id": candidate_data.get("id"),
                "form_type": form_template.get("form_type", "standard"),
                "ai_model": self.model,
            }

            logger.info(
                f"Generated HR form for candidate: {candidate_data.get('name', 'Unknown')}"
            )
            return filled_form

        except Exception as e:
            logger.error(f"Error generating HR form: {e}")
            raise

    def _create_form_filling_prompt(
        self, candidate_data: Dict[str, Any], form_template: Dict[str, Any]
    ) -> str:
        """Create a comprehensive prompt for AI form filling"""

        prompt = f"""
        Please fill out the following HR form based on the provided candidate data.
        
        CANDIDATE DATA:
        {json.dumps(candidate_data, indent=2)}
        
        FORM TEMPLATE:
        {json.dumps(form_template, indent=2)}
        
        INSTRUCTIONS:
        1. Fill in all applicable fields based on the candidate data
        2. If information is not available, leave the field empty or mark as "Not Available"
        3. Use professional language and formatting
        4. Ensure all dates are in YYYY-MM-DD format
        5. For skills, list them in order of relevance/importance
        6. For experience, include key achievements and responsibilities
        7. Maintain consistency with the original candidate data
        
        Please return the filled form as a JSON object with the same structure as the template.
        """

        return prompt

    def _parse_ai_response(
        self, ai_response: str, form_template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse AI response and structure it according to the form template"""
        try:
            # Try to extract JSON from the response
            json_start = ai_response.find("{")
            json_end = ai_response.rfind("}") + 1

            if json_start != -1 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                filled_form = json.loads(json_str)
            else:
                # Fallback: create form based on template structure
                filled_form = self._create_fallback_form(form_template, candidate_data)

            return filled_form

        except json.JSONDecodeError:
            logger.warning("Failed to parse AI response as JSON, using fallback")
            return self._create_fallback_form(form_template, candidate_data)

    def _create_fallback_form(
        self, form_template: Dict[str, Any], candidate_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a fallback form when AI response parsing fails"""
        filled_form = {}

        for section, fields in form_template.get("sections", {}).items():
            filled_form[section] = {}
            for field, config in fields.items():
                # Try to map candidate data to form fields
                if candidate_data:
                    field_value = self._map_candidate_data_to_field(
                        field, candidate_data
                    )
                    if field_value:
                        filled_form[section][field] = field_value
                    else:
                        filled_form[section][field] = config.get("default_value", "")
                else:
                    filled_form[section][field] = config.get("default_value", "")

        return filled_form

    def _map_candidate_data_to_field(
        self, field_name: str, candidate_data: Dict[str, Any]
    ) -> str:
        """Map candidate data to form field names"""
        field_mapping = {
            "full_name": candidate_data.get("name", ""),
            "email": candidate_data.get("email", ""),
            "phone": candidate_data.get("phone", ""),
            "location": candidate_data.get("location", ""),
            "linkedin_url": candidate_data.get("linkedin_url", ""),
            "current_position": candidate_data.get("current_position", ""),
            "current_company": candidate_data.get("current_company", ""),
            "experience_years": candidate_data.get("experience_years", ""),
            "technical_skills": ", ".join(candidate_data.get("skills", [])),
            "work_experience": ", ".join(
                [
                    exp.get("title", "") + " at " + exp.get("company", "")
                    for exp in candidate_data.get("experience", [])
                ]
            ),
            "education": ", ".join(
                [
                    edu.get("degree", "") + " from " + edu.get("institution", "")
                    for edu in candidate_data.get("education", [])
                ]
            ),
        }

        return field_mapping.get(field_name, "")

    def generate_standard_hr_form(
        self, candidate_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a standard HR form for the candidate"""

        standard_template = {
            "form_type": "standard_hr_form",
            "sections": {
                "personal_information": {
                    "full_name": {
                        "label": "Full Name",
                        "type": "text",
                        "required": True,
                    },
                    "email": {
                        "label": "Email Address",
                        "type": "email",
                        "required": True,
                    },
                    "phone": {"label": "Phone Number", "type": "tel", "required": True},
                    "location": {
                        "label": "Location",
                        "type": "text",
                        "required": False,
                    },
                    "linkedin_url": {
                        "label": "LinkedIn Profile",
                        "type": "url",
                        "required": False,
                    },
                },
                "professional_summary": {
                    "summary": {
                        "label": "Professional Summary",
                        "type": "textarea",
                        "required": True,
                    },
                    "current_position": {
                        "label": "Current Position",
                        "type": "text",
                        "required": True,
                    },
                    "current_company": {
                        "label": "Current Company",
                        "type": "text",
                        "required": True,
                    },
                    "experience_years": {
                        "label": "Years of Experience",
                        "type": "number",
                        "required": True,
                    },
                },
                "skills_assessment": {
                    "technical_skills": {
                        "label": "Technical Skills",
                        "type": "textarea",
                        "required": True,
                    },
                    "soft_skills": {
                        "label": "Soft Skills",
                        "type": "textarea",
                        "required": False,
                    },
                    "certifications": {
                        "label": "Certifications",
                        "type": "textarea",
                        "required": False,
                    },
                },
                "experience_details": {
                    "work_experience": {
                        "label": "Work Experience",
                        "type": "textarea",
                        "required": True,
                    },
                    "key_achievements": {
                        "label": "Key Achievements",
                        "type": "textarea",
                        "required": False,
                    },
                },
                "education_background": {
                    "education": {
                        "label": "Education",
                        "type": "textarea",
                        "required": True,
                    },
                    "additional_training": {
                        "label": "Additional Training/Courses",
                        "type": "textarea",
                        "required": False,
                    },
                },
                "hr_assessment": {
                    "availability": {
                        "label": "Availability",
                        "type": "text",
                        "required": False,
                    },
                    "salary_expectations": {
                        "label": "Salary Expectations",
                        "type": "text",
                        "required": False,
                    },
                    "notice_period": {
                        "label": "Notice Period",
                        "type": "text",
                        "required": False,
                    },
                    "additional_notes": {
                        "label": "Additional Notes",
                        "type": "textarea",
                        "required": False,
                    },
                },
            },
        }

        return self.generate_hr_form(candidate_data, standard_template)

    def generate_interview_form(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an interview assessment form"""

        interview_template = {
            "form_type": "interview_assessment",
            "sections": {
                "candidate_overview": {
                    "candidate_name": {
                        "label": "Candidate Name",
                        "type": "text",
                        "required": True,
                    },
                    "position_applied": {
                        "label": "Position Applied For",
                        "type": "text",
                        "required": True,
                    },
                    "interview_date": {
                        "label": "Interview Date",
                        "type": "date",
                        "required": True,
                    },
                    "interviewer_name": {
                        "label": "Interviewer Name",
                        "type": "text",
                        "required": True,
                    },
                },
                "technical_assessment": {
                    "technical_skills_rating": {
                        "label": "Technical Skills Rating (1-5)",
                        "type": "number",
                        "required": True,
                    },
                    "problem_solving_ability": {
                        "label": "Problem Solving Ability (1-5)",
                        "type": "number",
                        "required": True,
                    },
                    "technical_notes": {
                        "label": "Technical Assessment Notes",
                        "type": "textarea",
                        "required": False,
                    },
                },
                "communication_assessment": {
                    "communication_skills": {
                        "label": "Communication Skills (1-5)",
                        "type": "number",
                        "required": True,
                    },
                    "presentation_ability": {
                        "label": "Presentation Ability (1-5)",
                        "type": "number",
                        "required": True,
                    },
                    "communication_notes": {
                        "label": "Communication Assessment Notes",
                        "type": "textarea",
                        "required": False,
                    },
                },
                "cultural_fit": {
                    "team_work": {
                        "label": "Team Work (1-5)",
                        "type": "number",
                        "required": True,
                    },
                    "adaptability": {
                        "label": "Adaptability (1-5)",
                        "type": "number",
                        "required": True,
                    },
                    "cultural_fit_notes": {
                        "label": "Cultural Fit Notes",
                        "type": "textarea",
                        "required": False,
                    },
                },
                "overall_assessment": {
                    "overall_rating": {
                        "label": "Overall Rating (1-5)",
                        "type": "number",
                        "required": True,
                    },
                    "recommendation": {
                        "label": "Recommendation",
                        "type": "select",
                        "options": ["Strong Hire", "Hire", "No Hire", "Strong No Hire"],
                        "required": True,
                    },
                    "strengths": {
                        "label": "Key Strengths",
                        "type": "textarea",
                        "required": True,
                    },
                    "areas_for_improvement": {
                        "label": "Areas for Improvement",
                        "type": "textarea",
                        "required": False,
                    },
                    "final_notes": {
                        "label": "Final Notes",
                        "type": "textarea",
                        "required": False,
                    },
                },
            },
        }

        return self.generate_hr_form(candidate_data, interview_template)

    def export_form_to_pdf(self, filled_form: Dict[str, Any], output_path: str) -> str:
        """Export filled form to PDF using reportlab"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch

            doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            # Title
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=16,
                spaceAfter=30,
                alignment=1,  # Center alignment
            )

            form_type = filled_form.get("_metadata", {}).get("form_type", "HR Form")
            title = Paragraph(f"{form_type.upper()}", title_style)
            story.append(title)
            story.append(Spacer(1, 20))

            # Add form sections
            for section_name, section_data in filled_form.items():
                if section_name.startswith("_"):
                    continue

                # Section header
                section_style = ParagraphStyle(
                    "SectionHeader",
                    parent=styles["Heading2"],
                    fontSize=14,
                    spaceAfter=12,
                    spaceBefore=20,
                )

                section_title = Paragraph(
                    section_name.replace("_", " ").title(), section_style
                )
                story.append(section_title)

                # Section content
                for field_name, field_value in section_data.items():
                    if isinstance(field_value, (str, int, float)) and field_value:
                        field_text = f"<b>{field_name.replace('_', ' ').title()}:</b> {field_value}"
                        field_para = Paragraph(field_text, styles["Normal"])
                        story.append(field_para)
                        story.append(Spacer(1, 6))

                story.append(Spacer(1, 12))

            doc.build(story)
            logger.info(f"Exported form to PDF: {output_path}")
            return output_path

        except ImportError:
            logger.error("reportlab not installed. Install with: pip install reportlab")
            raise
        except Exception as e:
            logger.error(f"Error exporting form to PDF: {e}")
            raise

    def export_form_to_excel(
        self, filled_form: Dict[str, Any], output_path: str
    ) -> str:
        """Export filled form to Excel using openpyxl"""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment

            wb = Workbook()
            ws = wb.active
            ws.title = "HR Form"

            # Style definitions
            header_font = Font(bold=True, size=12)
            header_fill = PatternFill(
                start_color="CCCCCC", end_color="CCCCCC", fill_type="solid"
            )

            row = 1

            # Add form sections
            for section_name, section_data in filled_form.items():
                if section_name.startswith("_"):
                    continue

                # Section header
                ws.cell(row=row, column=1, value=section_name.replace("_", " ").title())
                ws.cell(row=row, column=1).font = header_font
                ws.cell(row=row, column=1).fill = header_fill
                row += 1

                # Section fields
                for field_name, field_value in section_data.items():
                    if isinstance(field_value, (str, int, float)) and field_value:
                        ws.cell(
                            row=row,
                            column=1,
                            value=field_name.replace("_", " ").title(),
                        )
                        ws.cell(row=row, column=2, value=str(field_value))
                        row += 1

                row += 1  # Empty row between sections

            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width

            wb.save(output_path)
            logger.info(f"Exported form to Excel: {output_path}")
            return output_path

        except ImportError:
            logger.error("openpyxl not installed. Install with: pip install openpyxl")
            raise
        except Exception as e:
            logger.error(f"Error exporting form to Excel: {e}")
            raise
