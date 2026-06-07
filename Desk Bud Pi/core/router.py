class ModelRouter:
    """
    Decide ce model sa foloseasca pe baza prompt-ului.
    Default: modelul 3B. Doar pentru fraze foarte simple
    si scurte, foloseste modelul 1B.
    """

    FRAZE_SIMPLE = (
        "hi",
        "hello",
        "hey",
        "yo",
        "sup",
        "bye",
        "goodbye",
        "see you",
        "thanks",
        "thank you",
        "thx",
        "yes",
        "no",
        "yeah",
        "yep",
        "nope",
        "nah",
        "ok",
        "okay",
        "got it",
        "sure",
        "alright",
        "cool",
        "nice",
        "good morning",
        "good afternoon",
        "good evening",
        "good night",
        "how are you",
        "what's up",
        "whats up",
        "please",
        "sorry",
        "my bad",
        "no problem",
    )

    FRAZE_SCURTE_COMPLEXE = (
        "what",
        "how",
        "why",
        "when",
        "where",
        "who",
        "which",
        "explain",
        "define",
        "describe",
        "calendar",
        "schedule",
        "weather",
        "remind",
        "reminder",
    )

    MAX_CUVINTE_PROMPT_SIMPLU = 4

    def __init__(self, model_rapid: str, model_smart: str):
        self.model_rapid = model_rapid
        self.model_smart = model_smart

    def alege_model(self, prompt: str) -> str:
        """Returneaza numele modelului potrivit pentru acest prompt."""
        text = prompt.lower().strip().rstrip(".!?,;:")

        if text in self.FRAZE_SIMPLE:
            return self.model_rapid

        cuvinte_prompt = text.split()

        if len(cuvinte_prompt) <= self.MAX_CUVINTE_PROMPT_SIMPLU:
            are_cuvinte_complexe = False
            for cuvant in cuvinte_prompt:
                if cuvant in self.FRAZE_SCURTE_COMPLEXE:
                    are_cuvinte_complexe = True

            if not are_cuvinte_complexe:
                return self.model_rapid

        return self.model_smart
