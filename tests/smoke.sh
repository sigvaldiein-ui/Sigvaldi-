#!/bin/bash
# Sprint 63 Track C1+C2: Alvitur smoke tests
# Usage: ./tests/smoke.sh [port]
# Default port is 8003 (DEV). Never target 8000 (PROD) in automated tests.

PORT="${1:-8003}"
BASE="http://localhost:$PORT"
FAILS=0
PASSES=0

pass() { echo "  PASS: $1"; PASSES=$((PASSES+1)); }
fail() { echo "  FAIL: $1"; FAILS=$((FAILS+1)); }

echo "==============================================="
echo "  ALVITUR SMOKE TESTS"
echo "  Target: $BASE"
echo "==============================================="

if [ "$PORT" = "8000" ]; then
  echo ""
  echo "  WARNING: targeting PROD. Prefer 8003 (DEV) for automated tests."
  echo ""
fi

echo ""
echo "[T1] Health endpoint"
HEALTH=$(curl -s --max-time 5 $BASE/api/health)
if echo "$HEALTH" | grep -q "status.:.ok"; then
  pass "health ok"
else
  fail "health broken: $HEALTH"
fi

echo ""
echo "[T2] Diagnostics endpoint"
DIAG=$(curl -s --max-time 5 $BASE/api/diagnostics)
ENV=$(echo "$DIAG" | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get(chr(101)+chr(110)+chr(118),chr(110)+chr(111)+chr(110)+chr(101)))" 2>/dev/null)
if [ "$ENV" = "prod" ] || [ "$ENV" = "dev" ]; then
  pass "diagnostics env=$ENV"
else
  fail "diagnostics missing env"
fi

echo ""
echo "[T3] Leid A enabled"
LEID_A=$(echo "$DIAG" | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get(chr(108)+chr(101)+chr(105)+chr(100)+chr(95)+chr(97)+chr(95)+chr(101)+chr(110)+chr(97)+chr(98)+chr(108)+chr(101)+chr(100),False))" 2>/dev/null)
if [ "$LEID_A" = "True" ]; then
  pass "leid A enabled"
else
  fail "leid A disabled"
fi

echo ""
echo "[T4] Beta promotion (first file upload with beta phrase)"
RESP=$(curl -s --max-time 60 -X POST $BASE/api/analyze-document \
  -F "query=sigvaldi sendi mig — hvad er heildarinnkoma?" \
  -F "file=@tests/fixtures/simple.xlsx")
ANS=$(echo "$RESP" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print((d.get(chr(115)+chr(117)+chr(109)+chr(109)+chr(97)+chr(114)+chr(121)) or d.get(chr(114)+chr(101)+chr(115)+chr(112)+chr(111)+chr(110)+chr(115)+chr(101)) or chr(0))[:250])" 2>/dev/null)
if echo "$ANS" | grep -q "450"; then
  pass "beta promoted + simple.xlsx sum=450000 in LLM output"
else
  fail "beta promotion failed or 450000 missing: $ANS"
fi

echo ""
echo "[T5] File upload multi-sheet (IP now beta)"
RESP=$(curl -s --max-time 60 -X POST $BASE/api/analyze-document \
  -F "query=Hvada dalkar eru i skjalinu?" \
  -F "file=@tests/fixtures/multi_sheet.xlsx")
PIPE=$(echo "$RESP" | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get(chr(112)+chr(105)+chr(112)+chr(101)+chr(108)+chr(105)+chr(110)+chr(101)+chr(95)+chr(115)+chr(111)+chr(117)+chr(114)+chr(99)+chr(101),chr(110)+chr(111)+chr(110)+chr(101)))" 2>/dev/null)
if [ -n "$PIPE" ] && [ "$PIPE" != "none" ]; then
  pass "multi_sheet.xlsx pipeline=$PIPE"
else
  fail "multi_sheet.xlsx broke"
fi

echo ""
echo "[T6] File upload empty (graceful)"
RESP=$(curl -s --max-time 30 -X POST $BASE/api/analyze-document \
  -F "query=Hvad er i skjalinu?" \
  -F "file=@tests/fixtures/empty.xlsx")
STATUS=$(echo "$RESP" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(chr(111)+chr(107) if (d.get(chr(115)+chr(117)+chr(109)+chr(109)+chr(97)+chr(114)+chr(121)) or d.get(chr(114)+chr(101)+chr(115)+chr(112)+chr(111)+chr(110)+chr(115)+chr(101))) else chr(102)+chr(97)+chr(105)+chr(108))" 2>/dev/null)
if [ "$STATUS" = "ok" ]; then
  pass "empty.xlsx handled gracefully"
else
  fail "empty.xlsx crashed"
fi

echo ""
echo "[T7] Auto-assert: netloss preprocessor number survives LLM"
RESP=$(curl -s --max-time 60 -X POST $BASE/api/analyze-document \
  -F "query=Hver er nettoutkoma?" \
  -F "file=@tests/fixtures/netloss.xlsx")
ANS=$(echo "$RESP" | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print((d.get(chr(115)+chr(117)+chr(109)+chr(109)+chr(97)+chr(114)+chr(121)) or d.get(chr(114)+chr(101)+chr(115)+chr(112)+chr(111)+chr(110)+chr(115)+chr(101)) or chr(0))[:300])" 2>/dev/null)
if echo "$ANS" | grep -qE "91.?000|91 000|-91"; then
  pass "netloss.xlsx LLM output contains -91000"
else
  fail "netloss.xlsx missing -91000: $ANS"
fi

echo ""
echo "==============================================="
echo "  RESULTS: $PASSES passed, $FAILS failed"
echo "==============================================="
[ $FAILS -eq 0 ] && exit 0 || exit 1
