import pathlib
import pytest

from multi_doc_chat.src.document_chat.retrieval import ConversationalRAG
from multi_doc_chat.exception.custom_exception import DocumentPortalException

# Purpose of This Test:  This test ensures that ConversationalRAG correctly raises your custom exception DocumentPortalException when:
# The chain is not initialized before invoking .invoke() and The FAISS index directory path doesn’t exist when loading the retriever
# That’s essential to confirm your app gracefully handles missing dependencies instead of crashing.


def test_conversationalrag_error_handling(tmp_dirs, stub_model_loader):
    rag = ConversationalRAG(session_id="s1")
    # This creates an instance of your conversational RAG class.
    # It uses your stub_model_loader fixture (from conftest.py), which replaces real Google/Groq models with stubs — so there’s no API dependency.
    # The class is initialized with: A dummy session ID "s1", A fake LLM and embedding loader, No retriever yet (so .chain is None)
    with pytest.raises(DocumentPortalException): # Expecting your custom exception
        rag.invoke("hello")
        # Since .chain is None (retriever not built yet), this should trigger: raise DocumentPortalException("RAG chain not initialized. Call load_retriever_from_faiss() before invoke().", sys)
    with pytest.raises(DocumentPortalException):
        rag.load_retriever_from_faiss(index_path="faiss_index/does_not_exist")
        # Since that FAISS directory doesn’t exist, the internal check:  raise FileNotFoundError(f"FAISS index directory not found: {index_path}")