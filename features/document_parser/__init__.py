"""
Document Parsing Feature for Charlie AI using Docling.

Integrates the Docling library (docling-main/) to convert documents
(PDF, DOCX, PPTX, XLSX, HTML, images, EPUB, etc.) into structured
Markdown or plain text suitable for LLM consumption and RAG pipelines.
"""

from features.document_parser.docling_adapter import DoclingAdapter

__all__ = ["DoclingAdapter"]
