import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv

from hie_rag.process import Process
from hie_rag.split import Split
from hie_rag.utils import Utils

load_dotenv()

split = Split(base_url=os.getenv('BASE_URL'))
utils = Utils(base_url=os.getenv('BASE_URL'))
process = Process(base_url=os.getenv('BASE_URL'))

with open("test.pdf", "rb") as uploaded_file:
    extracted_text = utils.extract_text(uploaded_file)

# Prepare the chunks to process
extracted_text = extracted_text[:1000]
result_split = split.split(extracted_text)
result_process = process.process_chunks(result_split)

# Write results to the text file
with open("test-process-result-new", "w", encoding="utf-8") as file:
    file.write("Processed Chunks:\n")
    file.write(str(result_process) + "\n")



print("Results written to a txt file.")
