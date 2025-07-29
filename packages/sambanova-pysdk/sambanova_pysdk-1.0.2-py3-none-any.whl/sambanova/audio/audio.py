import requests
from ..api_client import SambanovaAPIClient

class Audio:
    @staticmethod
    def create(client: SambanovaAPIClient, messages: list, model: str, **kwargs):

        messages = messages

        payload = {
            "messages": messages,
            "model": model,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "temperature": kwargs.get("temperature", 0.01),
            "stream": kwargs.get("stream", True)
        }

        response = requests.post(
            client.url("/v1/audio/reasoning"),
            headers=client.headers(),
            json=payload
        )

        #Content-Type check (case-insensitive, handles charset, handles None)
        content_type = ""
        if response.headers:
            content_type = response.headers.get("Content-Type", "")
        if content_type.lower().startswith("application/json"):
            return response.json()
        else:
            print("Warning: Response is not JSON. Raw response:", response.text)
            return response.text
