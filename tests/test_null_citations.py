import sys
sys.path.insert(0, '/workspace/Sigvaldi-')
from interfaces.chat_routes import _validate_response
ok, _ = _validate_response("Lög nr. 99/2023 segja að ...", [])
print(f"Tóm citations: grounding_ok={ok} (á að vera False)")
