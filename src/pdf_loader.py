import fitz

def extract_pdf(path):
    output = []
    with fitz.open(path) as doc:
        for page_no, page in enumerate(doc, start=1):
            output.append({"source": f"Page {page_no}", "text": page.get_text("text")})
    return output
