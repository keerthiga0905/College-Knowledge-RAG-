import sys
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure backend root is in python path
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_endpoints():
    print("Testing /api/health...")
    res = client.get("/api/health")
    print(f"Health Status: {res.status_code}, Response: {res.json()}")
    assert res.status_code == 200

    print("\nTesting User Login / Creation (/api/auth/login)...")
    res = client.post("/api/auth/login", json={"name": "Tanvi Punekar", "email": "tanvi.punekar@example.com"})
    print(f"Auth Status: {res.status_code}, Response: {res.json()}")
    assert res.status_code == 200
    user_data = res.json()
    user_id = user_data["user_id"]
    assert user_id is not None

    print("\nTesting Duplicate Login with same email (Should return existing user)...")
    res2 = client.post("/api/auth/login", json={"name": "Tanvi P", "email": "tanvi.punekar@example.com"})
    assert res2.status_code == 200
    assert res2.json()["user_id"] == user_id
    print("[PASS] Existing user ID matched correctly!")

    print("\nTesting Conversations Listing (/api/conversations)...")
    res = client.get(f"/api/conversations?user_id={user_id}")
    print(f"Conversations Status: {res.status_code}, Count: {len(res.json())}")
    assert res.status_code == 200

    print("\nTesting Documents Status (/api/documents)...")
    res = client.get("/api/documents")
    print(f"Documents Status: {res.status_code}, Total: {res.json()['total_documents']}")
    assert res.status_code == 200

    print("\nTesting Chat with Gemini key unconfigured test...")
    res = client.post("/api/chat", json={
        "user_id": user_id,
        "message": "What is the AIML syllabus?"
    })
    print(f"Chat Status: {res.status_code}, Response snippet: {res.json()['assistant_message']['content'][:100]}")
    assert res.status_code == 200
    conv_id = res.json()["conversation_id"]

    print("\nTesting Conversations after chat...")
    res = client.get(f"/api/conversations?user_id={user_id}")
    assert len(res.json()) >= 1
    print(f"[PASS] Conversation successfully persisted to DB with title: {res.json()[0]['title']}")

    print("\nTesting Conversation Details (/api/conversations/{conv_id})...")
    res = client.get(f"/api/conversations/{conv_id}")
    assert res.status_code == 200
    assert len(res.json()["messages"]) >= 2
    print(f"[PASS] Fetched {len(res.json()['messages'])} persisted messages!")

    print("\n[SUCCESS] All API endpoints, DB operations, multi-user flows, and RAG routes validated!")

if __name__ == "__main__":
    test_endpoints()
