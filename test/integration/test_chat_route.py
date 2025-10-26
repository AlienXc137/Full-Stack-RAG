import pytest

# Sends a request with a fake session ID ("nope") that doesn’t exist in main.SESSIONS.
# Expected:Status 400, Error detail: "Invalid or expired session_id"
def test_chat_invalid_session_returns_400(client, clear_sessions, stub_rag):
    body = {"session_id": "nope", "message": "hi"} 
    resp = client.post("/chat", json=body) 
    assert resp.status_code == 400
    assert "Invalid or expired" in resp.json()["detail"]

# Sets up a valid session but sends an empty message:
# Expected: Status 400, Error detail: "Message cannot be empty"
def test_chat_empty_message_returns_400(client, clear_sessions, stub_rag):
    sid = "sess_test"
    import main
    main.SESSIONS[sid] = []
    body = {"session_id": sid, "message": "   "}
    resp = client.post("/chat", json=body)
    assert resp.status_code == 400
    assert "Message cannot be empty" in resp.json()["detail"]

# This is your happy path.
# Expected: Status 200, Response JSON: {"answer": "stubbed answer"}, Session history updated: 2 messages (user + assistant)
# Validates that: The stub_rag fixture correctly mocks your RAG backend to always return "stubbed answer". History appending logic in main.py works.
def test_chat_success_returns_answer_and_appends_history(client, clear_sessions, stub_rag):
    sid = "sess_test"
    import main
    main.SESSIONS[sid] = []
    body = {"session_id": sid, "message": "Hello"}
    resp = client.post("/chat", json=body)
    assert resp.status_code == 200
    assert resp.json()["answer"] == "stubbed answer"
    assert len(main.SESSIONS[sid]) == 2

# This is a fault injection test — it simulates a failure during RAG loading to ensure your exception handling logic works.
# Checks: Server returns 500, Error message contains "fail load"
# Confirms: Your backend correctly catches DocumentPortalException, Converts it to HTTP 500 with JSON detail message, No raw stack traces leak to clients
def test_chat_failure_returns_500(client, clear_sessions, monkeypatch):
    sid = "sess_test"
    import main
    main.SESSIONS[sid] = []

    import main
 
    class BoomRAG: # RAG that always fails on load
        def __init__(self, session_id=None): 
            pass # Dummy init
        def load_retriever_from_faiss(self, *a, **k): 
            from multi_doc_chat.exception.custom_exception import DocumentPortalException 
            raise DocumentPortalException("fail load", None)

    monkeypatch.setattr(main, "ConversationalRAG", BoomRAG) # Patch RAG to BoomRAG
    resp = client.post("/chat", json={"session_id": sid, "message": "hi"}) 
    assert resp.status_code == 500
    assert "fail load" in resp.json()["detail"].lower() 