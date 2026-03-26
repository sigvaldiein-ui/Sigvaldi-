import os
import sys

# Tryggjum að Python finni core möppuna í mimir_net
sys.path.append('/workspace/mimir_net')

from core.mimir_core import mimir_core

class MetaAgent:
    def invoke(self, input_data):
        # Sækjum textann og sögu skilaboða
        task = input_data.get("task", "")
        messages = input_data.get("messages", [])
        
        # Keyrum Alhliða (AGI) heilann með tækjunum
        result = mimir_core.invoke({"messages": messages + [("user", task)]})
        
        # Skilum svari sem Telegram bótinn getur sýnt
        return {"result": result["messages"][-1].content}

graph = MetaAgent()