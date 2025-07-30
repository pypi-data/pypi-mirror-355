class BaseChatAdapter:
    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model

    def generate(self, prompt):
        raise NotImplemetedError("Each adapter must implement `generate` method." )
