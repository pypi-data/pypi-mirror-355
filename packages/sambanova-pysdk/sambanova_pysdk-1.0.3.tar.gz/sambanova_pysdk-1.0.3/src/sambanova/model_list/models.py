import requests
from ..api_client import SambanovaAPIClient

def get_available_models(client: SambanovaAPIClient):
    """
    Fetches the list of available models and their status from SambaNova Cloud.
    Returns a list of dicts with model information.
    """
    response = requests.get(
        client.url("/v1/models"),
        headers=client.headers()
    )
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch models: {response.status_code} {response.text}")
    data = response.json().get("data", [])
    if data is None:
        data = []
    return data

def get_model_details(client: SambanovaAPIClient, model_id: str):
    """
    Fetches details for a specific model from SambaNova Cloud.
    Returns a dict with model information.
    """
    response = requests.get(
        client.url(f"/v1/models/{model_id}"),
        headers=client.headers()
    )
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch model details: {response.status_code} {response.text}")
    return response.json()
