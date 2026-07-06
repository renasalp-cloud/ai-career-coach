from pypdf import PdfReader


def clean_text(text: str) -> str:
    """
    Cleans extracted PDF text while preserving line breaks.
    """
    lines = []

    for line in text.splitlines():
        cleaned_line = " ".join(line.split())

        if cleaned_line:
            lines.append(cleaned_line)

    return "\n".join(lines)


def extract_text(pdf_path: str) -> str:
    """
    Reads a PDF file and returns cleaned extracted text.
    """
    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return clean_text(text)