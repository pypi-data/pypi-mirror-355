from hie_rag.process import Process
from hie_rag.split import Split
from hie_rag.tree_index import TreeIndex
from hie_rag.utils import Utils
from hie_rag.vectordb import Vectordb


class HieRag:
    def __init__(self, base_url, path="./db", collection_name="db_collection"):
        self.split = Split(base_url=base_url)
        self.utils = Utils(base_url=base_url)
        self.tree_index = TreeIndex(base_url=base_url)
        self.process = Process(base_url=base_url)
        self.vector_db = Vectordb(path=path, base_url=base_url, collection_name=collection_name)
    
    def process_and_save_index_stream(self, file_name: str, uploaded_file: bytes, min_chunk_size, max_chunk_size):
        yield {"status": "🔍 Extracting text..."}
        print(f"Extracting text from {file_name}")
        extracted_text = self.utils.extract_text(uploaded_file)

        yield {"status": "✂️ Splitting into chunks..."}
        print(f"Splitting text into chunks with min size {min_chunk_size} and max size {max_chunk_size}")
        result_split = self.split.split(extracted_text, min_chunk_size=min_chunk_size, max_chunk_size=max_chunk_size)

        yield {"status": "🧠 Processing chunks..."}
        print(f"Processing {len(result_split)} chunks")
        result_process = self.process.process_chunks(result_split)

        yield {"status": "🌲 Building tree index..."}
        print(f"Building tree index with {len(result_process)} chunks")
        tree_index = self.tree_index.tree_index(file_name = file_name, chunk_metadata=result_process)

        yield {"status": "💾 Saving to vector DB..."}
        print(f"Saving tree index with {len(tree_index.get('chunks', []))} chunks to vector DB")
        save_result = self.vector_db.save_index(tree_index)

        file_id = save_result.get("file_id", "unknown")

        yield {
            "status": "✅ Done",
            "file_id": file_id,
            "summary_count": len(tree_index.get("summaries", [])),
            "chunk_count": len(tree_index.get("chunks", [])),
        }

    def get_summary(self, file_id):
        return self.vector_db.get_summary(file_id)

    def list_summaries(self):
        return self.vector_db.list_summaries()
    
    def list_chunks(self, file_id):
        return self.vector_db.list_chunks(file_id)
    
    def delete_index(self, file_id):
        return self.vector_db.delete_index(file_id)
    
    def query_summaries_by_text(self, query_text: str, n_results=5):
        return self.vector_db.query_summaries_by_text(query_text, n_results=n_results)
    
    def query_chunks_by_text(self, query_text: str, file_id: str, n_results=5):
        return self.vector_db.query_chunks_by_text(query_text, file_id=file_id, n_results=n_results)