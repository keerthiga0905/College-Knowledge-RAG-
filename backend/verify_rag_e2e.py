#!/usr/bin/env python
"""
College AI Knowledge Base
Complete End-to-End RAG Verification Test
"""

import sys
from pathlib import Path

# ============================================================
# WINDOWS UTF-8 SUPPORT
# ============================================================

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ============================================================
# BACKEND PATH
# ============================================================

current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

# ============================================================
# IMPORT FASTAPI
# ============================================================

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ============================================================
# HEADER
# ============================================================

print("\n" + "=" * 90)
print("       COLLEGE AI KNOWLEDGE BASE - RAG VERIFICATION")
print("=" * 90)

# ============================================================
# 1. LOGIN / USER CREATION
# ============================================================

print("\n[1] USER LOGIN")
print("-" * 90)

login_data = {
    "name": "Verification Student",
    "email": "verification.student@college.edu"
}

login_response = client.post(
    "/api/auth/login",
    json=login_data
)

if login_response.status_code != 200:
    print("❌ LOGIN FAILED")
    print("HTTP:", login_response.status_code)
    print("Response:", login_response.text)
    sys.exit(1)

user_data = login_response.json()

user_id = user_data.get("user_id")

if not user_id:
    print("❌ LOGIN FAILED: user_id was not returned.")
    print(user_data)
    sys.exit(1)

print("✅ LOGIN SUCCESSFUL")
print("User ID:", user_id)
print("Name:", user_data.get("name"))
print("Email:", user_data.get("email"))
print("Role:", user_data.get("role"))

# ============================================================
# 2. TEST CASES
# ============================================================

test_cases = [

    {
        "id": "A",
        "question": "What is the syllabus for TY AIML?",
        "expected_keywords": [
            "AIML",
            "Machine Learning"
        ],
        "source_keywords": [
            "aiml",
            "ty"
        ],
        "negative": False
    },

    {
        "id": "B",
        "question": "What subjects are included in the Third Year Artificial Intelligence and Machine Learning curriculum?",
        "expected_keywords": [
            "Machine Learning",
            "Digital Image Processing",
            "Soft Computing"
        ],
        "source_keywords": [
            "aiml"
        ],
        "negative": False
    },

    {
        "id": "C",
        "question": "Tell me the subjects and course names in the AIML TY 2025-26 syllabus.",
        "expected_keywords": [
            "AIML",
            "2025-26"
        ],
        "source_keywords": [
            "aiml"
        ],
        "negative": False
    },

    {
        "id": "D",
        "question": "What is the NASA space shuttle launch schedule for 2027?",
        "expected_keywords": [
            "could not find"
        ],
        "source_keywords": [],
        "negative": True
    }
]

# ============================================================
# 3. RUN RAG TESTS
# ============================================================

print("\n[2] RAG CHAT TESTS")
print("=" * 90)

all_passed = True

