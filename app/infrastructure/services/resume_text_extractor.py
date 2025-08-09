import io
from typing import Tuple
from pypdf import PdfReader
import docx2txt

class ResumeTextExtractor:
    @staticmethod
    def extract_text(filename: str, content: bytes) -> str:
        if filename.lower().endswith(".pdf"):
            reader = PdfReader(io.BytesIO(content))
            parts = []
            for page in reader.pages:
                v = page.extract_text() or ""
                if v: parts.append(v)
            return "\n".join(parts)
        if filename.lower().endswith(".docx"):
            import tempfile, os
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as f:
                f.write(content)
                tmp = f.name
            try:
                return docx2txt.process(tmp) or ""
            finally:
                try: os.remove(tmp)
                except Exception: pass
        raise ValueError("Type de fichier non supporté (PDF/DOCX)")
