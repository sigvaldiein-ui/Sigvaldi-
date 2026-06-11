"""LLM Router — velur líkan eftir áskriftarþrepi og flækjustigi."""

from typing import Optional


class LLMRouter:
    """Beinagrind að líkana-vali. Engin HTTP-köll — skilar aðeins streng."""

    def route_task(self, task_description: str, tier: str = "brons") -> str:
        """Velur líkan byggt á þrepi og verkefnalýsingu.

        Args:
            task_description: Lýsing á verkefninu
            tier: brons, silfur, gull

        Returns:
            Nafn líkans sem streng
        """
        task_lower = task_description.lower()

        # Gull áskrifendur fá alltaf Stórmeistara fyrir flókin verkefni
        if tier == "gull":
            if any(w in task_lower for w in ["kóði", "kóða", "flókið", "samning"]):
                return "openrouter_claude"
            return "openrouter_claude"

        # Silfur áskrifendur fá Stórmeistara fyrir kóða og flókin verkefni
        if tier == "silfur":
            if any(w in task_lower for w in ["kóði", "kóða", "flókið"]):
                return "openrouter_claude"
            return "local_qwen"

        # Brons áskrifendur fá alltaf Qwen
        return "local_qwen"


# ─── Keyrsla beint ───
if __name__ == "__main__":
    router = LLMRouter()
    
    tests = [
        ("Brons", "Greina samning", "brons"),
        ("Gull", "Greina samning", "gull"),
        ("Brons", "Skrifa flókinn kóða fyrir gagnagrunn", "brons"),
        ("Gull", "Skrifa flókinn kóða fyrir gagnagrunn", "gull"),
        ("Silfur", "Skrifa kóða", "silfur"),
    ]
    
    for label, task, tier in tests:
        result = router.route_task(task, tier)
        print(f"  {label} ({tier}): '{task[:40]}...' → {result}")
