import os

from dotenv import load_dotenv
from hie_rag.app import Split
from hie_rag.utils import Utils

load_dotenv()

split = Split(api_key=os.getenv("OPENAI_API_KEY"))
utils = Utils(api_key=os.getenv("OPENAI_API_KEY"))

with open("test.pdf", "rb") as uploaded_file:
    extracted_text = utils.extract_text(uploaded_file)

final_chunk_list = split.split(extracted_text)

print(final_chunk_list)