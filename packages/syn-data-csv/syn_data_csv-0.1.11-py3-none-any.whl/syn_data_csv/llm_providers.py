from syn_data_csv.adapters.groq_adapter import GroqChatAdapter
from syn_data_csv.adapters.hf_adapter import HuggingFaceChatAdapter


def generate_text_from_llm(prompt, provider, api_key, model):

    adapters = {
        "groq": GroqChatAdapter,
        "huggingface": HuggingFaceChatAdapter,
    }

    if provider not in adapters:
        raise ValueError(f"Unsupported provider: {provider}")

    adapter = adapters[provider](api_key=api_key, model=model)
    return adapter.generate(prompt)