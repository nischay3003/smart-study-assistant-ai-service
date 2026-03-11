import fitz

def extract_text_from_pdf(file_bytes:bytes)->str:
    """
    Extract text from a PDF file given its bytes.

    """
    text=""
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text+=page.get_text()
            
    return text