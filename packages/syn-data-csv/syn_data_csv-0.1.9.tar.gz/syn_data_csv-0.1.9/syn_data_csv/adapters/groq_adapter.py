from groq import Groq
from syn_data_csv.adapters.base import BaseChatAdapter

class GroqChatAdapter(BaseChatAdapter):

    def generate(self, prompt):
        client = Groq(api_key=self.api_key)
        messages = [{"role": "user", "content": prompt}]
        completion = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=1,
            max_tokens=6000,
            top_p=1,
            stream=True
        )
        response = ""
        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                response += chunk.choices[0].delta.content
        return response.strip()