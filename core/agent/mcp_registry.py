"""MCP Tól-Registry — skráningarkerfi fyrir tól Erindrekans.

Skráir Python föll sem tól, býr til JSON Schema sjálfkrafa,
og veitir Executor aðgang að skráðum tólum.
"""

import json
import inspect
from typing import Dict, Any, Callable, Optional, get_type_hints


class ToolRegistry:
    """Skráningarkerfi fyrir tól.

    Tól eru skráð með nafni, falli, lýsingu og HITL-flaggi.
    """

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: str = "",
        requires_approval: bool = False,
    ):
        """Skráir Python fall sem tól."""
        tool_name = name or func.__name__

        # Búa til JSON Schema úr type hints
        hints = get_type_hints(func)
        parameters = {}
        for param_name, param_type in hints.items():
            if param_name == "return":
                continue
            json_type = "string"
            if param_type == int:
                json_type = "integer"
            elif param_type == float:
                json_type = "number"
            elif param_type == bool:
                json_type = "boolean"

            parameters[param_name] = {"type": json_type}

        schema = {
            "name": tool_name,
            "description": description or func.__doc__ or "",
            "parameters": parameters,
        }

        self._tools[tool_name] = {
            "func": func,
            "schema": schema,
            "requires_approval": requires_approval,
        }

        print(f"[REGISTRY] Skráði tól: {tool_name} (HITL: {requires_approval})")

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Sækir tól eftir nafni."""
        return self._tools.get(name)

    def requires_approval(self, name: str) -> bool:
        """Athugar hvort tól krefst HITL samþykkis."""
        tool = self._tools.get(name)
        return tool["requires_approval"] if tool else False

    def list_tools(self) -> list:
        """Skilar lista af öllum skráðum tólum."""
        return [t["schema"] for t in self._tools.values()]

    def get_schemas_for_llm(self) -> str:
        """Skilar JSON Schema fyrir LLM — svo líkanið viti hvaða tól eru í boði."""
        return json.dumps(self.list_tools(), indent=2, ensure_ascii=False)


# ─── Dummy tól — færð hingað úr tools.py ───

def tool_draft_document(topic: str, context: str = "") -> str:
    """Semur drög að skjali."""
    return f"DRAFT: Skjal um {topic}"


def tool_analyze_text(text: str) -> str:
    """Greinir texta — dregur út lykilatriði."""
    word_count = len(text.split())
    return f"Greining: {word_count} orð"


def tool_write_code(spec: str) -> str:
    """Skrifar kóða út frá lýsingu."""
    return f"def solution():\n    # Kóði fyrir: {spec}\n    pass"


def tool_research(query: str) -> str:
    """Rannsakar efni — kallar á Vitann."""
    return f"Rannsóknarniðurstöður fyrir '{query}'"


def tool_send_email(to: str, subject: str, body: str) -> str:
    """Sendir tölvupóst. KREFST HITL SAMÞYKKIS."""
    return f"Tölvupóstur sendur til {to}: {subject}"


# ─── Keyrsla beint ───
if __name__ == "__main__":
    registry = ToolRegistry()
    registry.register(tool_draft_document, description="Semur drög að skjali")
    registry.register(tool_analyze_text, description="Greinir texta")
    registry.register(tool_write_code, description="Skrifar kóða")
    registry.register(tool_research, description="Rannsakar í gegnum Vitann")
    registry.register(tool_send_email, description="Sendir tölvupóst", requires_approval=True)

    print("\n=== SKRÁÐ TÓL ===")
    for tool in registry.list_tools():
        hitl = "🔴 HITL" if registry.requires_approval(tool["name"]) else "🟢 Öruggt"
        print(f"  {hitl} {tool['name']}: {tool['description']}")

    print("\n=== JSON SCHEMA FYRIR LLM ===")
    print(registry.get_schemas_for_llm())
