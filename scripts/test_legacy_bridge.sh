#!/bin/bash
# Test the Alvitur Legacy Bridge with a sample AS/400 string
curl -s http://localhost:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/workspace/models/qwen3-32b-awq",
    "messages": [
      {
        "role": "system",
        "content": "Þú ert sérfræðingur í að umbreyta íslenskum IBM AS/400 legacy gögnum í JSON. Þú skilar AÐEINS hreinu JSON, án nokkurs annars texta. EKKI nota <think> taggið. Skilaðu JSON í nákvæmlega þessu formi: {\"transaction_id\": \"0001\", \"type\": \"debit\", \"date\": \"2026-01-01\", \"amount\": {\"value\": 500.00, \"currency\": \"ISK\"}, \"description\": \"Vinnu laun\", \"counterparty\": {\"name\": \"Orkuskipti ehf\", \"kennitala\": \"5109190330\"}, \"status\": \"completed\"}. Breyttu dagsetningum í ISO form (YYYY-MM-DD), upphæðum í tölur (ekki strengi með núllum), og dragðu kennitölu og nafn út úr lýsingunni í counterparty hlutinn."
      },
      {
        "role": "user",
        "content": "Umbreyttu þessum íslenska AS/400 bankafærslustreng í JSON:\n\n0001KAUF 2026010100000001234567890000050000ISK0000000000VINNU LAUN ORKUSKIPTI EHF KT5109190330"
      }
    ],
    "max_tokens": 2000,
    "temperature": 0.0
  }' | python3 -c "
import sys, json, re
data = json.load(sys.stdin)
content = data['choices'][0]['message']['content']
cleaned = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
print(cleaned)
"
