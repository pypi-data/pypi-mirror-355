import uuid

import chromadb
import numpy as np

from .utils import Utils


class Vectordb():
    def __init__(self, path, base_url, collection_name):
        self.client = chromadb.PersistentClient(path = path)
        self.utils = Utils(base_url=base_url)
        self.collection = self.client.get_or_create_collection(collection_name)

    def _convert_numpy(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, list):
            return [self._convert_numpy(v) for v in obj]
        elif isinstance(obj, dict):
            return {k: self._convert_numpy(v) for k, v in obj.items()}
        return obj

    def save_index(self, tree_index):
        try:
            # Generate a unique file_id if not provided
            file_id = str(uuid.uuid4())

            # Prepare parent (summary) entry
            parent_entry = {
                "id": f"summary_{file_id}",
                "embedding": tree_index["embeddings"],
                "metadata": {
                    "type": "summary",
                    "file_name": tree_index["file_name"],
                    "file_id": file_id,
                    "summary": tree_index["summary"],
                    "keywords": "\n".join(tree_index.get("keywords", [])),
                }
            }

            # Prepare child (chunk) entries
            chunk_entries = [
                {
                    "id": f"chunk_{file_id}_{chunk['id']}",
                    "embedding": chunk["embeddings"],
                    "metadata": {
                        "type": "chunk",
                        "file_id": file_id,
                        "summary": chunk["summary"],
                        "keywords": "\n".join(chunk.get("keywords", [])),
                        "original_chunk": chunk.get("original_chunk", "")
                    }
                }
                for chunk in tree_index.get("chunks", [])
            ]

            all_entries = [parent_entry] + chunk_entries

            self.collection.add(
                ids=[entry["id"] for entry in all_entries],
                embeddings=[entry["embedding"] for entry in all_entries],
                metadatas=[entry["metadata"] for entry in all_entries],
            )

            return {
                "message": "Index saved successfully",
                "file_id": file_id,
            }

        except Exception as e:
            print(f"[save_index error] {e}")
            return {
                "message": "Failed to save index",
                "error": str(e),
            }
        
    def get_summary(self, file_id):
        """
        get the summary in the collection.
        """
        try:
            raw_result = self.collection.get(
                where={"$and": [{"type": "summary"}, {"file_id": file_id}]},
                # include=["distances", "metadatas"]
            )
            
            ids = raw_result.get("ids", [])
            metadatas = raw_result.get("metadatas", [])

            result_length = min(len(ids), len(metadatas))

            flat_result = [
                {
                    "id": self._convert_numpy(ids[i]),
                    "metadata": self._convert_numpy(metadatas[i])
                }
                for i in range(result_length)
            ]

            return {
                "summary": flat_result,
            }
        except Exception as e:
            print(f"[list_index error]: {e}")
            return {
                "message": "Failed to list index",
                "error": str(e),
            }

    def list_summaries(self):
        """
        List all the summaries in the collection.
        """
        try:
            raw_result = self.collection.get(
                where={"type": "summary"},
                # include=["distances", "metadatas"]
            )

            # print(raw_result)
            
            ids = raw_result.get("ids", [])
            metadatas = raw_result.get("metadatas", [])

            result_length = min(len(ids), len(metadatas))

            flat_result = [
                {
                    "id": self._convert_numpy(ids[i]),
                    "metadata": self._convert_numpy(metadatas[i])
                }
                for i in range(result_length)
            ]

            return {
                "summaries": flat_result,
            }
        except Exception as e:
            print(f"[list_index error]: {e}")
            return {
                "message": "Failed to list index",
                "error": str(e),
            }
        
    def list_chunks(self, file_id):
        """
        List all the chunks in the collection.
        """

        try:
            raw_result = self.collection.get(
                where={"$and": [{"type": "chunk"}, {"file_id": file_id}]},
            )

            ids = raw_result.get("ids", [])
            metadatas = raw_result.get("metadatas", [])

            result_length = min(len(ids), len(metadatas))

            flat_result = [
                {
                    "id": self._convert_numpy(ids[i]),
                    "metadata": self._convert_numpy(metadatas[i])
                }
                for i in range(result_length)
            ]

            return {
                "chunks": flat_result,
            }
        except Exception as e:
            print(f"[list_index error]: {e}")
            return {
                "message": "Failed to list index",
                "error": str(e),
            }        



    def delete_index(self, file_id):
        """
        Delete all the index of a specific file_id, including its summary and chunks.
        """
        try:
            self.collection.delete(
                where={"file_id": file_id}
            )
            print(f"Deleted summary with file_id: {file_id}")
            return{
                "message": "Index deleted successfully",
                "file_id": file_id,
            }

        except Exception as e:
            print(f"[delete_index error]: {e}")
            return {
                "message": "Failed to delete index",
                "error": str(e),
            }


    def query_summaries_by_text(self, query_text, n_results=5) -> list:
        """
        Query summaries based on the query text.
        Args:
        - `query_text`: The text to query against.
        - `n_results`: Number of results to return.
        """
        try:  
            query_embedding = self.utils.get_embedding(query_text)

            raw_result = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where={"type": "summary"},
                include=["distances", "metadatas"]
            )

            ids = raw_result.get("ids", [[]])[0] if raw_result.get("ids") else []
            distances = raw_result.get("distances", [[]])[0] if raw_result.get("distances") else []
            metadatas = raw_result.get("metadatas", [[]])[0] if raw_result.get("metadatas") else []

            result_length = min(len(ids), len(distances), len(metadatas))

            flat_result = [
                {
                    "id": self._convert_numpy(ids[i]),
                    "distance": self._convert_numpy(distances[i]),
                    "metadata": self._convert_numpy(metadatas[i])
                }
                for i in range(result_length)
            ]

            return {
                "summaries": flat_result,
            }
        except Exception as e:
            print(f"[query_summaries_by_text error] {e}")
            return {
                "message": "Failed to query summaries",
                "error": str(e),
            }

    def query_chunks_by_text(self, query_text, file_id, n_results=5) -> list:
        """
        Query chunks that belong to a specific file_id, based on query text.
        Args:
        - `query_text`: The text to query against.
        - `file_id`: The ID of the file to filter chunks by.
        - `n_results`: Number of results to return.
        """
        try:
            query_embedding = self.utils.get_embedding(query_text)

            # Get the summary of the file_id
            summary_raw_result = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=1,
                where={"$and": [{"type": "summary"}, {"file_id": file_id}]},
                include=["distances", "metadatas"]
            )
            
            summary_ids = summary_raw_result.get("ids", [[]])[0] if summary_raw_result.get("ids") else []
            summary_distances = summary_raw_result.get("distances", [[]])[0] if summary_raw_result.get("distances") else []
            summary_metadatas = summary_raw_result.get("metadatas", [[]])[0] if summary_raw_result.get("metadatas") else []

            summary_result_length = min(len(summary_ids), len(summary_distances), len(summary_metadatas))

            summary_flat_result = [
                {
                    "id": self._convert_numpy(summary_ids[i]),
                    "distance": self._convert_numpy(summary_distances[i]),
                    "metadata": self._convert_numpy(summary_metadatas[i])
                }
                for i in range(summary_result_length)
            ]

            print("The summary_flat_result is querying...")


            # Get the relevant chunks of the file_id
            raw_result = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where={"$and": [{"type": "chunk"}, {"file_id": file_id}]},
                include=["distances", "metadatas"]
            )

            ids = raw_result.get("ids", [[]])[0] if raw_result.get("ids") else []
            distances = raw_result.get("distances", [[]])[0] if raw_result.get("distances") else []
            metadatas = raw_result.get("metadatas", [[]])[0] if raw_result.get("metadatas") else []

            flat_result_length = min(len(ids), len(distances), len(metadatas))

            flat_result = [
                {
                    "id": self._convert_numpy(ids[i]),
                    "distance": self._convert_numpy(distances[i]),
                    "metadata": self._convert_numpy(metadatas[i])
                }
                for i in range(flat_result_length)
            ]

            print("The flat_result is querying...")

            # Return the summary and most relevant chunks of the file_id
            return {
                "file_id": file_id,
                "summary": summary_flat_result,
                "chunks": flat_result
            }
        except Exception as e:
            print(f"[query_chunks_by_text error] {e}")
            return {
                "message": "Failed to query chunks",
                "error": str(e),
            }
    