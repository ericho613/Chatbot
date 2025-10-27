from pypdf import PdfReader

def generate_pdf_citation_prompt(pdf_file, citation_style):

    pdf_reader = PdfReader(pdf_file)

    pdf_text = ""

    # Only read the first PDF page and remove all the new 
    # line characters to save tokens
    for i in range(1):
        pdf_text += ' '.join(pdf_reader.pages[i].extract_text().split())

    citation_prompt = f'''
You are an expert at creating academic citations.  Create a {citation_style} citation for the following text, and only output the citation:
{pdf_text}
'''

    return citation_prompt

