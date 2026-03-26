import os
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.tools.file_management import WriteFileTool
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool

# SOP: Algildar slóðir og stillingar
load_dotenv('/workspace/mimir_net/config/.env')

@tool
def read_advanced_file(file_path: str) -> str:
    """Les PDF, Excel, CSV, Docx og Text. Notaðu fullgilda slóð."""
    if not os.path.isabs(file_path):
        file_path = os.path.join("/workspace/mimir_net", file_path)
    
    if not os.path.exists(file_path):
        sandbox_path = os.path.join("/workspace/mimir_net/sandbox", os.path.basename(file_path))
        if os.path.exists(sandbox_path):
            file_path = sandbox_path
        else:
            return f"Villa: Skrá fannst ekki á {file_path}"
    
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == '.pdf':
            reader = PdfReader(file_path)
            return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        elif ext in ['.xlsx', '.xls']:
            return pd.read_excel(file_path).head(20).to_string()
        elif ext == '.csv':
            return pd.read_csv(file_path).head(20).to_string()
        elif ext == '.docx':
            return "\n".join([p.text for p in Document(file_path).paragraphs])
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        return f"Villa við lestur á {ext}: {str(e)}"

# Flytjum inn sérsniðin tól
try:
    from core.tools import get_current_time, send_email
except ImportError:
    from tools import get_current_time, send_email

tools = [
    DuckDuckGoSearchRun(),
    PythonREPLTool(),
    get_current_time,
    read_advanced_file,
    WriteFileTool(root_dir="/workspace/mimir_net/sandbox")
]
if 'send_email' in globals() and send_email:
    tools.append(send_email)

llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="anthropic/claude-3.5-sonnet", 
    temperature=0
)

system_prompt = "Þú ert Mímir Core (AGI). Þú getur lesið PDF/Excel. Notaðu tækin þín sjálfstætt."
mimir_core = create_react_agent(llm, tools, prompt=system_prompt)