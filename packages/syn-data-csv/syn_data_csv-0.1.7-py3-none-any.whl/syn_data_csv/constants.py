import os
from dotenv import load_dotenv


load_dotenv() 

GROQ_API_KEY = os.getenv("GROQ_API")
DEFAULT_MODEL = os.getenv("MODEL", "mistral-saba-24b")

DEFAULTS = {
    "groq": {
        "api_key": GROQ_API_KEY,
        "model": "llama3-8b-8192"
    },
    "huggingface": {
        "api_key": "your-huggingface-api-key",
        "model": "HuggingFaceH4/zephyr-7b-beta"
    }
}

SUPPORTED_PROVIDERS = ["groq", "huggingface"]

MAX_BATCH_SIZE = 100
MAX_DEFAULT_ROWS = 100