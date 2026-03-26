import os
from datetime import datetime
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage

# 1. LYKLAUPPSETNING
env_path = "/workspace/mimir_net/config/.env"
load_dotenv(env_path)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError(
        f"VILLA: Fann ekki OPENROUTER_API_KEY í {env_path}. Athugaðu skrána!"
    )

# 2. VERKFÆRI
search_tool = DuckDuckGoSearchRun()
tools = [search_tool]

# 3. LLM (Claude 3 Haiku í gegnum OpenRouter)
today_date = datetime.now().strftime("%d. %B %Y")

system_prompt = f"""Þú ert Mímir, snjall íslenskur gervigreindaraðstoðarmaður.
Dagsetningin í dag er {today_date}.
Þú hefur aðgang að leitarvél (DuckDuckGo) til að finna nýjustu upplýsingar.

ÞÍNAR REGLUR:
1. SVARAÐU ALLTAF Á FULLKOMINNI ÍSLENSKU.
2. Þýddu og dragðu saman mikilvægustu punktana.
3. Nefndu alltaf hvaðan upplýsingarnar koma.
4. Vertu hnitmiðaður og faglegur.
5. Þú ert aðstoðarmaður notandans og hjálpar honum að finna og skilja upplýsingar.
6. Talaðu aldrei eins og þú sért sjálfur að fara að framkvæma hluti í raunheimum; þú lýsir aðeins hvað notandinn getur gert eða hvað niðurstöðurnar sýna.
"""

llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    model="anthropic/claude-3-haiku",
    temperature=0.1,
)

# 4. AGENT – ReAct agent með DuckDuckGo
mimir_search_agent = create_react_agent(
    llm,
    tools,
)

# 5. FALL SEM TELEGRAM-BOTURINN MUN NOTA SÍÐAR
def run_search(query: str) -> str:
    """Tekur inn spurningu og skilar íslenskri samantekt úr netleit."""
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query),
    ]
    result = mimir_search_agent.invoke(
        {"messages": messages},
        {"recursion_limit": 5},
    )
    return result["messages"][-1].content

# 6. PRUFUKEYRSLA
if __name__ == "__main__":
    print(f"--- 🧠 Mímir Search Agent vaknar (Dags: {today_date}) ---")
    test_question = "Hver eru helstu fréttamál á Íslandi í dag?"
    print(f"👤 Sigvaldi spyr: {test_question}")
    print("🔍 Mímir rannsakar netið...\n")

    svar = run_search(test_question)
    print("--- 🏆 SVAR MÍMIS ---")
    print(svar)