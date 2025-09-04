"""
Database Manager for candidate data storage and retrieval
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations for candidate data"""

    def __init__(self, db_path: str = "candidate_database.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Candidates table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS candidates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT,
                        phone TEXT,
                        linkedin_url TEXT,
                        resume_path TEXT,
                        skills TEXT,  -- JSON string
                        experience_years INTEGER,
                        education TEXT,
                        current_position TEXT,
                        current_company TEXT,
                        location TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Skills table for normalized skill storage
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS skills (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        skill_name TEXT UNIQUE NOT NULL,
                        category TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Candidate-Skills junction table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS candidate_skills (
                        candidate_id INTEGER,
                        skill_id INTEGER,
                        proficiency_level TEXT,
                        source TEXT,  -- 'resume', 'linkedin', 'ai_inferred'
                        PRIMARY KEY (candidate_id, skill_id),
                        FOREIGN KEY (candidate_id) REFERENCES candidates (id),
                        FOREIGN KEY (skill_id) REFERENCES skills (id)
                    )
                """
                )

                # Forms table for generated HR forms
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS generated_forms (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        candidate_id INTEGER,
                        form_type TEXT,
                        form_data TEXT,  -- JSON string
                        file_path TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (candidate_id) REFERENCES candidates (id)
                    )
                """
                )

                conn.commit()
                logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def add_candidate(self, candidate_data: Dict[str, Any]) -> int:
        """Add a new candidate to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Convert lists to JSON strings
                skills_json = json.dumps(candidate_data.get("skills", []))
                education_json = json.dumps(candidate_data.get("education", []))
                experience_json = json.dumps(candidate_data.get("experience", []))

                cursor.execute(
                    """
                    INSERT INTO candidates (
                        name, email, phone, linkedin_url, resume_path, skills,
                        experience_years, education, current_position, 
                        current_company, location
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        candidate_data.get("name"),
                        candidate_data.get("email"),
                        candidate_data.get("phone"),
                        candidate_data.get("linkedin_url"),
                        candidate_data.get("resume_path"),
                        skills_json,
                        candidate_data.get("experience_years"),
                        education_json,
                        candidate_data.get("current_position"),
                        candidate_data.get("current_company"),
                        candidate_data.get("location"),
                    ),
                )

                candidate_id = cursor.lastrowid
                conn.commit()

                # Add skills to normalized tables
                if candidate_data.get("skills"):
                    self._add_candidate_skills(candidate_id, candidate_data["skills"])

                logger.info(
                    f"Added candidate: {candidate_data.get('name')} (ID: {candidate_id})"
                )
                return candidate_id

        except Exception as e:
            logger.error(f"Error adding candidate: {e}")
            raise

    def get_candidate(self, candidate_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve candidate data by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,))
                row = cursor.fetchone()

                if row:
                    columns = [description[0] for description in cursor.description]
                    candidate_data = dict(zip(columns, row))

                    # Parse skills JSON
                    if candidate_data["skills"]:
                        candidate_data["skills"] = json.loads(candidate_data["skills"])
                    else:
                        candidate_data["skills"] = []

                    return candidate_data
                return None

        except Exception as e:
            logger.error(f"Error retrieving candidate: {e}")
            raise

    def search_candidates(self, query: str) -> List[Dict[str, Any]]:
        """Search candidates by name, skills, or other criteria"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Search in multiple fields
                cursor.execute(
                    """
                    SELECT * FROM candidates 
                    WHERE name LIKE ? OR skills LIKE ? OR current_position LIKE ? 
                    OR current_company LIKE ? OR education LIKE ?
                """,
                    (
                        f"%{query}%",
                        f"%{query}%",
                        f"%{query}%",
                        f"%{query}%",
                        f"%{query}%",
                    ),
                )

                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]

                candidates = []
                for row in rows:
                    candidate_data = dict(zip(columns, row))
                    if candidate_data["skills"]:
                        candidate_data["skills"] = json.loads(candidate_data["skills"])
                    else:
                        candidate_data["skills"] = []
                    candidates.append(candidate_data)

                return candidates

        except Exception as e:
            logger.error(f"Error searching candidates: {e}")
            raise

    def update_candidate(self, candidate_id: int, update_data: Dict[str, Any]) -> bool:
        """Update candidate data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Build dynamic update query
                set_clauses = []
                values = []

                for key, value in update_data.items():
                    if key == "skills":
                        value = json.dumps(value) if value else "[]"
                    set_clauses.append(f"{key} = ?")
                    values.append(value)

                if set_clauses:
                    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                    values.append(candidate_id)

                    query = (
                        f"UPDATE candidates SET {', '.join(set_clauses)} WHERE id = ?"
                    )
                    cursor.execute(query, values)
                    conn.commit()

                    # Update skills if provided
                    if "skills" in update_data and update_data["skills"]:
                        self._add_candidate_skills(candidate_id, update_data["skills"])

                    logger.info(f"Updated candidate ID: {candidate_id}")
                    return True
                return False

        except Exception as e:
            logger.error(f"Error updating candidate: {e}")
            raise

    def _add_candidate_skills(self, candidate_id: int, skills: List[str]):
        """Add skills to normalized tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                for skill in skills:
                    # Insert skill if not exists
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO skills (skill_name, category) 
                        VALUES (?, ?)
                    """,
                        (skill, "technical"),
                    )  # Default category

                    # Get skill ID
                    cursor.execute(
                        "SELECT id FROM skills WHERE skill_name = ?", (skill,)
                    )
                    skill_id = cursor.fetchone()[0]

                    # Link candidate to skill
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO candidate_skills 
                        (candidate_id, skill_id, proficiency_level, source)
                        VALUES (?, ?, ?, ?)
                    """,
                        (candidate_id, skill_id, "intermediate", "ai_inferred"),
                    )

                conn.commit()

        except Exception as e:
            logger.error(f"Error adding candidate skills: {e}")
            raise

    def save_generated_form(
        self,
        candidate_id: int,
        form_type: str,
        form_data: Dict[str, Any],
        file_path: str = None,
    ) -> int:
        """Save generated HR form data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO generated_forms 
                    (candidate_id, form_type, form_data, file_path)
                    VALUES (?, ?, ?, ?)
                """,
                    (candidate_id, form_type, json.dumps(form_data), file_path),
                )

                form_id = cursor.lastrowid
                conn.commit()

                logger.info(f"Saved generated form ID: {form_id}")
                return form_id

        except Exception as e:
            logger.error(f"Error saving generated form: {e}")
            raise

    def get_all_candidates(self) -> List[Dict[str, Any]]:
        """Get all candidates from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM candidates ORDER BY created_at DESC")

                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]

                candidates = []
                for row in rows:
                    candidate_data = dict(zip(columns, row))
                    if candidate_data["skills"]:
                        candidate_data["skills"] = json.loads(candidate_data["skills"])
                    else:
                        candidate_data["skills"] = []
                    candidates.append(candidate_data)

                return candidates

        except Exception as e:
            logger.error(f"Error retrieving all candidates: {e}")
            raise

    def export_to_dataframe(self) -> pd.DataFrame:
        """Export all candidate data to pandas DataFrame"""
        try:
            candidates = self.get_all_candidates()
            return pd.DataFrame(candidates)
        except Exception as e:
            logger.error(f"Error exporting to DataFrame: {e}")
            raise
