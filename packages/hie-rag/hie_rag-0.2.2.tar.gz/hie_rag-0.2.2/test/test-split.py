import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv

from hie_rag.split import Split
from hie_rag.utils import Utils

load_dotenv()

split = Split(base_url=os.getenv("BASE_URL"))
utils = Utils(base_url=os.getenv("BASE_URL"))

with open("test.pdf", "rb") as uploaded_file:
    extracted_text = utils.extract_text(uploaded_file)

# Simplify the extracted text for testing
extracted_text = extracted_text[:1000]

# Split the extracted text
result_split = split.split(extracted_text, min_chunk_size=300, max_chunk_size=500)

# Write results to the text file
with open("test-split-result-new", "w", encoding="utf-8") as file:
    file.write("Splitted Text:\n")
    file.write(str(result_split) + "\n")
    file.write("Length of the Splitted Text:\n")
    file.write(str(len(result_split)) + "\n")

print("Results written to a txt file.")
