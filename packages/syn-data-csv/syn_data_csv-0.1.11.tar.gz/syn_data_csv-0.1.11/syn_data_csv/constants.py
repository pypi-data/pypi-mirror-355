import yaml
import os

# Get the absolute path to the config.yaml file in the same directory
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yaml')

# Read the YAML file
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

# Access keys safely
GROQ_API_KEY = config.get("GROQ_API")
DEFAULT_MODEL = config.get("MODEL", "mistral-saba-24b")

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