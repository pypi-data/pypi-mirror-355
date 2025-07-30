import requests
from app.adapters.base import BaseChatAdapter

class HuggingFaceChatAdapter(BaseChatAdapter):
    def generate(self, prompt):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"inputs": prompt}
        url = f"https://api-inference.huggingface.co/models/{self.model}"
        response = requests.post(url, headers=headers, json=payload)
        return response.json()[0]["generated_text"]