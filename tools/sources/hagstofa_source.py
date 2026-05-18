"""
Sprint 87 — Hagstofa Source
Hybrid: keyword fast-path + dynamic PX-Web API fetch.
Phase D V1: metadata GET + aggregate POST + one-step previous-year fallback.
"""
import asyncio
import copy
import httpx
from datetime import datetime, timezone
from typing import Dict

HAGSTOFA_API = "https://px.hagstofa.is/pxis/api/v1/is"

KEYWORD_FASTPATH = {
    "mannfjoldi": "MAN00101",
    "ibuar": "MAN00101",
    "ibúar": "MAN00101",
    "íbúafjöldi": "MAN00101",
    "fólksfjöldi": "MAN00101",
    "population": "MAN00101",
    "verdbolga": "VIS01000",
    "verdbólga": "VIS01000",
    "verðbólga": "VIS01000",
    "neysluveris": "VIS01000",
    "neysluverð": "VIS01000",
    "atvinnuleysi": "VIN00910",
    "atvinnuthattaka": "VIN00910",
    "atvinnuþátttaka": "VIN00910",
    "laun": "LAN10001",
    "meðallaun": "LAN10001",
    "sveitarfelag": "MAN10001",
    "sveitarfélag": "MAN10001",
}

TABLE_META = {
    "MAN00101": {
        "title": "Mannfjöldi eftir kyni og aldri",
        "url": f"{HAGSTOFA_API}/Ibuar/mannfjoldi/1_yfirlit/Yfirlit_mannfjolda/MAN00101.px",
        "public_url": "https://px.hagstofa.is/pxis/pxweb/is/Ibuar/Ibuar__mannfjoldi__1_yfirlit__Yfirlit_mannfjolda/MAN00101.px",
    },
    "MAN10001": {
        "title": "Mannfjöldi eftir sveitarfélögum",
        "url": f"{HAGSTOFA_API}/Ibuar/mannfjoldi/2_byggdir/sveitarfelog/MAN10001.px",
        "public_url": "https://px.hagstofa.is/pxis/pxweb/is/Ibuar/Ibuar__mannfjoldi__2_byggdir__sveitarfelog/MAN10001.px",
    },
    "VIS01000": {
        "title": "Vísitala neysluverðs og breytingar",
        "url": f"{HAGSTOFA_API}/Efnahagur/visitolur/visitalaNeysluverdis/VIS01000.px",
        "public_url": "https://px.hagstofa.is/pxis/pxweb/is/Efnahagur/Efnahagur__visitolur__1_vnv__1_vnv/VIS01000.px",
    },
    "VIN00910": {
        "title": "Atvinnuþátttaka og atvinnuleysi",
        "url": f"{HAGSTOFA_API}/Atvinnuvegir/vinnumarkadur/atvinnuthattaka/VIN00910.px",
        "public_url": "https://px.hagstofa.is/pxis/pxweb/is/Atvinnuvegir/Atvinnuvegir__vinnumarkadur__1_vinnumarkadsrannsoknir__3_arstolur/VIN00910.px",
    },
    "LAN10001": {
        "title": "Meðallaun eftir starfsstéttum",
        "url": f"{HAGSTOFA_API}/Samfelag/launogtekjur/laun/LAN10001.px",
        "public_url": "https://px.hagstofa.is/pxis/pxweb/is/Samfelag/Samfelag__launogtekjur__1_laun__1_arsfjordungslaun/LAN10001.px",
    },
}


def _keyword_lookup(query: str) -> str | None:
    q = query.lower()
    for keyword, table_id in KEYWORD_FASTPATH.items():
        if keyword in q:
            return table_id
    return None


async def _get_table_metadata(client: httpx.AsyncClient, url: str) -> Dict:
    resp = await client.get(url, timeout=20)
    resp.raise_for_status()
    return resp.json()


def _build_default_selection(variables: list) -> Dict:
    selection = []
    for v in variables:
        code = v["code"]
        values = v.get("values", [])
        is_time = v.get("time", False)

        if "Total" in values:
            sel = {"filter": "item", "values": ["Total"]}
        elif "-1" in values:
            sel = {"filter": "item", "values": ["-1"]}
        elif is_time and values:
            sel = {"filter": "item", "values": [values[-1]]}
        elif values:
            sel = {"filter": "item", "values": [values[0]]}
        else:
            continue

        selection.append({"code": code, "selection": sel})

    return {"query": selection, "response": {"format": "json"}}


