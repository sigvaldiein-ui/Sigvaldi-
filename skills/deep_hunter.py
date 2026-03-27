import requests

def scrape_url(url: str) -> str:
    """
    Kafarinn v5.0 (Proxy-Augu): Notar Jina Reader til að brjótast framhjá
    Cloudflare bot-vörnum, rendera JavaScript og sækja faldar töflur.
    Skilar hreinum Markdown texta.
    """
    print(f"🕵️‍♂️ [Proxy-Augu] Kafa í gegnum Jina Reader: {url}")
    
    jina_url = f"https://r.jina.ai/{url}"
    headers = {"Accept": "text/plain"}
    
    try:
        resp = requests.get(jina_url, headers=headers, timeout=25)
        resp.raise_for_status()
        
        texti = resp.text
        if len(texti) < 150 or "Title: " not in texti:
            return "❌ VILLA: Proxy-Augu skiluðu of litlum eða engum gögnum (Bot-vörn)."
            
        return texti[:30000]
        
    except requests.exceptions.Timeout:
        return f"❌ VILLA: Proxy-Augu tímuðu út á {url} (Síðan of þung)."
    except Exception as e:
        return f"❌ VILLA við Proxy-skröpun: {e}"

if __name__ == "__main__":
    print("Testa Kafarann...")
    gogn = scrape_url("https://www.csc.fi/en/lumi-supercomputer/")
    print(f"\n--- NIÐURSTAÐA ---\n{gogn[:500]}")
