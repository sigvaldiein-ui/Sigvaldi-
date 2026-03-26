import os
from langchain_community.tools import DuckDuckGoSearchRun

def research_openclaw():
    search = DuckDuckGoSearchRun()
    query = "OpenClaw AI environment web crawling autonomous agents"
    print(f"🔎 Rannsaka: {query}...")
    results = search.run(query)
    
    with open("/workspace/openclaw_plan.md", "w") as f:
        f.write("# OpenClaw & Gagnaöflun Mímis\n\n")
        f.write(results)
    print("✅ Skýrsla vistuð í /workspace/openclaw_plan.md")

if __name__ == "__main__":
    research_openclaw()
