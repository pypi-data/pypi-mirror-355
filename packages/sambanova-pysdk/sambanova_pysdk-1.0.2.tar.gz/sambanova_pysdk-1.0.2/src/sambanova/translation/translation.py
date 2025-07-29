import requests
from ..api_client import SambanovaAPIClient

class Translation:
    @staticmethod 
    def create(client: SambanovaAPIClient, audio_file_path: str, model: str, language: str = "english", response_format: str = "json", stream: bool = True):
        headers = client.headers()
        # Remove Content-Type if present, requests will set it for multipart
        headers.pop("Content-Type", None)
        files = {"file": open(audio_file_path, "rb")}
        data = {
            "model": model,
            "language": language,
            "response_format": response_format,
            "stream": str(stream).lower(),
        }
        response = requests.post(
            client.url("/v1/audio/translations"),
            headers=headers,
            files=files,
            data=data,
        )
        files["file"].close()
        content_type = ""
        if response.headers:
            content_type = response.headers.get("Content-Type", "")
        if content_type.lower().startswith("application/json"):
            return response.json()
        else:
            return response.text
