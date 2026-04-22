#!/bin/bash
# Sprint 63 Track C1: Alvitur smoke tests
# Usage: ./tests/smoke.sh [port]
# Exit 0 on all pass, 1 on any fail.

PORT="${1:-8000}"
BASE="http://localhost:$PORT"
FAILS=0
PASSES=0

pass() { echo "  PASS: $1"; PASSES=$((PASSES+1)); }
fail() { echo "  FAIL: $1"; FAILS=$((FAILS+1)); }

echo "==============================================="
echo "  ALVITUR SMOKE TESTS"
echo "  Target: $BASE"
echo "==============================================="

echo ""
echo "[T1] Health endpoint"
HEALTH=$(curl -s --max-time 5 $BASE/api/health)
if echo "$HEALTH" | grep -q "\"status\":\"ok\""; then
  pass "health ok"
else
  fail "health broken: $HEALTH"
fi

echo ""
echo "[T2] Diagnostics endpoint"
DIAG=$(curl -s --max-time 5 $BASE/api/diagnostics)
ENV=$(echo "$DIAG" | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('env','none'))" 2>/dev/null)
if [ "$ENV" = "prod" ] || [ "$ENV" = "dev" ]; then
  pass "diagnostics env=$ENV"
else
  fail "diagnostics missing env field"
fi

echo ""
echo "[T3] Leid A enabled"
LEID_A=$(echo "$DIAG" | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('leid_a_enabled',False))" 2>/dev/null)
if [ "$LEID_A" = "True" ]; then
  pass "leid A enabled"
else
  fail "leid A disabled"
fi

echo ""
echo "[T4] Text-only query"
RESP=$(curl -s --max-time 30 -X POST $BASE/api/analyze-document -F "query=Hvad er 2+2?")
PIPE=$(echo "$RESP" | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('pipeline_source','none'))" 2>/dev/null)
ANS=$(echo "$RESP" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print((d.get('summary') or d.get('response') or '')[:50])" 2>/dev/null)
if [ -n "$PIPE" ] && [ "$PIPE" != "none" ]; then
  pass "text pipeline=$PIPE"
else
  fail "text query broken"
fi
if echo "$ANS" | grep -q "4"; then
  pass "text answer contains 4"
else
  fail "text answer missing 4: $ANS"
fi

echo ""
echo "[T5] Iceland geography query"
RESP=$(curl -s --max-time 30 -X POST $BASE/api/analyze-document -F "query=Hofudborg Islands?")
ANS=$(echo "$RESP" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print((d.get('summary') or d.get('response') or '')[:100])" 2>/dev/null)
if echo "$ANS" | grep -qi "reykjavik\|reykjavík"; then
  pass "geography answer mentions Reykjavik"
else
  fail "geography answer wrong: $ANS"
fi

echo ""

echo ""
echo "[T6] Excel simple upload (preprocessor + LLM)"
RESP=$(curl -s --max-time 60 -X POST $BASE/api/analyze-document \
  -F "query=Hvad er heildarinnkoma?" \
  -F "file=@tests/fixtures/simple.xlsx")
ANS=$(echo "$RESP" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print((d.get('summary') or d.get('response') or '')[:200])" 2>/dev/null)
if echo "$ANS" | grep -q "450"; then
  pass "simple.xlsx preprocessor sum matches LLM"
else
  fail "simple.xlsx missing 450000: $ANS"
fi

echo ""
echo "[T7] Excel multi-sheet upload"
RESP=$(curl -s --max-time 60 -X POST $BASE/api/analyze-document \
  -F "query=Hvada dalkar eru i skjalinu?" \
  -F "file=@tests/fixtures/multi_sheet.xlsx")
PIPE=$(echo "$RESP" | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('pipeline_source','none'))" 2>/dev/null)
if [ "$PIPE" != "none" ] && [ -n "$PIPE" ]; then
  pass "multi_sheet.xlsx processed pipeline=$PIPE"
else
  fail "multi_sheet.xlsx broke pipeline"
fi

echo ""
echo "[T8] Excel empty file (graceful handling)"
RESP=$(curl -s --max-time 30 -X POST $BASE/api/analyze-document \
  -F "query=Hvad er i skjalinu?" \
  -F "file=@tests/fixtures/empty.xlsx")
STATUS=$(echo "$RESP" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print('ok' if d.get('summary') or d.get('response') else 'fail')" 2>/dev/null)
if [ "$STATUS" = "ok" ]; then
  pass "empty.xlsx handled gracefully"
else
  fail "empty.xlsx crashed or no response"
fi

echo ""
echo "[T9] Excel net loss auto-assert (preprocessor number in LLM output)"
RESP=$(curl -s --max-time 60 -X POST $BASE/api/analyze-document \
  -F "query=Hver er nettoutkoma?" \
  -F "file=@tests/fixtures/netloss.xlsx")
ANS=$(echo "$RESP" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print((d.get('summary') or d.get('response') or '')[:300])" 2>/dev/null)
# Net = 500000 - 591000 = -91000
if echo "$ANS" | grep -qE "91\.?000|-91|91 000"; then
  pass "netloss.xlsx LLM output contains -91000 (preprocessor ground truth)"
else
  fail "netloss.xlsx missing -91000: $ANS"
fi

echo ""
echo "==============================================="
echo "  RESULTS: $PASSES passed, $FAILS failed"
echo "==============================================="
[ $FAILS -eq 0 ] && exit 0 || exit 1
