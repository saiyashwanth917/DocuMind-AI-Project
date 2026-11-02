from docx import Document

def extract_docx(path):
    doc = Document(path)
    output = []
    for n, paragraph in enumerate(doc.paragraphs, start=1):
        text = paragraph.text.strip()
        if text:
            output.append({"source": f"Paragraph {n}", "text": text})
    for table_no, table in enumerate(doc.tables, start=1):
        for row_no, row in enumerate(table.rows, start=1):
            text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if text:
                output.append({"source": f"Table {table_no}, row {row_no}", "text": text})
    return output
