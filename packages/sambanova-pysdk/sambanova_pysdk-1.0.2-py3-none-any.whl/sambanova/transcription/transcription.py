import requests
from ..api_client import SambanovaAPIClient

class Transcription:
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
            client.url("v1/audio/transcriptions"),
            headers=client.headers(),
            json=payload
        )
        content_type = ""
        if response.headers:
            content_type = response.headers.get("Content-Type", "")
        if content_type.lower().startswith("application/json"):
            return response.json()
        else:
            print("Warning: Response is not JSON. Raw response:", response.text)
            return response.text

    @staticmethod
    def transcribe_audio_file(client: SambanovaAPIClient, model: str, audio_file_path: str, language: str = "english", response_format: str = "json", stream: bool = True):
        """
        Transcription of an an audio file using the /v1/audio/transcriptions endpoint.
        """
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
            client.url("/v1/audio/transcriptions"),
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
            print("Warning: Response is not JSON. plain text response")
            return response.text
