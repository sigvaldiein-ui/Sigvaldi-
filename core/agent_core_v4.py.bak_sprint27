import os
import sys
import requests
import urllib.parse
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

from skills.deep_hunter import scrape_url

load_dotenv(os.path.join(BASE_DIR, 'config', '.env'))
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

def ask_llm(system_prompt: str, user_prompt: str, temp: float = 0.1) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "google/gemini-2.5-flash",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temp
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"VILLA: {e}"

def optimize_query(spurning: str) -> str:
    from datetime import datetime
    nuverandi_ar = datetime.now().year
    sys_prompt = (
        f"Thu ert OSINT leitarvelarserfreaingur. Arid i dag er {nuverandi_ar}. "
        "Notandi spyr a islensku. Thitt EINA verkefni er ao skila hnitmioudum, enskum leitarstreng (max 4-6 ord) "
        "fyrir leitarvel til ao finna hragogn. Slepptu fyllioroum eins og 'news' eda 'specs'. "
        f"MIKILVAEGT: Ef spurningin fjallar um eitthvad nytt, 'nyjaста' eda krefst nyrra upplysinga, "
        f"baettu tha ARTALINU {nuverandi_ar} vid leitarstrenginn til ao fordast gomul gogn. "
        f"Daemi: 'NVIDIA latest GPU {nuverandi_ar}'. "
        "Skilaou AETHEINS enska leitarstrenginn an utskyringa."
    )
    ensk_leit = ask_llm(sys_prompt, spurning, temp=0.0)
    if "VILLA" in ensk_leit or len(ensk_leit) > 150:
        return spurning
    return ensk_leit.replace('"', '').replace("'", "").strip()

def get_radar_urls(query: str):
    """Óbrjótanlegt Dual-Radar kerfi"""
    urls = []
    
    # 1. AÐAL-RATSJÁ (Google Search)
    try:
        from googlesearch import search
        print("📡 Sendi Ratsjá beint á Google Search...")
        urls = list(search(query, num_results=5, lang="en"))
    except Exception as e:
        print(f"   ⚠️ Google Ratsjá lokaði (IP blokkun eða pakki vantar).")

    # 2. VARA-RATSJÁ (DuckDuckGo Raw HTML - Algjörlega óháð pökkum)
    if not urls:
        print("📡 Kveiki á Vara-Ratsjá (DuckDuckGo Raw HTML)...")
        try:
            from bs4 import BeautifulSoup
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.post("https://html.duckduckgo.com/html/", data={"q": query}, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            for a in soup.find_all('a', class_='result__url'):
                href = a.get('href')
                if href and "uddg=" in href:
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    if "uddg" in parsed:
                        url_cand = parsed["uddg"][0]
                        if "y.js" not in url_cand and "duckduckgo.com" not in url_cand:
                            urls.append(url_cand)
                elif href and href.startswith("http"):
                    if "y.js" not in href and "duckduckgo.com" not in href:
                        urls.append(href)
                if len(urls) >= 5:
                    break
        except Exception as e:
            print(f"   ⚠️ Vara-Ratsjá bilaði: {e}")

    return urls[:5]

def analyze_query(spurning: str):
    print(f"\n🔍 [Mímir v4.7] Upprunaleg spurning: '{spurning}'")
    enska_leitin = optimize_query(spurning)
    print(f"🎯 [Query Optimizer] Radar stilltur á: '{enska_leitin}'")
    
    urls = get_radar_urls(enska_leitin)

    if not urls:
        return "🛑 **Failure Mode:** Ratsjár fundu engar slóðir á netinu. Allar varaleiðir brugðust."

    system_svar = (
        "Þú ert Mímir. Svaraðu á fágaðri íslensku EINGÖNGU út frá GÖGNUM í textanum. "
        "Dragðu út þær upplýsingar sem tengjast spurningunni. "
        "Það er Í LAGI þótt þú finnir ekki svar við öllum hlutum spurningarinnar (t.d. ef FP8 vantar en minnisbandvídd er til staðar, gefðu upp minnisbandvíddina og LLM greininguna). "
        "Ef textinn fjallar alls ekki um efnið eða inniheldur engar gagnlegar tölur, svaraðu ÞÁ AÐEINS NÁKVÆMLEGA: 'EKKI_FUNDIÐ'."
    )

    kannadar_slodir = []
    for i, url in enumerate(urls[:5]):
        print(f"🤿 Strike {i+1}/5: Kafa í {url}")
        kannadar_slodir.append(url)
        gogn = scrape_url(url)
        
        if "❌" in gogn or len(gogn) < 200: 
            print("   ⚠️ Slóð varin eða biluð. Stekk á næstu...")
            continue
            
        print("   🧠 Greini gögn í vinnsluminni...")
        usr_prompt = f"GÖGN (Markdown):\n{gogn[:25000]}\n\nSPURNING: {spurning}"
        svar = ask_llm(system_svar, usr_prompt)
        
        if "EKKI_FUNDIÐ" not in svar:
            print("   ✅ Gögn fundin og svöruð!")
            return f"📄 **Heimild:** {url}\n\n🤖 **Mímir:**\n{svar}"
            
    slodir_str = "\n".join([f"- {s}" for s in kannadar_slodir])
    return f"🛑 **Failure Mode (5-Strikes):**\nÉg kafaði í þessar heimildir en fann ekki umbeðin gögn:\n{slodir_str}\n\nLeitinni hætt."