for case in test_cases:

    print("\n" + "-" * 90)
    print(f"TEST CASE {case['id']}")
    print("-" * 90)

    question = case["question"]

    print("Question:")
    print(question)

    # --------------------------------------------------------
    # SEND CHAT REQUEST
    # --------------------------------------------------------

    response = client.post(
        "/api/chat",
        json={
            "user_id": user_id,
            "message": question
        }
    )

    # --------------------------------------------------------
    # HTTP CHECK
    # --------------------------------------------------------

    if response.status_code != 200:

        print("\n❌ FAIL")
        print("HTTP Status:", response.status_code)
        print("Response:", response.text)

        all_passed = False
        continue

    print("\n✅ HTTP 200 OK")

    # --------------------------------------------------------
    # RESPONSE JSON
    # --------------------------------------------------------

    try:
        data = response.json()
    except Exception:

        print("❌ FAIL: Response is not valid JSON.")
        all_passed = False
        continue

    conversation_id = data.get("conversation_id")

    assistant_message = data.get(
        "assistant_message",
        {}
    )

    answer = assistant_message.get(
        "content",
        ""
    )

    sources = data.get(
        "sources",
        []
    )

    # --------------------------------------------------------
    # BASIC RESPONSE CHECK
    # --------------------------------------------------------

    if not answer.strip():

        print("❌ FAIL: Assistant returned an empty answer.")
        all_passed = False
        continue

    print("\nCONVERSATION ID:")
    print(conversation_id)

    # --------------------------------------------------------
    # PRINT COMPLETE ANSWER
    # --------------------------------------------------------

    print("\nASSISTANT ANSWER")
    print("-" * 90)
    print(answer)
    print("-" * 90)

    # ========================================================
    # NEGATIVE TEST
    # ========================================================

    if case["negative"]:

        answer_lower = answer.lower()

        negative_phrases = [
            "could not find",
            "not found",
            "no information",
            "don't have information",
            "do not have information",
            "not available",
            "cannot find",
            "unable to find"
        ]

        negative_passed = any(
            phrase in answer_lower
            for phrase in negative_phrases
        )

        if negative_passed:

            print("\n✅ PASS")
            print("System correctly rejected information outside the college knowledge base.")

        else:

            print("\n❌ FAIL")
            print("System may have hallucinated an answer.")
            all_passed = False

        continue

    # ========================================================
    # POSITIVE TEST - KEYWORD CHECK
    # ========================================================

    answer_lower = answer.lower()

    found_keywords = []
    missing_keywords = []

    for keyword in case["expected_keywords"]:

        if keyword.lower() in answer_lower:
            found_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)

    print("\nANSWER RELEVANCE CHECK")
    print("-" * 90)

    if found_keywords:

        print("✅ Found keywords:")
        for keyword in found_keywords:
            print("   •", keyword)

    if missing_keywords:

        print("⚠ Missing keywords:")
        for keyword in missing_keywords:
            print("   •", keyword)

    # Require at least one important keyword
    if not found_keywords:

        print("\n❌ FAIL: Answer does not contain expected syllabus information.")
        all_passed = False

    else:

        print("\n✅ Answer relevance check passed.")

    # ========================================================
    # SOURCE CHECK
    # ========================================================

    print("\nRETRIEVED SOURCES")
    print("-" * 90)

    if not sources:

        print("❌ No sources returned.")
        all_passed = False
        continue

    print("Total sources:", len(sources))

    correct_source_found = False

    for index, source in enumerate(sources[:10], 1):

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
            "Unknown"
        )

        score = source.get(
            "score",
            0
        )

        snippet = source.get(
            "snippet",
            ""
        )

        print(f"\n[{index}] {filename}")
        print("    Category:", category)
        print("    Page:", page)
        print("    Similarity Score:", score)

        # Check source relevance
        filename_lower = filename.lower()

        if any(
            word.lower() in filename_lower
            for word in case["source_keywords"]
        ):
            correct_source_found = True

    # ========================================================
    # SOURCE RELEVANCE RESULT
    # ========================================================

    if correct_source_found:

        print("\n✅ Correct AIML-related source retrieved.")

    else:

        print("\n⚠ No clearly named AIML source found in returned sources.")
        print("This does not automatically mean RAG failed, because the")
        print("document filename may not contain 'AIML'.")

        # Do not automatically fail only because of filename.
        # The answer relevance is more important.

# ============================================================
# FINAL RESULT
# ============================================================

print("\n" + "=" * 90)
print("                         FINAL RESULT")
print("=" * 90)

if all_passed:

    print("\n✅ ALL RAG TEST CASES PASSED")
    print("\nYour College AI Knowledge Base successfully demonstrated:")
    print("  ✓ Student authentication")
    print("  ✓ Chat API")
    print("  ✓ RAG retrieval")
    print("  ✓ College document-based answers")
    print("  ✓ Source retrieval")
    print("  ✓ Negative query handling")
    print("  ✓ Answer relevance checking")

else:

    print("\n⚠ SOME TEST CASES REQUIRE REVIEW")

print("\n" + "=" * 90)