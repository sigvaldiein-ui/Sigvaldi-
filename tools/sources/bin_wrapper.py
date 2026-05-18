"""
Sprint 88 — BÍN Wrapper
Sækir nefnimynd úr Beygingarlýsingu íslensks nútímamáls.
Notað af Source Gate til að bera kennsl á nöfn í ólíkum föllum.
"""
import httpx
from typing import Optional

BIN_API_URL = "https://bin.arnastofnun.is/api/beygingarmynd/"


async def get_nominative(word: str) -> Optional[str]:
    """
    Sækir nefnimynd (NFET) fyrir gefna beygingarmynd.
    Skilar uppflettimynd eða None ef hún finnst ekki.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{BIN_API_URL}{word}")
            if resp.status_code != 200:
                return None

            data = resp.json()
            if not data or not isinstance(data, list):
                return None

            # Fyrsta niðurstaða — leita að NFET beygingarmynd
            for entry in data:
                for bmynd in entry.get("bmyndir", []):
                    if bmynd.get("g") == "NFET":
                        return bmynd.get("b")

            # Ef NFET finnst ekki, skila uppflettimynd
            return data[0].get("ord")

    except Exception:
        return None


async def get_all_forms(word: str) -> list[str]:
    """
    Skilar öllum beygingarmyndum fyrir gefna beygingarmynd.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{BIN_API_URL}{word}")
            if resp.status_code != 200:
                return []

            data = resp.json()
            if not data or not isinstance(data, list):
                return []

            forms = []
            for entry in data:
                for bmynd in entry.get("bmyndir", []):
                    forms.append(bmynd.get("b", ""))

            return list(set(forms))  # Fjarlægja tvítekningar

    except Exception:
        return []


# Prófun ef keyrt beint
if __name__ == "__main__":
    import asyncio

    async def test():
        for word in ["Daða", "Kristrúnu", "Þorgerði", "Engin"]:
            nom = await get_nominative(word)
            forms = await get_all_forms(word)
            print(f"{word}: nefnimynd={nom}, allar myndir={forms}")

    asyncio.run(test())
