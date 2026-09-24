"""Extracts plain text from an uploaded resume file (PDF or DOCX)."""
import io
from pypdf import PdfReader
import docx


class UnsupportedFileType(Exception):
    pass


class UnreadableFile(Exception):
    pass


SUPPORTED_EXTENSIONS = (".pdf", ".docx")
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB


def extract_text_from_upload(filename, content_bytes):
    if not filename:
        raise UnsupportedFileType("No filename provided.")
    name = filename.lower()

    if len(content_bytes) > MAX_FILE_SIZE_BYTES:
        raise UnreadableFile("File is too large (max 5MB).")

    if name.endswith(".pdf"):
        try:
            reader = PdfReader(io.BytesIO(content_bytes))
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception as exc:
            raise UnreadableFile(f"Could not read that PDF: {exc}") from exc

    elif name.endswith(".docx"):
        try:
            document = docx.Document(io.BytesIO(content_bytes))
            text = "\n".join(p.text for p in document.paragraphs)
        except Exception as exc:
            raise UnreadableFile(f"Could not read that DOCX file: {exc}") from exc

    else:
        raise UnsupportedFileType(
            f"Unsupported file type for '{filename}'. Please upload a .pdf or .docx resume."
        )

    if not text.strip():
        raise UnreadableFile(
            "Couldn't find any text in that file — if it's a scanned/image-only PDF, "
            "try a version with selectable text instead."
        )

    return text
