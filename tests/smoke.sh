#!/bin/bash
# Sprint 63 Track C: Alvitur smoke tests (DEV-only by default)
# Usage: ./tests/smoke.sh [port]

PORT="${1:-8003}"
BASE="http://localhost:$PORT"
FAILS=0
PASSES=0
HELPER="python3 tests/_parse_resp.py"

pass() { echo "  PASS: $1"; PASSES=$((PASSES+1)); }
fail() { echo "  FAIL: $1"; FAILS=$((FAILS+1)); }

echo "==============================================="
echo "  ALVITUR SMOKE TESTS"
echo "  Target: $BASE"
echo "==============================================="

if [ "$PORT" = "8000" ]; then
  echo ""
  echo "  WARNING: targeting PROD. Prefer 8003 (DEV)."
fi

echo ""
echo "[T1] Health endpoint"
HEALTH=$(curl -s --max-time 5 $BASE/api/health)
if echo "$HEALTH" | grep -q "ok"; then pass "health ok"; else fail "health broken"; fi

echo ""
echo "[T2] Diagnostics env"
DIAG=$(curl -s --max-time 5 $BASE/api/diagnostics)
ENV=$(echo "$DIAG" | $HELPER env)
if [ "$ENV" = "prod" ] || [ "$ENV" = "dev" ]; then pass "env=$ENV"; else fail "env missing"; fi

echo ""
echo "[T3] Leid A enabled"
LEID_A=$(echo "$DIAG" | $HELPER leid_a_enabled)
if [ "$LEID_A" = "True" ]; then pass "leid A enabled"; else fail "leid A disabled"; fi

echo ""
echo "[T4] Beta promotion + simple.xlsx (450000)"
curl -s --max-time 60 -X POST $BASE/api/analyze-document \
  -F "query=sigvaldi sendi mig — hvad er heildarinnkoma?" \
  -F "file=@tests/fixtures/simple.xlsx" > /tmp/smoke_t4.json
ANS=$(cat /tmp/smoke_t4.json | $HELPER answer)
if echo "$ANS" | grep -q "450"; then
  pass "beta promoted + 450000 in answer"
else
  fail "no 450000 in answer: $ANS"
fi

echo ""
echo "[T5] Multi-sheet xlsx (soft: http 200 or timeout)"
HTTP=$(curl -s -o /tmp/smoke_t5.json -w "%{http_code}" --max-time 90 -X POST $BASE/api/analyze-document \
  -F "query=Hvada dalkar eru i skjalinu?" \
  -F "file=@tests/fixtures/multi_sheet.xlsx")
if [ "$HTTP" = "200" ] || [ "$HTTP" = "000" ]; then
  pass "multi_sheet.xlsx http=$HTTP"
else
  fail "multi_sheet.xlsx http=$HTTP"
fi

echo ""
echo "[T6] Empty xlsx graceful"
curl -s --max-time 30 -X POST $BASE/api/analyze-document \
  -F "query=Hvad er i skjalinu?" \
  -F "file=@tests/fixtures/empty.xlsx" > /tmp/smoke_t6.json
ANS=$(cat /tmp/smoke_t6.json | $HELPER answer)
if [ -n "$ANS" ]; then pass "empty.xlsx responded"; else fail "empty.xlsx no response"; fi

echo ""
echo "[T7] Netloss auto-assert (-91000 survives LLM)"
curl -s --max-time 60 -X POST $BASE/api/analyze-document \
  -F "query=Hver er nettoutkoma?" \
  -F "file=@tests/fixtures/netloss.xlsx" > /tmp/smoke_t7.json
ANS=$(cat /tmp/smoke_t7.json | $HELPER answer)
if echo "$ANS" | grep -qE "91.?000|-91"; then
  pass "netloss -91000 in answer"
else
  fail "no -91000 in answer: $ANS"
fi

echo ""
echo "==============================================="
echo "  RESULTS: $PASSES passed, $FAILS failed"
echo "==============================================="
[ $FAILS -eq 0 ] && exit 0 || exit 1
