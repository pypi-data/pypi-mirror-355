import requests
from ..api_client import SambanovaAPIClient

class Image:
    @staticmethod
    def create(client: SambanovaAPIClient, messages: list, model: str, **kwargs):

        payload = {
            "messages": messages,
            "model": model,
            "max_tokens": kwargs.get("max_tokens", 300),
            "temperature": kwargs.get("temperature", 0.7),
            "stream": kwargs.get("stream", True)
        }

        response = requests.post(
            client.url("/v1/chat/completions"),
            headers=client.headers(),
            json=payload
        )

        response.raise_for_status()  

        # Check if the response contains JSON data
        if response.headers.get("Content-Type", "").startswith("application/json"):
            return response.json()
        else:
            print("Warning: Response is not JSON. Raw response:\n", response.text)
            return response.text
