#from sambanova.model_list.models import get_available_models


class SambanovaAPIClient: 
    # A client for interacting with the SambaNova AI API.
    def __init__(self, api_key: str, contentType: str="application/json", use_bearer_auth: bool = False):
        self.api_key = api_key
        self.base_url = "https://api.sambanova.ai/"
        self.use_bearer_auth = use_bearer_auth
        self.contentType = contentType

    def headers(self):
        headers = { 
            "Accept": "application/json",
            "Content-Type": self.contentType
        }

        headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    def url(self, path: str):
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
