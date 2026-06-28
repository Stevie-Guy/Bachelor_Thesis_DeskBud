from abc import ABC, abstractmethod


class ToolHandler(ABC):
    # Orce handler va implementa metoda proceseaza si returneaza string-ul spus de TTS.

    @abstractmethod
    def proceseaza(self, text: str) -> str | None:
        pass