def _find_time_var_index(variables: list) -> int:
    for i, v in enumerate(variables):
        if v.get("time", False):
            return i
    return -1


def _format_number(value) -> str:
    try:
        return f"{int(value):,}".replace(",", ".")
    except Exception:
        return str(value)


async def _post_px_query(client: httpx.AsyncClient, url: str, body: Dict) -> Dict:
    resp = await client.post(url, json=body, timeout=20)
    resp.raise_for_status()
    return resp.json()


async def _fetch_table_data(client: httpx.AsyncClient, table_id: str) -> Dict:
    meta = TABLE_META.get(table_id, {})
    title = meta.get("title", table_id)
    url = meta.get("url", "")

    try:
        metadata = await _get_table_metadata(client, url)
        variables = metadata.get("variables", [])
        body = _build_default_selection(variables)

        response = await _post_px_query(client, url, body)
        data_rows = response.get("data", [])

        year_var_index = _find_time_var_index(variables)
        year_values = variables[year_var_index].get("values", []) if year_var_index >= 0 else []

        if not data_rows and year_var_index >= 0 and len(year_values) >= 2:
            retry_body = copy.deepcopy(body)
            retry_body["query"][year_var_index]["selection"]["values"] = [year_values[-2]]
            response = await _post_px_query(client, url, retry_body)
            data_rows = response.get("data", [])

        if data_rows and data_rows[0].get("values"):
            value_str = data_rows[0]["values"][0]
            formatted = _format_number(value_str)
            row_key = data_rows[0].get("key", [])
            year = row_key[year_var_index] if year_var_index >= 0 and len(row_key) > year_var_index else ""

            if table_id == "MAN00101" and year:
                snippet = f"Mannfjöldi á Íslandi {year}: {formatted} (Hagstofa {table_id})"
            else:
                snippet = f"Hagstofa: {title} — {formatted}"

            value_count = len([r for r in data_rows if r.get("values")])
        else:
            snippet = f"{title}: gögn ekki tiltæk fyrir nýjustu ár"
            value_count = 0

        return {
            "title": title,
            "url": meta.get("public_url", url),
            "snippet": snippet,
            "source": "hagstofa",
            "table_id": table_id,
            "tier": "sovereign",
            "sovereign": True,
            "value_count": value_count,
            "accessed_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        return {
            "title": title,
            "url": meta.get("public_url", url),
            "snippet": title,
            "source": "hagstofa",
            "table_id": table_id,
            "tier": "sovereign",
            "sovereign": True,
            "accessed_at": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }


async def fetch_hagstofa(query: str, max_results: int = 5) -> Dict:
    citations = []
    try:
        async with httpx.AsyncClient(
            timeout=20,
            headers={"User-Agent": "Alvitur-Sovereign-Bot/1.0"}
        ) as client:
            table_id = _keyword_lookup(query)
            if table_id:
                result = await _fetch_table_data(client, table_id)
                result["rank"] = 1
                citations.append(result)

                if table_id != "MAN10001" and "MAN10001" in TABLE_META and max_results > 1:
                    fallback = await _fetch_table_data(client, "MAN10001")
                    fallback["rank"] = 2
                    citations.append(fallback)
            else:
                tasks = [_fetch_table_data(client, tid) for tid in list(TABLE_META.keys())[:max_results]]
                results = await asyncio.gather(*tasks)
                for i, r in enumerate(results, 1):
                    r["rank"] = i
                    citations.append(r)

        return {
            "citations": citations,
            "source": "hagstofa",
            "raw_count": len(citations),
        }

    except httpx.TimeoutException:
        return {"citations": [], "source": "hagstofa", "error": "timeout", "raw_count": 0}
    except Exception as e:
        return {"citations": [], "source": "hagstofa", "error": f"unexpected_{type(e).__name__}", "raw_count": 0}


if __name__ == "__main__":
    async def test():
        result = await fetch_hagstofa("íbúafjöldi á Íslandi 2026")
        print(f"Fjöldi: {result['raw_count']}")
        for c in result["citations"]:
            print(f"{c['rank']}. [{c['table_id']}] {c['title']}")
            print(f"   {c['snippet']}")
            print(f"   accessed_at: {c['accessed_at']}")
            if c.get("error"):
                print(f"   error: {c['error']}")

    asyncio.run(test())
