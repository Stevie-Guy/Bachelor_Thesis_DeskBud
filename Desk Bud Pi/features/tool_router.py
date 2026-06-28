from features.tools.abstract_tool import ToolHandler


class ToolRouter:
    def __init__(self):
        self.handlere: list[ToolHandler] = []

    def adauga_handler(self, handler: ToolHandler):
        self.handlere.append(handler)

    def proceseaza(self, prompt: str) -> str | None:
        for handler in self.handlere:
            raspuns = handler.proceseaza(prompt)
            if raspuns is not None:
                return raspuns
        return None
