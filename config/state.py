from typing import TypedDict, Annotated, List
import operator

class MimirState(TypedDict):
    messages: Annotated[List[dict], operator.add]
    task: str
    result: str

print("✅ MimirState tilbúinn")
