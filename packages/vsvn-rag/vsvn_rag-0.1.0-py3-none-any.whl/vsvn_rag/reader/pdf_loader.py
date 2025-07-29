from reader.base_loader import BaseLoader

class PDFLoader(BaseLoader):
    def load(self, file_path: str) -> str:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n\n"
            return text.strip()
        except Exception as e:
            raise RuntimeError(f"Error loading PDF file: {e}")
