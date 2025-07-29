import json
import requests

from sambanova.model_list.models import get_model_details
from ..api_client import SambanovaAPIClient
from ..utils import parse_sse_stream

class ChatCompletion:
    @staticmethod
    def create(client: SambanovaAPIClient, messages: list, model: str, **kwargs):

        # model = get_model_details(client, model)
        # if not model:
        #     raise ValueError(f"Model '{model}' is not available or invalid.")
        # max_tokens = kwargs.get("max_tokens", 2048)
        # model_max_tokens = model.get("context_length")
        payload = {            
                "messages": messages,
                "model": model,
                "stream": True,
                "stream_options": {"include_usage": True},
                "stop": ["<|eot_id|>"],
                "process_prompt": True,
                "do_sample": False,
                "max_tokens": kwargs.get("max_tokens", 2048)
            }

        response = requests.post(
            client.url("/v1/chat/completions"),
            headers=client.headers(),
            data=json.dumps(payload),
            stream=True
        )
        response.raise_for_status()

        for chunk in parse_sse_stream(response):
            if chunk == "[DONE]":
                break
            yield json.loads(chunk)
