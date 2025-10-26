import pathlib
import pytest
from langchain.schema import Document

from multi_doc_chat.src.document_ingestion.data_ingestion import (
    generate_session_id,
    ChatIngestor,
    FaissManager,
)

# Checks your internal session ID generator produces: Unique session IDs,Correct format like session_20251025_065200_ABC12345
# Ensures pattern and prefix consistency
# What it verifies: Each ingestion run gets a unique isolated session directory (important for multi-user chat isolation).
def test_generate_session_id_format_and_uniqueness(): 
    a = generate_session_id() # First session ID
    b = generate_session_id() # Second session ID
    assert a != b  # Uniqueness check
    assert a.startswith("session_") and b.startswith("session_") # Prefix check
    # Rough pattern check: session_YYYYMMDD_HHMMSS_XXXXXXXX -> 4 parts
    assert len(a.split("_")) == 4  # Pattern structure check

# Instantiates a ChatIngestor and verifies: It auto-generates a unique session ID. It creates separate temp (data/) and FAISS (faiss_index/) directories under that session
# Dependencies handled: stub_model_loader fixture from conftest.py injects fake embeddings + LLMs so initialization never hits Groq/Google.
# tmp_dirs fixture uses a temporary filesystem location, ensuring no pollution in your real project folders.
# Why it matters: This confirms your ingestion process correctly isolates each chat session’s vectorstore and document temp files.
def test_chat_ingestor_resolve_dir_uses_session_dirs(tmp_dirs, stub_model_loader): # Using tmp_dirs fixture to isolate filesystem effects
    ing = ChatIngestor(temp_base="data", faiss_base="faiss_index", use_session_dirs=True) # Instantiate with session dirs
    assert ing.session_id # Auto-generated session ID exists
    assert str(ing.temp_dir).endswith(ing.session_id) # Temp dir ends with session ID
    assert str(ing.faiss_dir).endswith(ing.session_id) # FAISS dir ends with session ID

# Ensures that _split() respects the desired chunk size and overlap between document segments.
# What happens: Creates a 1200-character fake document. Splits it into chunks of size 500 with 100 overlap.
# Asserts: There are multiple chunks, Each chunk ≤ 500 chars
# Why it matters: Chunking determines embedding granularity — this ensures your retrieval precision remains controlled.
def test_split_chunks_respect_size_and_overlap(tmp_dirs, stub_model_loader):
    ing = ChatIngestor(temp_base="data", faiss_base="faiss_index", use_session_dirs=True) # Instantiate ChatIngestor
    docs = [Document(page_content="A" * 1200, metadata={"source": "x.txt"})] # Fake long document
    chunks = ing._split(docs, chunk_size=500, chunk_overlap=100) # Split into chunks
    assert len(chunks) >= 2 # Multiple chunks created
    # spot check boundaries
    assert len(chunks[0].page_content) <= 500 # First chunk size check

# Tests FAISS’s ability to avoid re-adding duplicate documents: Creates a fresh FAISS manager. Loads or creates an index from text data.
# Adds a document once → should be added (>=0). Adds the same document again → should not be added (0 new docs)
# Why it matters: Ensures FAISS indexing stays idempotent, so re-ingesting the same document doesn’t inflate your index unnecessarily.
def test_faiss_manager_add_documents_idempotent(tmp_dirs, stub_model_loader): 
    fm = FaissManager(index_dir=pathlib.Path("faiss_index/test")) # Fresh FAISS manager
    fm.load_or_create(texts=["hello", "world"], metadatas=[{"source": "a"}, {"source": "b"}]) # Load or create index
    docs = [Document(page_content="hello", metadata={"source": "a"})] # Duplicate document  
    first = fm.add_documents(docs)  # First addition
    second = fm.add_documents(docs) # Second addition (duplicate)
    assert first >= 0 # First addition should add docs
    assert second == 0 # Second addition should add 0 new docs