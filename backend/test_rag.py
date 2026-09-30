#!/usr/bin/env python

"""
CIT College Knowledge AI
End-to-End Entity-Aware RAG Verification Test Suite
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
print("       COIMBATORE INSTITUTE OF TECHNOLOGY (CIT) - RAG & ENTITY SUITE")
print("=" * 80)

# 1. LOGIN
login_response = client.post(
    "/api/auth/login",
    json={"name": "CIT Test Student", "email": "student@cit.edu.in"}
)
user_id = login_response.json().get("user_id")

test_cases = [
    {
        "name": "HOD of M.Sc Software Systems",
        "question": "Who is the HOD of M.Sc Software Systems?",
        "expected_type": "faculty",
        "expected_keyword": "Yamuna Devi",
    },
    {
        "name": "Eligibility for M.Sc Software Systems",
        "question": "What is the eligibility for M.Sc Software Systems?",
        "expected_type": "program",
        "expected_keyword": "Higher Secondary",
    },
    {
        "name": "Duration of M.Sc Software Systems",
        "question": "What is the duration of M.Sc Software Systems?",
        "expected_type": "program",
        "expected_keyword": "5 Years",
    },
    {
        "name": "HOD of CSE",
        "question": "Who is the HOD of CSE?",
        "expected_type": "faculty",
        "expected_keyword": "Kousalya",
    },
    {
        "name": "Non-existent Department HOD",
        "question": "Who is the HOD of XYZ Aerospace Quantum Department?",
        "expected_type": "not_found",
        "expected_keyword": "couldn't find",
    }
]

passed = 0
failed = 0

for number, test in enumerate(test_cases, start=1):
    print(f"\nTEST {number}: {test['name']}")
    print("Question:", test["question"])

    response = client.post("/api/chat", json={"user_id": user_id, "message": test["question"]})
    if response.status_code != 200:
        print("FAIL: Chat request failed", response.status_code)
        failed += 1
        continue

    data = response.json()
    answer = data.get("assistant_message", {}).get("content", "")
    resp_type = data.get("type") or data.get("assistant_message", {}).get("type")
    entity = data.get("entity") or data.get("assistant_message", {}).get("entity")

    print(f"HTTP 200 OK | Response Type: {resp_type}")
    if entity:
        print(f"Entity Matched: {entity.get('name')} | {entity.get('designation')} | Dept: {entity.get('department')}")

    print("Answer:")
    print("-" * 50)
    print(answer)
    print("-" * 50)

    lowered_ans = answer.lower()
    kw = test["expected_keyword"].lower()

    if (kw in lowered_ans or (resp_type == test["expected_type"])):
        print(f"PASS: Test '{test['name']}' passed cleanly!")
        passed += 1
    else:
        print(f"FAIL: Keyword '{test['expected_keyword']}' or type '{test['expected_type']}' not met.")
        failed += 1

print("\n" + "=" * 80)
print(f"FINAL ENTITY TEST RESULT: {passed} PASSED, {failed} FAILED")
print("=" * 80)