"""Sprint 69 Track E — Ingest 4 sample laws into Qdrant alvitur_laws_v1.

Usage: PYTHONPATH=/workspace/Sigvaldi- python3 scripts/ingest_laws.py
"""
import time, json
from pathlib import Path
from core.ingestion.chunker import LegalDocumentChunker
from core.ingestion.vector_store import LegalVectorStore

LAWS = [
    ("data/bronze/logs/samples/1994145_bokhald.html",
     {"law_nr":145,"law_year":1994,"law_title":"um bókhald",
      "source_url":"https://www.althingi.is/lagas/nuna/1994145.html"}),
    ("data/bronze/logs/samples/2003090_tekjuskattur.html",
     {"law_nr":90,"law_year":2003,"law_title":"um tekjuskatt til ríkisins",
      "source_url":"https://www.althingi.is/lagas/nuna/2003090.html"}),
    ("data/bronze/logs/samples/2016118_fasteignalan.html",
     {"law_nr":118,"law_year":2016,"law_title":"um fasteignalán til neytenda",
      "source_url":"https://www.althingi.is/lagas/nuna/2016118.html"}),
    ("data/bronze/logs/samples/2018090_personuvernd.html",
     {"law_nr":90,"law_year":2018,"law_title":"um persónuvernd og vinnslu persónuupplýsinga",
      "source_url":"https://www.althingi.is/lagas/nuna/2018090.html"}),
]

def main():
    print("=== ALVITUR RAG+ INGESTION ===")
    print(f"Model: intfloat/multilingual-e5-large")
    print(f"Target: data/qdrant_store/alvitur_laws_v1")
    print()

    chunker = LegalDocumentChunker()
    vs = LegalVectorStore(model_name="intfloat/multilingual-e5-large")
    print(f"Collection count before: {vs.count()}")
    print()

    total_chunks = 0
    results = []
    for path, meta in LAWS:
        t0 = time.time()
        html = open(path).read()
        chunks = chunker.parse_html(html, meta)
        n = vs.upsert_chunks(chunks)
        elapsed = round(time.time()-t0, 2)
        print(f"OK {meta['law_nr']}/{meta['law_year']} — {n} chunks — {elapsed}s")
        total_chunks += n
        results.append({"law": f"{meta['law_nr']}/{meta['law_year']}", "chunks": n, "seconds": elapsed})

    print()
    print(f"Total chunks ingested: {total_chunks}")
    print(f"Collection count after: {vs.count()}")

    # Quick search test
    print()
    print("=== SEARCH TEST ===")
    queries = [
        "bókhaldsskyldir aðilar",
        "fasteignalán neytendavernd",
        "persónuvernd vinnsla gagna",
    ]
    for q in queries:
        hits = vs.search(q, top_k=2)
        print(f"Q: {q!r}")
        for h in hits:
            print(f"  score={h.score:.3f} law={h.payload['law_nr']}/{h.payload['law_year']} gr={h.payload['grein']}")

    # Vista manifest
    manifest = {"ingested": results, "total_chunks": total_chunks,
                "collection": "alvitur_laws_v1", "model": "intfloat/multilingual-e5-large",
                "date": time.strftime("%Y-%m-%d")}
    Path("data/qdrant_store/ingest_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2))
    print()
    print("Manifest saved: data/qdrant_store/ingest_manifest.json")

if __name__ == "__main__":
    main()
