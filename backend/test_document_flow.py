#!/usr/bin/env python
"""Test script to verify document processing and chat integration."""

import tempfile
from pathlib import Path

from app.core.document_processor import DocumentProcessor


def test_document_processor():
    """Test document extraction from different file types."""

    # Create a temporary text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document.\nIt contains multiple lines.\nFor testing purposes.")
        txt_path = f.name

    try:
        # Test TXT extraction
        print("Testing TXT extraction...")
        result = DocumentProcessor.extract_text(txt_path)
        assert result["content"] != ""
        assert result["error"] is None
        assert result["word_count"] > 0
        print(f"✅ TXT: Extracted {result['word_count']} words")

        # Test LLM preparation
        print("\nTesting LLM preparation...")
        prepared = DocumentProcessor.prepare_for_llm(result["content"], max_length=100)
        assert len(prepared) <= 100 + 50  # Allow some buffer for truncation message
        print(f"✅ LLM prep: {len(prepared)} characters")

        # Test document context formatting
        print("\nTesting document context formatting...")
        docs = [
            {"filename": "test1.txt", "content": "Document 1 content"},
            {"filename": "test2.txt", "content": "Document 2 content"}
        ]
        context = DocumentProcessor.format_document_context(docs)
        assert "Document 1: test1.txt" in context
        assert "Document 2: test2.txt" in context
        print(f"✅ Context formatted: {len(context)} characters")

        # Test unsupported format
        print("\nTesting unsupported format...")
        result = DocumentProcessor.extract_text("fake.xyz")
        assert result["error"] is not None
        print(f"✅ Unsupported format handled: {result['error']}")

        print("\n🎉 All document processor tests passed!")

    finally:
        # Clean up
        Path(txt_path).unlink(missing_ok=True)


if __name__ == "__main__":
    test_document_processor()