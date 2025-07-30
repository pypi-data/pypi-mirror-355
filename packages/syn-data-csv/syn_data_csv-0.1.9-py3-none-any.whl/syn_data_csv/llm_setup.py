from .constants import DEFAULTS, SUPPORTED_PROVIDERS

def get_api_key_model():
    """
    Prompt the user for provider, API key, and model selection.
    Supports Groq and Hugging Face with separate defaults.
    """
    print("\n🔌 Provider, 🔑 API Key & 🤖 Model Selection")
    print("--------------------------------------------------")

    # Prompt for provider
    print("Choose a provider (or press Enter to use default 'groq'):")
    for i, provider in enumerate(SUPPORTED_PROVIDERS, 1):
        print(f"  {i}. {provider.title()}")

    user_provider_input = input("Enter your choice [1 or 2]: ").strip()
    
    if user_provider_input in ['1', '2']:
        provider = SUPPORTED_PROVIDERS[int(user_provider_input) - 1]
    else:
        provider = "groq"
        print(f"✨ Using default provider: {provider}")

    # Get provider-specific defaults
    default_api_key = DEFAULTS[provider]["api_key"]
    default_model = DEFAULTS[provider]["model"]

    # Prompt for API key
    user_api_key = input(f"Enter your API key for {provider.title()} (or press Enter to use default): ").strip()
    api_key = user_api_key if user_api_key else default_api_key

    # Define top models for each provider
    models_by_provider = {
        "groq": [
            "llama3-70b-8192",
            "llama3-8b-8192",
            "mistral-saba-24b",
            "gemma-9b-it",
            "deepseek-r1-distill-llama-70b"
        ],
        "huggingface": [
            "HuggingFaceH4/zephyr-7b-beta",
            "mistralai/Mistral-7B-Instruct-v0.2",
            "google/gemma-7b-it",
            "microsoft/Phi-3-mini-4k-instruct",
            "NousResearch/Nous-Hermes-2-Mistral-7B-DPO"
        ]
    }

    print(f"\nChoose a model for provider '{provider}' (or press Enter to use default):")
    for idx, model_name in enumerate(models_by_provider[provider], 1):
        print(f"  {idx}. {model_name}")
    
    user_model_input = input(f"Enter your choice [1-{len(models_by_provider[provider])}]: ").strip()
    
    model = default_model
    if user_model_input.isdigit():
        index = int(user_model_input) - 1
        if 0 <= index < len(models_by_provider[provider]):
            model = models_by_provider[provider][index]
        else:
            print("⚠️  Invalid input. Using default model.")
    elif user_model_input == '':
        print(f"✨ Using default model: {default_model}")
    else:
        print("⚠️  Invalid input. Using default model.")

    print("✅ Configuration complete.\n")
    return provider, api_key, model

