"""Erindrekinn — Agent runtime (Plan-and-Execute loop).

Þetta er beinagrind sem sýnir arkitektúrinn.
Engin LLM-köll, engin ytri tenging — bara hreinn strúktúr.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Task:
    """Eitt verkefni sem Erindrekinn vinnur að."""
    id: str
    description: str
    status: str = "pending"  # pending → in_progress → done → failed


@dataclass
class Plan:
    """Áætlun — röð af skrefum."""
    task_id: str
    steps: List[str] = field(default_factory=list)


class Planner:
    """Býr til áætlun út frá verkefni.

    Í framtíðinni mun þetta kalla á LLM.
    Núna skilar þetta bara dummy áætlun.
    """

    def create_plan(self, task: Task) -> Plan:
        """Býr til áætlun fyrir verkefni."""
        print(f"[Planner] Bý til áætlun fyrir: {task.description}")
        steps = [
            "Greina verkefni",
            "Sækja gögn (í gegnum Vitann)",
            "Útbúa drög",
            "Senda í yfirlestur",
        ]
        plan = Plan(task_id=task.id, steps=steps)
        print(f"[Planner] Áætlun tilbúin: {len(steps)} skref")
        return plan


class Executor:
    """Framkvæmir skref í áætlun.

    Í framtíðinni mun þetta kalla á tól og LLM.
    Núna prentar þetta bara út hvað það myndi gera.
    """

    def execute_step(self, step: str) -> Dict[str, Any]:
        """Framkvæmir eitt skref."""
        print(f"[Executor] Framkvæmi: {step}")
        return {"step": step, "status": "done", "output": f"Dummy output fyrir: {step}"}


class AgentLoop:
    """Plan-and-Execute lykkja.

    Tengir saman Planner og Executor.
    """

    def __init__(self):
        self.planner = Planner()
        self.executor = Executor()

    def run(self, task: Task) -> Dict[str, Any]:
        """Keyrir alla lykkjuna fyrir eitt verkefni."""
        print(f"\n=== Erindrekinn ræstur fyrir: {task.description} ===")

        # 1. Plan
        plan = self.planner.create_plan(task)

        # 2. Execute hvert skref
        results = []
        for step in plan.steps:
            result = self.executor.execute_step(step)
            results.append(result)

        print(f"=== Erindrekinn kláraði: {len(results)} skref ===")
        return {"task": task.description, "steps": results}


# ─── Keyrslu-dæmi (þegar skráin er keyrð beint) ───
if __name__ == "__main__":
    loop = AgentLoop()
    task = Task(id="demo-1", description="Sækja upplýsingar um fæðingarorlof")
    loop.run(task)
