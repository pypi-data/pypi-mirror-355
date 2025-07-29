import json
import requests
from ..api_client import SambanovaAPIClient
from ..utils import parse_sse_stream

class Embeddings:
    @staticmethod
    def create(client: SambanovaAPIClient, messages: list, model: str, **kwargs):
        payload =   {
                "input": messages,
                "model": model,
            } 

        print("\n--- Making API Request ---")
        print("POST", "/v1/embeddings")
        print("Headers:", client.headers())
        print("Payload:", json.dumps(payload, indent=2))
        print("---\n")

        response = requests.post(
            client.url("/v1/embeddings"),
            headers=client.headers(),
            data=json.dumps(payload) 
        )
        # Raise an error for bad HTTP status codes
        response.raise_for_status()

        # Check if the response contains JSON data
        if response.headers.get("Content-Type", "").startswith("application/json"):
            return response.json()
        else:
            print("Warning: Response is not JSON. Raw response:", response.text)
            return {"error": "Response is not JSON", "raw_response": response.text}
