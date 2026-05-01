# H.2 End-to-End Smoke Test Results

**Date:** 2026-04-25 04:42 UTC

## Summary
- Pass: 4
- Fail: 3
- Crash: 0
- Skip: 0

## Detailed Results

### 1_general_no_file
```json
{
  "test": "1_general_no_file",
  "tier": "general",
  "file": null,
  "query": "Hvað er höfuðborg Íslands?",
  "http_status": 200,
  "latency_s": 5.77,
  "response_len": 31,
  "response_sample": "Höfuðborg Íslands er Reykjavík.",
  "pipeline_source": "openrouter_gemini-3.1-pro-preview",
  "verdict": "pass"
}
```

### 2_general_excel_small
```json
{
  "test": "2_general_excel_small",
  "tier": "general",
  "file": "/tmp/test_small.xlsx",
  "query": "Greindu fjárhagslegu niðurstöðu úr þessu skjali",
  "http_status": 200,
  "latency_s": 18.9,
  "response_len": 452,
  "response_sample": "Ég finn ekki nógu nákvæmar upplýsingar í skjalinu til að svara spurningunni. Gögnin innihalda engar fyrirfram reiknaðar fjárhagslegar niðurstöður eða samtölur, heldur aðeins grunnlista yfir þrjár vörutegundir, magn þeirra og stykkaverð. Samkvæmt reglunum í skjalinu get ég ekki endurreiknað nýjar töl",
  "pipeline_source": "openrouter_gemini-3.1-pro-preview",
  "verdict": "pass"
}
```

### 3_vault_no_file
```json
{
  "test": "3_vault_no_file",
  "tier": "vault",
  "file": null,
  "query": "Útskýrðu lög nr. 145/1994 um bókhald í stuttu máli",
  "http_status": 200,
  "latency_s": 9.81,
  "response_len": 610,
  "response_sample": "Lög nr. 145/1994 um bókhald lýsir reglum um hvernig fyrirtæki og einstaklingar á að halda bókhaldi. Lögð eru fram kröfur um að bókhæstar á að vera réttar og fullnýjandi, svo að hægt sé að fá greiða upplýsingar um fjárhagsstæður og einkunni viðskiptavina.  \n\nLagið skilgreinir einnig aðferðir fyrir fj",
  "pipeline_source": "local_vllm_qwen3-32b-awq",
  "verdict": "pass"
}
```

### 4_vault_excel_small
```json
{
  "test": "4_vault_excel_small",
  "tier": "vault",
  "file": "/tmp/test_small.xlsx",
  "query": "Greindu trúnaðarmál úr þessu skjali",
  "http_status": 200,
  "latency_s": 5.28,
  "response_len": 319,
  "response_sample": "Þetta skjal sýnir upplýsingar um 3 vörur og tilheyrandi magn og verð. Í trúnaðarmáli má lýsa þessu sem einkaup af vörum, en ekki eru reiknaðar neinar samtölur eins og \"Samtals innheimt\" eða \"Samtals útborgun\". Því ekki eru reiknaðar neinar samtölur fyrirfram, get ég ekki gefið nánari trúnaðarmálsfræ",
  "pipeline_source": "local_vllm_qwen3-32b-awq",
  "verdict": "pass"
}
```

### 5_realtime_data
```json
{
  "test": "5_realtime_data",
  "tier": "general",
  "file": null,
  "query": "Hvað er klukkan í Reykjavík núna?",
  "http_status": 403,
  "latency_s": 0.06,
  "response_len": 224,
  "response_sample": "{'success': False, 'error': 'Ókeypis prufutími er liðinn.', 'error_code': 'quota_exceeded', 'upgrade_required': True, 'upgrade_url': '/askrift', 'message': 'Þú hefur nýtt þér 5 ókeypis beiðnir. Uppfærðu til að halda áfram.'}",
  "pipeline_source": "unknown",
  "verdict": "fail"
}
```

### 6_excel_sort
```json
{
  "test": "6_excel_sort",
  "tier": "general",
  "file": "/tmp/test_10_names.xlsx",
  "query": "Raðaðu nöfnunum í stafrófsröð",
  "http_status": 403,
  "latency_s": 0.06,
  "response_len": 224,
  "response_sample": "{'success': False, 'error': 'Ókeypis prufutími er liðinn.', 'error_code': 'quota_exceeded', 'upgrade_required': True, 'upgrade_url': '/askrift', 'message': 'Þú hefur nýtt þér 5 ókeypis beiðnir. Uppfærðu til að halda áfram.'}",
  "pipeline_source": "unknown",
  "verdict": "fail"
}
```

### 7_excel_46_names
```json
{
  "test": "7_excel_46_names",
  "tier": "general",
  "file": "/tmp/test_46_names.xlsx",
  "query": "Listaðu öll nöfnin í skjalinu",
  "http_status": 403,
  "latency_s": 0.06,
  "response_len": 224,
  "response_sample": "{'success': False, 'error': 'Ókeypis prufutími er liðinn.', 'error_code': 'quota_exceeded', 'upgrade_required': True, 'upgrade_url': '/askrift', 'message': 'Þú hefur nýtt þér 5 ókeypis beiðnir. Uppfærðu til að halda áfram.'}",
  "pipeline_source": "unknown",
  "verdict": "fail"
}
```

