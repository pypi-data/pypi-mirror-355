from typing import Dict, List

from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from pydantic import Field
from typing_extensions import TypedDict

from .utils import Utils


class Process:
    def __init__(self, base_url=None, model="llama3.2:latest"):
        self.client = ChatOllama(model=model)
        self.utils = Utils(base_url=base_url)

    def _generate_metadata(self, chunk: str) -> Dict:
        """Generate metadata for a chunk using LangChain"""
        prompt = PromptTemplate(
            template="""
            Based on the chunk of text, please generate a summary and a list of key words to represent the main points of the text.

            NOTE: 
            1. 請輸出繁體中文
            2. The summary should be concise and capture the main points of the text.
            3. The summary should be around 5-8 sentences long.

            Chunk:
            {chunk}
            """,
            input_variables=["chunk"],
        )

        class MetaData(TypedDict):
            summary: str = Field(
                description="The summary of the chunk.",
            )
            keywords: List[str] = Field(
                description="A list of keywords that represent the main points of the chunk.",
            )

        llm_with_tool = self.client.with_structured_output(MetaData)
        chain = prompt | llm_with_tool
        
        return chain.invoke({"chunk": chunk})
        
    def process_chunks(self, chunks: List[str]) -> Dict:
        """
        Process a list of text chunks and generate metadata and embeddings for each.
        Returns data in specified JSON format.
        """
        
        # Process all chunks
        processed_chunks = {
            "chunks": []
        }
        
        for idx, chunk in enumerate(chunks):
            # Generate metadata
            metadata = self._generate_metadata(chunk)
            
            # Get embedding
            embeddings = self.utils.get_embedding(chunk)
            
            # Create chunk entry
            chunk_data = {
                "id": idx,
                "summary": metadata["summary"],
                "keywords": metadata["keywords"],
                "embeddings": embeddings,
                "original_chunk": chunk
            }
            
            processed_chunks["chunks"].append(chunk_data)
        
        return processed_chunks