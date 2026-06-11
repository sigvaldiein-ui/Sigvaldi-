"""SPOR 10 — Heildarprófun: Schema, Router, Mock gögn."""

import sys
sys.path.insert(0, "/workspace/Sigvaldi-")
import json

print("=" * 60)
print("SPOR 10 — MCP SCHEMA, ROUTER, MOCK")
print("=" * 60)

# 1. MCP Schema Generator
print("\n1. MCP SCHEMA GENERATOR...")
from core.agent.mcp_registry import ToolRegistry, tool_analyze_text, tool_draft_document
from core.agent.mcp_registry import tool_research, tool_send_email, tool_write_code, tool_sign_document

reg = ToolRegistry()
reg.register(tool_analyze_text, description="Greinir texta og dregur út lykilatriði")
reg.register(tool_draft_document, description="Semur drög að skjali")
reg.register(tool_research, description="Rannsakar efni í gegnum Vitann")
reg.register(tool_send_email, description="Sendir tölvupóst", requires_approval=True)
reg.register(tool_write_code, description="Skrifar kóða út frá lýsingu")
reg.register(tool_sign_document, description="Undirritar skjal — HÁ ÁHÆTTA", requires_approval=True)

schemas = reg.get_all_schemas()
print(f"   ✅ {len(schemas)} tól skráð með JSON Schema")
for s in schemas:
    hitl = "🔴" if reg.requires_approval(s["name"]) else "🟢"
    print(f"   {hitl} {s['name']}: {s['description'][:50]}")

# 2. LLM Router
print("\n2. LLM ROUTER...")
from core.agent.llm_router import LLMRouter
router = LLMRouter()
print(f"   Brons + 'Greina samning' → {router.route_task('Greina samning', 'brons')}")
print(f"   Gull + 'Greina samning' → {router.route_task('Greina samning', 'gull')}")
print(f"   Brons + 'Skrifa flókinn kóða' → {router.route_task('Skrifa flókinn kóða', 'brons')}")
print(f"   Gull + 'Skrifa flókinn kóða' → {router.route_task('Skrifa flókinn kóða', 'gull')}")

# 3. Mock gögn
print("\n3. MOCK GÖGN...")
from core.agent.hitl_db import HITLDatabase
db = HITLDatabase()
pending = db.get_pending()
print(f"   ✅ {len(pending)} beiðnir í biðröð (tilbúnar fyrir Hönnuð)")
for item in pending:
    colors = {1: "🟢", 2: "🟡", 3: "🔴"}
    print(f"   {colors.get(item['risk_tier'], '⚪')} {item['item_id']}: {item['tool_name']} — {item['preview'][:60]}")

print("\n" + "=" * 60)
print("SPOR 10 — PRÓFUN LOKIÐ")
print("=" * 60)
