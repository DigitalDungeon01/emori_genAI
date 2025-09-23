import pandas as pd
from typing import Dict, List
from PyPDF2 import PdfReader


class data_processing:
    def __init__(self):
        pass

    # Clean text helper
    def _clean_text(self, text: str) -> str:
        return " ".join(text.split()).strip()

    # Process CSV file
    def _process_csv(self, file_path: str, title: str, tags: List[str], category: List[str]) -> List[Dict]:
        df = pd.read_csv(file_path)
        results = []

        for idx, row in df.iterrows():
            q = self._clean_text(str(row.iloc[0]))
            a = self._clean_text(str(row.iloc[1]))
            text = f"{q} {a}"

            results.append(
                {
                    "text": text,
                    "metadata": {
                        "title": title,
                        "tags": tags,
                        "category": category,
                        "filename": file_path.split("/")[-1]
                    }
                }
            )

        print(f"CSV processed: {len(results)} rows")
        return results

    # Process PDF file
    def _process_pdf(self, file_path: str, title: str, tags: List[str], category: List[str]) -> List[Dict]:
        reader = PdfReader(file_path)
        results = []

        for page_num, page in enumerate(reader.pages, start=1):
            text = self._clean_text(page.extract_text() or "")
            if not text:
                continue

            results.append(
                {
                    "text": text,
                    "metadata": {
                        "title": title,
                        "tags": tags,
                        "category": category,
                        "filename": file_path.split("/")[-1]
                    }
                }
            )

        print(f"PDF processed: {len(results)} pages")
        return results

    # Process document (CSV or PDF)
    def process_document(
        self,
        file_path: str,
        category: List[str],
        tags: List[str],
        title: str,
    ) -> List[Dict]:
        if not file_path or not title:
            raise ValueError("file_path and title are required")

        print(f"Processing: {file_path.split('/')[-1]}")

        if file_path.endswith(".csv"):
            content = self._process_csv(file_path, title, tags, category)
        elif file_path.endswith(".pdf"):
            content = self._process_pdf(file_path, title, tags, category)
        else:
            raise ValueError("Unsupported file format. Only CSV and PDF are allowed.")

        print(f"Done: {len(content)} items")
        return content