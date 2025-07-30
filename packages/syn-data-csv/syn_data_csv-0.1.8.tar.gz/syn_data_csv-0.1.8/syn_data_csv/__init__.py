from dotenv import load_dotenv
from pathlib import Path
import os

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

GROQ_API_KEY = os.environ.get("GROQ_API")

print("Loaded GROQ_API_KEY:", GROQ_API_KEY)


from .main import main