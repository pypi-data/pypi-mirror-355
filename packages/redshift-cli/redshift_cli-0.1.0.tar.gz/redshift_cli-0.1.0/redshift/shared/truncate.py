class Truncator:
    def __init__(self, model: str):
        self.model = model

    def standard_truncate(self, text: str, max_tokens: int) -> str:
        pass

    def window_truncate(self, text: str, max_tokens: int) -> str:
        pass

    def middle_truncate(self, text: str, max_tokens: int) -> str:
        pass
