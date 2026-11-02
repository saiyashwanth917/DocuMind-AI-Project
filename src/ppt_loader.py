from pptx import Presentation

def extract_pptx(path):
    presentation = Presentation(path)
    output = []
    for slide_no, slide in enumerate(presentation.slides, start=1):
        parts = []
        for shape in slide.shapes:
            if getattr(shape, "has_text_frame", False) and shape.text.strip():
                parts.append(shape.text.strip())
            if getattr(shape, "has_table", False):
                for row in shape.table.rows:
                    parts.append(" | ".join(cell.text.strip() for cell in row.cells))
        output.append({"source": f"Slide {slide_no}", "text": "\n".join(parts)})
    return output
