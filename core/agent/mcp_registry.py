"""MCP Tól-Registry — með sjálfvirkum JSON Schema generator."""

import json
import inspect
from typing import Dict, Any, Callable, Optional, get_type_hints


class ToolRegistry:
    """Skráningarkerfi fyrir tól með JSON Schema stuðningi."""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, func: Callable, name: Optional[str] = None,
                 description: str = "", requires_approval: bool = False):
        tool_name = name or func.__name__
        hints = get_type_hints(func)
        parameters = {}
        for param_name, param_type in hints.items():
            if param_name == "return":
                continue
            json_type = "string"
            if param_type == int: json_type = "integer"
            elif param_type == float: json_type = "number"
            elif param_type == bool: json_type = "boolean"
            parameters[param_name] = {"type": json_type}

        schema = {"name": tool_name, "description": description or func.__doc__ or "",
                   "parameters": parameters}
        self._tools[tool_name] = {"func": func, "schema": schema,
                                  "requires_approval": requires_approval}
        print(f"[REGISTRY] Skráði tól: {tool_name} (HITL: {requires_approval})")

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        return self._tools.get(name)

    def requires_approval(self, name: str) -> bool:
        tool = self._tools.get(name)
        return tool["requires_approval"] if tool else False

    def list_tools(self) -> list:
        return [t["schema"] for t in self._tools.values()]

    def get_all_schemas(self) -> list:
        """Skilar JSON Schema fyrir öll skráð tól — fyrir LLM."""
        return self.list_tools()


# ─── Tól (dummy) ───

def tool_analyze_text(text: str) -> str:
    """Greinir texta og dregur út lykilatriði."""
    return f"Greining: {len(text.split())} orð"


def tool_draft_document(topic: str, context: str = "") -> str:
    """Semur drög að skjali."""
    return f"DRAFT: Skjal um {topic}"


def tool_research(query: str) -> str:
    """Rannsakar efni í gegnum Vitann."""
    return f"Rannsóknarniðurstöður fyrir '{query}'"


def tool_send_email(to: str, subject: str, body: str) -> str:
    """Sendir tölvupóst. KREFST HITL SAMÞYKKIS."""
    return f"Tölvupóstur sendur til {to}: {subject}"


def tool_write_code(spec: str) -> str:
    """Skrifar kóða út frá lýsingu."""
    return f"def solution():\n    # {spec}\n    pass"


def tool_sign_document(doc_id: str, reason: str) -> str:
    """Undirritar skjal. KREFST HITL SAMÞYKKIS. HÁ ÁHÆTTA."""
    return f"Skjal {doc_id} undirritað: {reason}"
