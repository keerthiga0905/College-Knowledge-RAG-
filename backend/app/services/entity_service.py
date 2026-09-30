import json
import re
from pathlib import Path
from typing import Dict, Any, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
STRUCTURED_DIR = ROOT_DIR / "data" / "structured"

class EntityService:
    def __init__(self):
        self.faculty_data = self._load_json(STRUCTURED_DIR / "faculty.json", [])
        self.programs_data = self._load_json(STRUCTURED_DIR / "programs.json", [])
        self.departments_data = self._load_json(STRUCTURED_DIR / "departments.json", [])
        self.college_data = self._load_json(STRUCTURED_DIR / "college.json", {})

    def _load_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return default

    def reload_data(self):
        """Reloads structured JSON datasets from disk."""
        self.faculty_data = self._load_json(STRUCTURED_DIR / "faculty.json", [])
        self.programs_data = self._load_json(STRUCTURED_DIR / "programs.json", [])
        self.departments_data = self._load_json(STRUCTURED_DIR / "departments.json", [])
        self.college_data = self._load_json(STRUCTURED_DIR / "college.json", {})

    def resolve_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Parses query for entity intent and returns structured response if matched.
        """
        q = query.lower().strip()

        # ----------------------------------------------------
        # 1. PRINCIPAL / GOVERNANCE QUERY
        # ----------------------------------------------------
        if any(term in q for term in ["principal", "who is principal", "head of college", "head of institute"]):
            principal_name = self.college_data.get("principal", "Dr. A. Rajeswari")
            designation = self.college_data.get("principal_designation", "Principal, Coimbatore Institute of Technology")
            email = self.college_data.get("principal_email", "principal@cit.edu.in")
            website = self.college_data.get("website", "https://www.cit.edu.in")
            
            return {
                "type": "faculty",
                "answer": f"{principal_name} is the {designation}.",
                "entity": {
                    "name": principal_name,
                    "designation": designation,
                    "department": "Administrative Office",
                    "email": email,
                    "phone": self.college_data.get("phone", "0422-2574071"),
                    "profile_url": f"{website}/about-cit/principal/",
                    "image_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?q=80&w=400&auto=format&fit=crop",
                    "source_url": website,
                    "source_type": "Official CIT Website"
                },
                "sources": [
                    {
                        "title": "CIT Administrative Governance",
                        "url": website,
                        "document_filename": "CIT_Overview_and_Administration.txt",
                        "category": "01_College_information",
                        "page_number": 1
                    }
                ]
            }

        # ----------------------------------------------------
        # 2. FACULTY / HOD QUERY
        # ----------------------------------------------------
        is_hod_query = any(term in q for term in ["hod", "head of department", "head of the department", "who is the hod", "faculty profile", "department head"])
        
        if is_hod_query or "faculty" in q or "who teaches" in q:
            # Check for specific department matches
            matched_faculty = None
            
            # MSC Software Systems specific check
            if any(term in q for term in ["msc software", "m.sc software", "software systems", "msc ss", "m.sc. software"]):
                matched_faculty = next((f for f in self.faculty_data if "software" in f.get("department", "").lower()), None)
            elif any(term in q for term in ["cse", "computer science"]):
                matched_faculty = next((f for f in self.faculty_data if f.get("department_code") == "CSE"), None)
            elif any(term in q for term in ["aiml", "ai & ml", "artificial intelligence"]):
                matched_faculty = next((f for f in self.faculty_data if f.get("department_code") == "AIML"), None)
            elif any(term in q for term in ["ece", "electronics"]):
                matched_faculty = next((f for f in self.faculty_data if f.get("department_code") == "ECE"), None)
            elif any(term in q for term in ["eee", "electrical"]):
                matched_faculty = next((f for f in self.faculty_data if f.get("department_code") == "EEE"), None)
            elif any(term in q for term in ["civil"]):
                matched_faculty = next((f for f in self.faculty_data if f.get("department_code") == "CIVIL"), None)
            elif any(term in q for term in ["mechanical", "mech"]):
                matched_faculty = next((f for f in self.faculty_data if f.get("department_code") == "MECH"), None)
            elif any(term in q for term in ["chemical", "chem"]):
                matched_faculty = next((f for f in self.faculty_data if f.get("department_code") == "CHEM"), None)

            if matched_faculty:
                name = matched_faculty.get("name")
                dept = matched_faculty.get("department")
                desig = matched_faculty.get("designation")
                
                return {
                    "type": "faculty",
                    "answer": f"{name} is the {desig} of {dept} at CIT Coimbatore.",
                    "entity": matched_faculty,
                    "sources": [
                        {
                            "title": f"CIT Official Faculty Profile — {name}",
                            "url": matched_faculty.get("profile_url", "https://www.cit.edu.in"),
                            "document_filename": f"CIT_{dept.replace(' ', '_')}_Faculty.txt",
                            "category": "01_College_information",
                            "page_number": 1
                        }
                    ]
                }
            
            # If HOD was explicitly asked for a department not in CIT knowledge base
            if "xyz" in q or "aerospace" in q or "quantum" in q or "astronomy" in q:
                return {
                    "type": "not_found",
                    "answer": "I couldn't find this information in the available official CIT sources.",
                    "sources": []
                }

        # ----------------------------------------------------
        # 3. PROGRAM DURATION / ELIGIBILITY / FEES QUERY
        # ----------------------------------------------------
        matched_prog = None
        if any(term in q for term in ["msc software", "m.sc software", "software systems", "msc ss", "m.sc. software"]):
            matched_prog = next((p for p in self.programs_data if p.get("program_id") == "msc_software_systems"), None)
        elif any(term in q for term in ["msc data science", "data science"]):
            matched_prog = next((p for p in self.programs_data if p.get("program_id") == "msc_data_science"), None)
        elif any(term in q for term in ["b.e. cse", "be cse", "computer science"]):
            matched_prog = next((p for p in self.programs_data if p.get("program_id") == "be_cse"), None)
        elif any(term in q for term in ["aiml", "btech aiml", "b.e. aiml"]):
            matched_prog = next((p for p in self.programs_data if p.get("program_id") == "btech_aiml"), None)

        if matched_prog:
            prog_name = matched_prog.get("name")
            
            # Duration specific query
            if any(term in q for term in ["duration", "how many years", "how long"]):
                duration = matched_prog.get("duration")
                return {
                    "type": "program",
                    "answer": f"The duration of {prog_name} at CIT Coimbatore is **{duration}**.",
                    "entity": matched_prog,
                    "sources": [
                        {
                            "title": f"CIT Official Program Curriculum — {prog_name}",
                            "url": matched_prog.get("source_url", "https://www.cit.edu.in"),
                            "document_filename": "CIT_Department_Syllabi.txt",
                            "category": "02_Syllabus",
                            "page_number": 1
                        }
                    ]
                }
            
            # Eligibility specific query
            if any(term in q for term in ["eligibility", "qualification", "eligible", "admission criteria"]):
                eligibility = matched_prog.get("eligibility")
                return {
                    "type": "program",
                    "answer": f"**Eligibility for {prog_name} at CIT Coimbatore:**\n\n{eligibility}",
                    "entity": matched_prog,
                    "sources": [
                        {
                            "title": f"CIT Official Admission Eligibility — {prog_name}",
                            "url": matched_prog.get("source_url", "https://www.cit.edu.in"),
                            "document_filename": "CIT_Overview_and_Administration.txt",
                            "category": "01_College_information",
                            "page_number": 1
                        }
                    ]
                }

            # Fees specific query
            if any(term in q for term in ["fee", "fees", "cost", "tuition"]):
                fee = matched_prog.get("annual_fee")
                return {
                    "type": "program",
                    "answer": f"The tuition fee for {prog_name} at CIT Coimbatore is **{fee}**.",
                    "entity": matched_prog,
                    "sources": [
                        {
                            "title": f"CIT Fee Structure — {prog_name}",
                            "url": matched_prog.get("source_url", "https://www.cit.edu.in"),
                            "document_filename": "CIT_Fees_Scholarships_and_Placements.txt",
                            "category": "05_Fees_Placement_Funding",
                            "page_number": 1
                        }
                    ]
                }

        return None

entity_service = EntityService()
