import os
import sys

# Tryggjum að Python finni core möppuna í mimir_net
sys.path.append('/workspace/mimir_net')

# Flytjum inn nýja Alhliða heilann sem þú varst að vista
from core.mimir_core import mimir_core

class MetaAgent:
    def invoke(self, input_data):
        # Sækjum textann frá notanda í Telegram
        task = input_data.get("task", "")
        # Sækjum sögu samtalsins
        messages = input_data.get("messages", [])
        
        # Keyrum Mímir Core (með öllum nýju tækjunum)
        result = mimir_core.invoke({"messages": messages + [("user", task)]})
        
        # Skilum svari sem Telegram bótinn getur sýnt
        return {"result": result["messages"][-1].content}

# Skilgreinum 'graph' svo mimir_bot_v2.py geti kallað á hann
graph = MetaAgent()