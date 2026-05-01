"""H.2 End-to-end smoke test fyrir Alvitur production flow."""
import asyncio, httpx, json, time
from pathlib import Path

API_BASE = "http://localhost:8000"
SMALL_EXCEL = "/tmp/test_small.xlsx"
NAMES_10_EXCEL = "/tmp/test_10_names.xlsx"
NAMES_46_EXCEL = "/tmp/test_46_names.xlsx"

async def run_test(name, tier, query, file_path=None):
    headers = {"X-Alvitur-Tier": tier} if tier else {}
    files = None
    if file_path and Path(file_path).exists():
        files = {"file": (Path(file_path).name, open(file_path,"rb"),
                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{API_BASE}/api/analyze-document",
                                  data={"query": query}, files=files, headers=headers)
            elapsed = round(time.time()-t0, 2)
            try:
                body = r.json()
            except Exception:
                body = {"raw": r.text[:500]}
            resp = body.get("response") or body.get("answer") or str(body)[:300]
            verdict = "pass" if r.status_code==200 and len(str(resp))>20 else "fail"
            return {"test":name,"tier":tier,"file":file_path,"query":query,
                    "http_status":r.status_code,"latency_s":elapsed,
                    "response_len":len(str(resp)),"response_sample":str(resp)[:300],
                    "pipeline_source":body.get("pipeline_source","unknown"),
                    "verdict":verdict}
    except Exception as e:
        return {"test":name,"tier":tier,"query":query,
                "error":f"{type(e).__name__}: {e}","verdict":"crash"}

async def main():
    tests = [
        ("1_general_no_file",   "general", "Hvað er höfuðborg Íslands?", None),
        ("2_general_excel_small","general", "Greindu fjárhagslegu niðurstöðu úr þessu skjali", SMALL_EXCEL),
        ("3_vault_no_file",     "vault",   "Útskýrðu lög nr. 145/1994 um bókhald í stuttu máli", None),
        ("4_vault_excel_small", "vault",   "Greindu trúnaðarmál úr þessu skjali", SMALL_EXCEL),
        ("5_realtime_data",     "general", "Hvað er klukkan í Reykjavík núna?", None),
        ("6_excel_sort",        "general", "Raðaðu nöfnunum í stafrófsröð", NAMES_10_EXCEL),
        ("7_excel_46_names",    "general", "Listaðu öll nöfnin í skjalinu", NAMES_46_EXCEL),
    ]
    results = []
    for name,tier,query,fp in tests:
        print(f"\n=== {name} ===")
        if fp and not Path(fp).exists():
            print(f"  SKIP: {fp} not found")
            results.append({"test":name,"verdict":"skip","reason":"file missing"})
            continue
        r = await run_test(name,tier,query,fp)
        print(f"  HTTP:{r.get('http_status')} lat:{r.get('latency_s')}s verdict:{r.get('verdict')}")
        print(f"  src:{r.get('pipeline_source')} len:{r.get('response_len')}")
        print(f"  resp:{r.get('response_sample','')[:150]}")
        results.append(r)

    out = Path("docs/H2_SMOKE_TEST_RESULTS.md")
    passed  = sum(1 for r in results if r.get("verdict")=="pass")
    failed  = sum(1 for r in results if r.get("verdict")=="fail")
    crashed = sum(1 for r in results if r.get("verdict")=="crash")
    skipped = sum(1 for r in results if r.get("verdict")=="skip")
    with open(out,"w") as f:
        f.write("# H.2 End-to-End Smoke Test Results\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M UTC',time.gmtime())}\n\n")
        f.write(f"## Summary\n- Pass: {passed}\n- Fail: {failed}\n- Crash: {crashed}\n- Skip: {skipped}\n\n")
        f.write("## Detailed Results\n\n")
        for r in results:
            f.write(f"### {r.get('test')}\n```json\n{json.dumps(r,indent=2,ensure_ascii=False)}\n```\n\n")
    print(f"\nSummary: {passed} pass / {failed} fail / {crashed} crash / {skipped} skip")
    print(f"Results: {out}")

asyncio.run(main())
