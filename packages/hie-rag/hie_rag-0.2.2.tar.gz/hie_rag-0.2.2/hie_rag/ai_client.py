import requests


class AiClient:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}

    def get_embedding(self, text: str, model="nomic-embed-text") -> list:
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": model,
            "prompt": text
        }
        response = requests.post(url, json=payload, headers=self.headers, timeout=60)
        response.raise_for_status()
        data = response.json()

        # Extract embedding, adapt if your API response structure differs
        embedding = data.get("embedding") or (data.get("data") and data["data"][0].get("embedding"))
        if embedding is None:
            raise ValueError("Embedding not found in Ollama response")
        return embedding

    def list_embeddings(self, texts: list, model="nomic-embed-text") -> list:
        return [self.get_embedding(text, model=model) for text in texts]