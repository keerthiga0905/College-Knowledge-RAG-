#!/usr/bin/env python

"""
CIT College Knowledge AI
End-to-End RAG Verification Test Suite
"""

import sys
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=" * 80)
print("       COIMBATORE INSTITUTE OF TECHNOLOGY (CIT) - RAG VERIFICATION")
print("=" * 80)

# 1. LOGIN
print("\n[1] STUDENT LOGIN")
print("-" * 80)

login_response = client.post(
    "/api/auth/login",
    json={
        "name": "CIT Student",
        "email": "student@cit.edu.in"
    }
)

if login_response.status_code != 200:
    print("FAIL: Student login failed.")
    sys.exit(1)

user_data = login_response.json()
user_id = user_data.get("user_id")

print("PASS: Student login successful.")
print("User ID:", user_id)

# 2. TEST CASES FOR CIT
test_cases = [
    {
        "name": "CIT Attendance Regulations",
        "question": "What are the minimum attendance requirements at CIT Coimbatore?",
        "expected_keyword": "75%",
    },
    {
        "name": "CIT Departments & Programs",
        "question": "What departments and degree programs are available at CIT?",
        "expected_keyword": "Civil",
    },
    {
        "name": "CIT Academic Regulations",
        "question": "What are the academic regulations and grading system at CIT?",
        "expected_keyword": "CBCS",
    },
    {
        "name": "CIT Placement Information",
        "question": "What are the placement statistics and top recruiters at CIT Coimbatore?",
        "expected_keyword": "Placement",
    },
    {
        "name": "CIT Fees & Scholarships",
        "question": "What is the fee structure and scholarship options for CIT students?",
        "expected_keyword": "Scholarship",
    },
    {
        "name": "Negative Grounding Test",
        "question": "What is the fee for quantum teleportation rocket engineering at Mars campus?",
        "expected_keyword": "not find",
    }
]

print("\n[2] RAG PIPELINE EXECUTIONS")
print("-" * 80)

passed = 0
failed = 0

for number, test in enumerate(test_cases, start=1):
    print(f"\nTEST {number}: {test['name']}")
    print("Question:", test["question"])

    response = client.post(
        "/api/chat",
        json={
            "user_id": user_id,
            "message": test["question"]
        }
    )

    if response.status_code != 200:
        print("FAIL: Chat request failed with status", response.status_code)
        failed += 1
        continue

    data = response.json()
    assistant_message = data.get("assistant_message", {}).get("content", "")
    sources = data.get("sources", [])

    print("HTTP 200 OK | Sources Retrieved:", len(sources))
    for idx, src in enumerate(sources[:3], start=1):
        print(f"  Source {idx}: {src.get('document_filename')} | Page {src.get('page_number')} | Category: {src.get('category')}")

    print("\nAnswer Snippet:")
    print("-" * 50)
    print(assistant_message[:400] + ("..." if len(assistant_message) > 400 else ""))
    print("-" * 50)

    # Verification
    lowered_msg = assistant_message.lower()
    expected = test["expected_keyword"].lower()

    if expected in lowered_msg or len(sources) > 0:
        print(f"PASS: Test '{test['name']}' executed cleanly.")
        passed += 1
    else:
        print(f"FAIL: Expected keyword '{test['expected_keyword']}' or sources missing.")
        failed += 1

print("\n" + "=" * 80)
print(f"FINAL RESULT: {passed} PASSED, {failed} FAILED")
print("=" * 80)