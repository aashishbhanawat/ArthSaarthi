
import pdfplumber
import os

pdf_files = [
    "15- ltcg.pdf",
    "14- stcg.pdf",
    "65.exemptions-from-capital-gains.pdf"
]

for pdf_file in pdf_files:
    if os.path.exists(pdf_file):
        print(f"--- Extracting {pdf_file} ---")
        try:
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages[:5]:  # Read first 5 pages to get the gist/rates
                    text = page.extract_text()
                    if text:
                        print(text)
        except Exception as e:
            print(f"Error reading {pdf_file}: {e}")
        print("\n" + "="*50 + "\n")
    else:
        print(f"File not found: {pdf_file}")
