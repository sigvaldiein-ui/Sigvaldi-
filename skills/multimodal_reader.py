import os
import time
from google import genai
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(BASE_DIR, 'config', '.env'))

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

def analyze_multimodal(file_path: str, user_prompt: str = "") -> str:
    """Multimodal Gáttin v5.1 (Nýja google-genai API)"""
    if not GOOGLE_API_KEY: 
        return "❌ VILLA: Vantar GOOGLE_API_KEY í config/.env"
    if not os.path.exists(file_path): 
        return "❌ VILLA: Skrá fannst ekki á RunPod."

    print(f"\n👁️👂 [Multimodal v5.1] Hleð upp í nýja Google File API: {os.path.basename(file_path)}")
    client = genai.Client(api_key=GOOGLE_API_KEY)
    uploaded_file = None
    
    try:
        # 1. Hlaða upp á örugga gátt
        uploaded_file = client.files.upload(file=file_path)
        print(f"   ✅ Skrá komin í skýið (Nafn: {uploaded_file.name})")
        
        # 2. Bíða eftir vinnslu (Lífsnauðsynlegt fyrir Vídeó og stór PDF)
        while True:
            file_info = client.files.get(name=uploaded_file.name)
            state_str = str(file_info.state)
            if "PROCESSING" in state_str:
                print("   ⏳ Bíð eftir að Google melti skrána...")
                time.sleep(3)
            elif "FAILED" in state_str:
                return "❌ VILLA: Google API gat ekki unnið þessa skrá (Óstudd eða gölluð)."
            else:
                break # Módelið er klárt

        # 3. Keyra greiningu með nýja 2.5 líkaninu
        print("   🧠 Skrá tilbúin. Bið um greiningu frá Gemini 2.5 Flash...")
        prompt = user_prompt
        if not prompt:
            # Flokkum eftir skráarendingu ef enginn texti fylgdi á Telegram
            if file_path.lower().endswith(('.wav', '.mp3', '.ogg', '.oga', '.m4a')):
                prompt = "Hlustaðu á þessi raddskilaboð. Skrifaðu niður hvað er sagt og svaraðu eða leystu verkefnið á faglegri íslensku."
            elif file_path.lower().endswith(('.mp4', '.mov')):
                prompt = "Horfðu á þetta myndband og lýstu nákvæmlega á íslensku hvað er að gerast. Greindu aðalatriðin."
            else:
                prompt = "Greindu þessa skrá eða mynd nákvæmlega og dragðu út helstu upplýsingar á íslensku."

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[file_info, prompt]
        )
        return response.text
        
    except Exception as e:
        return f"❌ Multimodal API Villa: {str(e)}"
        
    finally:
        # 4. ZERO-DATA FOOTPRINT (Eyða úr skýinu!)
        if uploaded_file:
            try:
                client.files.delete(name=uploaded_file.name)
                print(f"   🧹 [ÖRYGGI] Skrá algjörlega eydd af Google API netþjónum.")
            except Exception as e:
                print(f"   ⚠️ Gat ekki eytt skrá úr skýi: {e}")