
import asyncio
from tools.stjornarradid_source import fetch_stjornarradid

async def search_web_multi(query: str, max_results: int = 5):
    """Sækir eingöngu Stjórnarráð — bein og traust heimild."""
    result = await fetch_stjornarradid(query, max_results)
    return result

def rrf_merge(*args, **kwargs):
    return []
