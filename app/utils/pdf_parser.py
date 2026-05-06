from fastapi import File, UploadFile
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




def extract_text(file_bytes: bytes, file: UploadFile = File(...)):
    filename = file.filename.lower()

    # PDF
    if filename.endswith(".pdf"):
        from app.utils.pdf_parser import extract_text_from_pdf
        return extract_text_from_pdf(file_bytes)

    # TXT
    elif filename.endswith(".txt"):
        return file_bytes.decode("utf-8")

    # DOCX
    elif filename.endswith(".docx"):
        import docx
        from io import BytesIO
        doc = docx.Document(BytesIO(file_bytes))
        return "\n".join([p.text for p in doc.paragraphs])

    else:
        raise ValueError("Unsupported file type")
    



