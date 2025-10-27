from pypdf import PdfReader

def generate_pdf_summary_prompt(pdf_file, language):

    pdf_reader = PdfReader(pdf_file)

    full_pdf_text = ""

    # Iterate through all the PDF pages and remove all the new 
    # line characters to save tokens
    for i in range(len(pdf_reader.pages)):
        full_pdf_text += ' '.join(pdf_reader.pages[i].extract_text().split())

    summary_prompt = f'''
You are a scientific expert that can communicate simply, clearly, and concisely.  Provide a detailed summary of the following text in layman's terms in {language}:
{full_pdf_text}
'''

    return summary_prompt

