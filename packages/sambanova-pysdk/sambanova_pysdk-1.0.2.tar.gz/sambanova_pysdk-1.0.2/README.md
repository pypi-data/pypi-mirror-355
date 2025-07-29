# Sambanova Python SDK

A Python SDK for interacting with Sambanova's REST APIs, including chat, image, audio, transcription, translation, and embeddings.

## Installation

```bash
pip install sambanova-pysdk 
```

## About Sambanova

Sambanova provides advanced AI infrastructure and models for generative AI, vision, audio, and language tasks. The Sambanova SDK enables seamless integration with Sambanova's REST APIs, allowing you to build, deploy, and scale AI-powered applications efficiently.

With Sambanova, you can:

- Access high-performance AI inference and training
- Use state-of-the-art models for chat, vision, audio, and more
- Scale your AI workloads with robust cloud and on-premise solutions

## Documentation

The REST API documentation can be found on the [Sambanova documentation portal](https://docs.sambanova.ai). The full API of this library can be found in `api.md`.

## Usage Examples

### Chat Completion

```python
from src.sambanova.api_client import SambanovaAPIClient
from src.sambanova.chat import ChatCompletion

client = SambanovaAPIClient("your_api_key")
messages = [{"role": "user", "content": "Hello, how are you?"}]
stream = ChatCompletion.create(
    client,
    messages=messages,
    model="Llama-4-Maverick-17B-128E-Instruct"
)
response = ""
for chunk in stream:
    choices = chunk.get("choices", [])
    if not choices:
        continue
    delta = choices[0].get("delta", {})
    content = delta.get("content", "")
    response += content
print("Assistant:", response)
```

### Image Completion

```python
from src.sambanova.api_client import SambanovaAPIClient
from src.sambanova.image import Image
import base64

client = SambanovaAPIClient("your_api_key")
with open("path/to/image.jpg", "rb") as image_file:
    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe this image."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
    }
]
response = Image.create(
    client,
    messages=messages,
    model="Llama-4-Maverick-17B-128E-Instruct",
    max_tokens=300,
    temperature=0.7,
    stream=False
)
print(response)
```

### Embeddings

```python
from src.sambanova.api_client import SambanovaAPIClient
from src.sambanova.embeddings import Embeddings

client = SambanovaAPIClient("your_api_key")
messages = [
    "Our solar system orbits the Milky Way galaxy at about 515,000 mph",
    "Jupiter's Great Red Spot is a storm that has been raging for at least 350 years."
]
response = Embeddings.create(
    client,
    messages=messages,
    model="E5-Mistral-7B-Instruct"
)
print(response)
```

### Audio Reasoning

```python
from src.sambanova.api_client import SambanovaAPIClient
from src.sambanova.audio import Audio
import base64

client = SambanovaAPIClient("your_api_key")
with open("path/to/audio.mp3", "rb") as audio_file:
    base64_audio = base64.b64encode(audio_file.read()).decode('utf-8')
messages = [
    {"role": "assistant", "content": "You are a helpful assistant."},
    {"role": "user", "content": [
        {"type": "audio_content", "audio_content": {"content": f"data:audio/mp3;base64,{base64_audio}"}}
    ]},
    {"role": "user", "content": "What is in this audio?"}
]
response = Audio.create(
    client,
    messages=messages,
    model="Qwen2-Audio-7B-Instruct",
    max_tokens=200,
)
print(response)
```

### Transcription

```python
from src.sambanova.api_client import SambanovaAPIClient
from src.sambanova.transcription import Transcription

client = SambanovaAPIClient("your_api_key")
audio_file_path = "path/to/audio.mp3"
response = Transcription.transcribe_audio_file(
    client,
    model="Whisper-Large-v3",
    audio_file_path=audio_file_path,
    language="english",
    response_format="text"
)
print(response)
```

## API Key

Get an API Key from your Sambanova account and add it to your environment variables:

```bash
export SN_API_KEY="your-api-key-here"
```

You can also use [python-dotenv](https://pypi.org/project/python-dotenv/) to add `SN_API_KEY="your-api-key-here"` to your `.env` file.

or for generating a reponse in the terminal: 

```bash
export SN_API_KEY=your-api-key-here 
PYTHONPATH=. python3 "your file relative path"
```

## Advanced Usage

### Streaming Responses

The SDK supports streaming responses for chat and other endpoints. When streaming, usage and timing information will only be included in the final chunk.

```python
stream = ChatCompletion.create(
    client,
    messages=messages,
    model="Llama-4-Maverick-17B-128E-Instruct",
    stream=True,
)
for chunk in stream:
    print(chunk.get("choices", [{}])[0].get("delta", {}).get("content", ""), end="")
```

### Error Handling

When the SDK is unable to connect to the API (e.g., network issues or timeouts), a `SambanovaAPIConnectionError` is raised.

When the API returns a non-success status code (4xx or 5xx), a `SambanovaAPIStatusError` is raised, containing `status_code` and `response` properties.

All errors inherit from `SambanovaAPIError`.

```python
from src.sambanova.api_client import SambanovaAPIClient, SambanovaAPIError

client = SambanovaAPIClient("your_api_key")
try:
    # ...your API call...
    pass
except SambanovaAPIError as e:
    print("An error occurred:", e)
```

Common error codes:

| Status Code | Error Type                  |
|-------------|----------------------------|
| 400         | BadRequestError             |
| 401         | AuthenticationError         |
| 403         | PermissionDeniedError       |
| 404         | NotFoundError               |
| 422         | UnprocessableEntityError    |
| 429         | RateLimitError              |
| >=500       | InternalServerError         |
| N/A         | SambanovaAPIConnectionError |

### Retries and Timeouts

The SDK automatically retries certain errors (connection errors, timeouts, 429, >=500) up to 2 times by default, with exponential backoff. You can configure retries and timeouts globally or per request.

```python
client = SambanovaAPIClient("your_api_key", max_retries=3, timeout=30.0)
```

### Logging

Enable logging by setting the environment variable:

```bash
export SAMBANOVA_LOG=info
```

Or use `debug` for more verbose output.

### Custom Requests

You can make custom requests to undocumented endpoints using the `request` method:

```python
response = client.request("POST", "/custom-endpoint", json={"param": "value"})
print(response)
```

### Managing Resources

The SDK manages HTTP connections automatically. You can manually close the client if needed:

```python
client.close()
```

Or use a context manager:

```python
with SambanovaAPIClient("your_api_key") as client:
    # make requests
    pass
# client is now closed
```

## Requirements

- Python 3.8 or higher

## Contributing

Contributions are welcome! Please read our [contributing guide](CONTRIBUTING.md) for more information on how to get started.