import pymupdf as fitz
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

PDF_SPECS = [
    {
        "path": ROOT_DIR / "01_College_information" / "CIT_Official_Brochure_and_Governance.pdf",
        "title": "COIMBATORE INSTITUTE OF TECHNOLOGY (CIT)",
        "subtitle": "Official Institutional Overview & Autonomous Governance 2026",
        "content": [
            "Coimbatore Institute of Technology (CIT), Peelamedu, Coimbatore - 641014, Tamil Nadu.",
            "Established in 1956 by V. Rangaswamy Naidu Educational Trust (VRET).",
            "Affiliated to Anna University, Approved by AICTE, Accredited by NAAC with 'A' Grade.",
            "Granted Autonomous status in 1987 by UGC and Anna University.",
            "Motto: Progress Through Technology.",
            "Official Contact: Phone 0422-2574071 | Email: principal@cit.edu.in | Website: www.cit.edu.in",
            "",
            "Key Academic Highlights:",
            "- Offering 9 B.E./B.Tech programs, 12 M.E./M.Tech programs, MCA, 5-Yr Integrated M.Sc.",
            "- Over 200+ experienced faculty members with high research citations.",
            "- Active MoUs with Bosch, Texas Instruments, Qualcomm, IBM, TCS, L&T, and Caterpillar.",
            "- 25+ Acre Lush Green Autonomous Campus located along Avinashi Road in Peelamedu, Coimbatore."
        ]
    },
    {
        "path": ROOT_DIR / "02_Syllabus" / "CIT_Academic_Regulations_and_Examination_Rules.pdf",
        "title": "CIT ACADEMIC REGULATIONS & EXAM RULES 2026",
        "subtitle": "Coimbatore Institute of Technology - Autonomous Regulations",
        "content": [
            "1. Attendance Regulations:",
            "- Minimum required attendance is 75% aggregate across all registered courses in a semester.",
            "- Condonation for shortage (65% to 74%) may be sanctioned by the Principal for genuine medical grounds.",
            "- Students below 65% attendance are detained and must repeat the semester.",
            "",
            "2. Choice Based Credit System (CBCS):",
            "- Total credits required for B.E. / B.Tech degree: 160 - 165 Credits.",
            "- Grading System: O (10), A+ (9), A (8), B+ (7), B (6), C (5), RA (Re-appear/Fail, <45 Marks).",
            "- Evaluation: 40% Continuous Assessment (CAT 1 & CAT 2) + 60% End Semester Exam."
        ]
    },
    {
        "path": ROOT_DIR / "02_Syllabus" / "CIT_BTech_AIML_and_CSE_Syllabus_Structure.pdf",
        "title": "CIT B.E. CSE & B.Tech AI & ML SYLLABUS",
        "subtitle": "Department of Computer Science & Engineering (AIML)",
        "content": [
            "Semester 5 (3rd Year):",
            "- Artificial Intelligence & Search Strategies (3 Credits)",
            "- Machine Learning Algorithms - Supervised & Unsupervised (4 Credits)",
            "- Web Technologies & Frameworks (3 Credits)",
            "- AI & Machine Learning Laboratory (2 Credits)",
            "",
            "Semester 6 (3rd Year):",
            "- Natural Language Processing & Text Mining (3 Credits)",
            "- Computer Vision & Image Processing (3 Credits)",
            "- Big Data Analytics & Distributed Systems (3 Credits)",
            "- Mini Project & Innovation Lab (2 Credits)"
        ]
    },
    {
        "path": ROOT_DIR / "05_Fees_Placement_Funding" / "CIT_Placement_Statistics_and_Fee_Structure.pdf",
        "title": "CIT CAREER PLACEMENTS & FEE STRUCTURE 2026",
        "subtitle": "Career Guidance & Placement Cell (CGPC), CIT Coimbatore",
        "content": [
            "1. Placement Statistics:",
            "- Over 90% placement rate consistently achieved.",
            "- Highest Salary Package: Rs. 42.0 to 52.0 Lakhs Per Annum (LPA).",
            "- Average Salary Package: Rs. 7.5 to 9.5 Lakhs Per Annum (LPA).",
            "- Top Recruiters: Amazon, Microsoft, Bosch, Texas Instruments, Qualcomm, TCS, Cognizant, Wipro, L&T.",
            "",
            "2. Fee Structure & Scholarships:",
            "- Government Aided B.E. Tuition Fee: Approx Rs 15,000 - Rs 25,000 / year.",
            "- Self-Supporting B.Tech Tuition Fee: Approx Rs 50,000 - Rs 70,000 / year.",
            "- Govt First Generation Graduate Scholarship & BC/MBC/SC/ST Scholarships available."
        ]
    }
]

def generate_pdfs():
    for spec in PDF_SPECS:
        doc = fitz.open()
        page = doc.new_page(width=595, height=842) # A4 size
        
        y = 50
        # Title
        page.insert_text(fitz.Point(40, y), spec["title"], fontsize=14, fontname="helv")
        y += 25
        page.insert_text(fitz.Point(40, y), spec["subtitle"], fontsize=11, fontname="helv")
        y += 35
        
        for line in spec["content"]:
            if y > 800:
                page = doc.new_page(width=595, height=842)
                y = 50
            page.insert_text(fitz.Point(40, y), line, fontsize=10, fontname="helv")
            y += 18
            
        doc.save(str(spec["path"]))
        doc.close()
        print(f"Generated PDF: {spec['path'].name}")

if __name__ == "__main__":
    generate_pdfs()
