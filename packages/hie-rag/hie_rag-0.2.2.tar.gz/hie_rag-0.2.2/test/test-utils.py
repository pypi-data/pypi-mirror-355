import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv

from hie_rag.utils import Utils

load_dotenv()

utils = Utils(base_url=os.getenv("BASE_URL"))

with open("test2.pdf", "rb") as uploaded_file:
    extracted_text = utils.extract_text(uploaded_file)

# Count tokens for the first 100 words
# result_count_tokens = utils.count_tokens(extracted_text[:100])
result_count_tokens = utils.count_tokens(extracted_text)
print(f"Token count: {result_count_tokens}")

# # Get embeddings for the text slices
# result_list_embeddings = utils.list_embeddings([
#     extracted_text[:100],
#     extracted_text[100:200],
#     extracted_text[200:300]
# ])

# # Get the embedding for the first 100 words
# result_get_embedding = utils.get_embedding(extracted_text[:100])

# # Find the index of least similar consecutive embeddings
# result_get_consecutive_least_similar = utils.get_consecutive_least_similar(result_list_embeddings)

# # Write results to the text file
# with open("test-utils-result-new", "w", encoding="utf-8") as file:
#     file.write("Extracted Text:\n")
#     file.write(extracted_text + "\n\n")
#     file.write("====================================\n\n")
    
#     file.write("Count of Tokens (First 100 words):\n")
#     file.write(str(result_count_tokens) + "\n\n")
#     file.write("====================================\n\n")
    
#     file.write("List of Embeddings:\n")
#     file.write(str(result_list_embeddings) + "\n\n")
#     file.write("====================================\n\n")
    
#     file.write("Embedding of First 100 words:\n")
#     file.write(str(result_get_embedding) + "\n\n")
#     file.write("====================================\n\n")
    
#     file.write("Index of Least Similar Consecutive Embeddings:\n")
#     file.write(str(result_get_consecutive_least_similar) + "\n")

# print("Results written to a txt file.")
