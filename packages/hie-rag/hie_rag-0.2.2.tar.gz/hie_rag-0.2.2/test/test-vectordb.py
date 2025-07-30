import os

from dotenv import load_dotenv
from hie_rag.app import Split
from hie_rag.process import Process
from hie_rag.utils import Utils
from hie_rag.vectordb import Vectordb

load_dotenv()

vectordb = Vectordb(path="test-vectordb", collection_name="index", api_key=os.getenv("OPENAI_API_KEY"))
split = Split(api_key=os.getenv("OPENAI_API_KEY"), min_chunk_size=200, max_chunk_size=500)
utils = Utils(api_key=os.getenv("OPENAI_API_KEY"))
process = Process(api_key=os.getenv("OPENAI_API_KEY"))

with open("test.pdf", "rb") as uploaded_file:
    extracted_text = utils.extract_text(uploaded_file)

# Prepare the chunks to process
extracted_text = extracted_text[:1000]
result_split = split.split(extracted_text)
result_process = process.process_chunks(result_split)


# Write results to the text file
with open("test-vectordb-result", "w", encoding="utf-8") as file:
    file.write("Save index:\n")
    file.write(str(vectordb.save_index(result_process)) + "\n")
    
    file.write("Query by text:\n")
    file.write(str(vectordb.query_by_text("臺中市政府")) + "\n")

    file.write("Query by embedding:\n")
    file.write(str(vectordb.query_by_embedding(utils.get_embedding("臺中市政府"))) + "\n")