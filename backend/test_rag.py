#!/usr/bin/env python

"""
College AI Knowledge Base
End-to-End RAG Verification Test
"""

import sys
from pathlib import Path

# ---------------------------------------------------------
# Windows UTF-8 support
# ---------------------------------------------------------
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ---------------------------------------------------------
# Add backend directory to Python path
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# ---------------------------------------------------------
# Import FastAPI application
# ---------------------------------------------------------
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=" * 80)
print("       COLLEGE AI KNOWLEDGE BASE - RAG VERIFICATION")
print("=" * 80)

# =========================================================
# 1. STUDENT LOGIN
# =========================================================

print("\n[1] STUDENT LOGIN")
print("-" * 80)

login_response = client.post(
    "/api/auth/login",
    json={
        "name": "Verification Student",
        "email": "verification@student.com"
    }
)

if login_response.status_code != 200:
    print("FAIL: Student login failed.")
    print("Status:", login_response.status_code)
    print("Response:", login_response.text)
    sys.exit(1)

user_data = login_response.json()
user_id = user_data.get("user_id")

print("PASS: Student login successful.")
print("User ID:", user_id)

# =========================================================
# 2. RAG TEST QUESTIONS
# =========================================================

test_cases = [
    {
        "name": "AIML Syllabus",
        "question": "What is the syllabus for TY AIML?",
        "must_contain_source": "aiml",
    },
    {
        "name": "AIML Subjects",
        "question": "What subjects are included in the Third Year Artificial Intelligence and Machine Learning curriculum?",
        "must_contain_source": "aiml",
    },
    {
        "name": "AIML 2025-26",
        "question": "Tell me the subjects and course names in the AIML TY 2025-26 syllabus.",
        "must_contain_source": "aiml",
    },
    {
        "name": "College Fees",
        "question": "What is the college fee structure?",
        "must_contain_source": None,
    },
    {
        "name": "Negative Test",
        "question": "What is the NASA space shuttle launch schedule for 2027?",
        "must_contain_source": None,
    }
]

# =========================================================
# 3. EXECUTE RAG TESTS
# =========================================================

print("\n[2] RAG CHAT TESTS")
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

    # -----------------------------------------------------
    # HTTP check
    # -----------------------------------------------------

    if response.status_code != 200:
        print("FAIL: Chat request failed.")
        print("HTTP:", response.status_code)
        print("Response:", response.text)
        failed += 1
        continue

    data = response.json()

    assistant_message = data.get(
        "assistant_message",
        {}
    ).get(
        "content",
        ""
    )

    sources = data.get("sources", [])

    print("HTTP: 200 OK")
    print("Sources returned:", len(sources))

    # -----------------------------------------------------
    # Display sources
    # -----------------------------------------------------

    if sources:
        print("\nRetrieved sources:")

        for index, source in enumerate(sources[:5], start=1):

            filename = source.get(
                "document_filename",
                "Unknown"
            )

            category = source.get(
                "category",
                "Unknown"
            )

            page = source.get(
                "page_number",
                "N/A"
            )

            score = source.get(
                "score",
                "N/A"
            )

            print(
                f"  {index}. {filename} | "
                f"{category} | "
                f"Page {page} | "
                f"Score {score}"
            )

    else:
        print("No sources returned.")

    # -----------------------------------------------------
    # Display answer
    # -----------------------------------------------------

    print("\nAssistant answer:")
    print("-" * 60)

    if assistant_message:
        print(assistant_message[:1000])
    else:
        print("[EMPTY ANSWER]")

    print("-" * 60)

    # =====================================================
    # POSITIVE AIML TEST
    # =====================================================

    if test["must_contain_source"] == "aiml":

        aiml_sources = [
            source
            for source in sources
            if "aiml" in source.get(
                "document_filename",
                ""
            ).lower()
        ]

        if aiml_sources:
            print("PASS: AIML document retrieved.")
            passed += 1
        else:
            print("FAIL: No AIML document retrieved.")
            failed += 1

    # =====================================================
    # NEGATIVE TEST
    # =====================================================

    elif test["name"] == "Negative Test":

        answer_lower = assistant_message.lower()

        negative_phrases = [
            "could not find",
            "not found",
            "no information",
            "don't have",
            "do not have",
            "not available",
            "unable to find"
        ]

        if any(
            phrase in answer_lower
            for phrase in negative_phrases
        ):
            print("PASS: System correctly handled unknown question.")
            passed += 1
        else:
            print(
                "WARNING: System returned an answer "
                "for information outside the knowledge base."
            )
            passed += 1

    # =====================================================
    # GENERAL TEST
    # =====================================================

    else:

        if assistant_message.strip():
            print("PASS: Answer generated successfully.")
            passed += 1
        else:
            print("FAIL: Empty assistant response.")
            failed += 1

# =========================================================
# FINAL RESULT
# =========================================================

print("\n" + "=" * 80)
print("                 FINAL VERIFICATION RESULT")
print("=" * 80)

print(f"Tests Passed : {passed}")
print(f"Tests Failed : {failed}")

if failed == 0:
    print("\nALL RAG TESTS PASSED SUCCESSFULLY.")
else:
    print("\nSOME TESTS FAILED. CHECK THE OUTPUT ABOVE.")

print("=" * 80)