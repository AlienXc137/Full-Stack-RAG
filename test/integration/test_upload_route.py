import io
import pytest

# This test validates your happy path for document ingestion.
# Checks: Endpoint returns 200, Response JSON includes "indexed": true , "session_id" exists
# This confirms: File upload handling works, Ingestor (ChatIngestor) was called correctly, FastAPI’s request parsing behaves as expected
def test_upload_success_returns_session_and_indexed(client, clear_sessions, stub_ingestor, tmp_dirs): # Using tmp_dirs to isolate filesystem effects
    files = {"files": ("note.txt", io.BytesIO(b"hello world"), "text/plain")} # Single test file
    resp = client.post("/upload", files=files) # POST to /upload
    assert resp.status_code == 200 # Expect HTTP 200
    data = resp.json() # Parse JSON response
    assert data["indexed"] is True # Confirm indexed is True
    assert data["session_id"] # Confirm session_id exists

# This test checks your upload endpoint’s handling of no files being sent.
def test_upload_no_files_validation_error(client, clear_sessions, stub_ingestor):
    # Without files FastAPI validation will yield 422; send empty list to hit our 400
    resp = client.post("/upload", files=[]) 
    assert resp.status_code == 422

# This is a fault injection test — it simulates a failure during ingestion to ensure your exception handling logic works.
# Checks: Server returns 500, Error message contains "boom"
# Confirms: Your backend correctly catches DocumentPortalException, Converts it to HTTP 500 with JSON detail message, No raw stack traces leak to clients
def test_upload_ingestor_failure_returns_500(client, clear_sessions, monkeypatch, tmp_dirs):
    import multi_doc_chat.src.document_ingestion.data_ingestion as di
    import main

    class Boom: # Ingestor that always fails
        def __init__(self, *a, **k):  
            self.session_id = "sess_test" # Dummy session ID
        def built_retriver(self, *a, **k): # Dummy method
            from multi_doc_chat.exception.custom_exception import DocumentPortalException # Import custom exception
            raise DocumentPortalException("boom", None) # Always raise boom error

    monkeypatch.setattr(di, "ChatIngestor", Boom) # Patch ChatIngestor to Boom
    monkeypatch.setattr(main, "ChatIngestor", Boom) # Patch in main as well
    files = {"files": ("note.txt", io.BytesIO(b"hello world"), "text/plain")} # Test file
    resp = client.post("/upload", files=files) # POST to /upload
    assert resp.status_code == 500 
    assert "boom" in resp.json()["detail"].lower() # Confirm boom in error message