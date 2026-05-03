import os
import pandas as pd
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.tools.file_management import WriteFileTool
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool

# ==========================================
# 🛡️ REKSTRARHEILLEIKI (SOP)
# ==========================================
ENV_PATH = '/workspace/.env'
SANDBOX_DIR = '/workspace/Sigvaldi-/sandbox'

if not os.path.exists(ENV_PATH):
    print("❌ ERROR: .env skrá vantar í /config/. Stöðva ræsingu.")
    exit(1)

load_dotenv(ENV_PATH)

# Staðfesta innflutning á innri einingum
FULL_SYSTEM = False
try:
    from data_ingestion.drive_handler import GDriveHandler
    FULL_SYSTEM = True
    print("✅ Mímir Net einingar fundust.")
except ImportError:
    print("⚠️ VIÐVÖRUN: drive_handler fannst ekki. Takmörkuð virkni.")

# ==========================================
# 🛠️ VERKFÆRI (TOOLS)
# ==========================================

@tool
def read_advanced_file(file_path: str) -> str:
    """
    Les PDF, Excel, CSV og Textaskrár. 
    Leitar sjálfkrafa í sandbox ef engin slóð er gefin.
    """
    if not os.path.isabs(file_path):
        file_path = os.path.join(SANDBOX_DIR, os.path.basename(file_path))
    
    if not os.path.exists(file_path):
        return f"Villa: Skrá fannst ekki á slóðinni {file_path}"
    
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == '.pdf':
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text if text.strip() else "PDF er tóm eða myndatengd."
        
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
            return f"Excel gögn (fyrstu 30 línur):\n{df.head(30).to_string()}"
        
        elif ext == '.csv':
            df = pd.read_csv(file_path)
            return f"CSV gögn (fyrstu 30 línur):\n{df.head(30).to_string()}"
        
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        return f"Villa við vinnslu á {ext} skrá: {str(e)}"

@tool
def upload_to_drive(file_name: str) -> str:
    """
    Flytur skrá úr sandbox yfir á Google Drive (Data Lake).
    Gefur skýra stöðu ef kvóta er náð.
    """
    local_path = os.path.join(SANDBOX_DIR, file_name)
    if not os.path.exists(local_path):
        # Leita í rót ef hún er ekki í sandbox
        local_path = os.path.join('/workspace/Sigvaldi-', file_name)
        
    if not os.path.exists(local_path):
        return f"Villa: fann ekki skrána {file_name} til að hlaða upp."

    if not FULL_SYSTEM:
        return "Villa: DriveHandler er ekki virkur."

    handler = GDriveHandler()
    return handler.upload_file(local_path)

# Samsetning verkfæra
tools = [
    DuckDuckGoSearchRun(),
    PythonREPLTool(),
    read_advanced_file,
    upload_to_drive,
    WriteFileTool(root_dir=SANDBOX_DIR)
]

# ==========================================
# 🧠 HEILINN (CLAUDE 3.5 SONNET)
# ==========================================
llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="anthropic/claude-3.5-sonnet",
    temperature=0
)

system_prompt = (
    "Þú ert Mímir Core, Alhliða gervigreind (AGI) og MBA/AI ráðgjafi Sigvalda. "
    "Þitt hlutverk er að veita hnitmiðuð, beitt og fagleg svör byggð á gögnum. "
    "Þú vinnur í 'Hreinu herbergi' (/workspace/Sigvaldi-/sandbox). "
    "Allar greiningar skulu vera hnitmiðaðar og miða að því að hámarka virði AI.is."
)

# Agent ræsing
mimir_core = create_react_agent(llm, tools, prompt=system_prompt)

if __name__ == "__main__":
    print("Mímir v2 vaknaður! LangGraph heilinn virkur! 🧠")