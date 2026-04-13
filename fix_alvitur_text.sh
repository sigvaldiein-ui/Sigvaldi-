#!/bin/bash
# ============================================================
# ALVITUR.IS — LEIÐRÉTTING Á ÍSLENSKU TEXTA
# Keyra á RunPod Terminal í /workspace/mimir_net/
# Dagsetning: 6. apríl 2026
# ============================================================

set -e

TARGET="/workspace/mimir_net/interfaces/web_server.py"

# --- 0. AFRIT ---
echo "📦 Bý til afrit..."
cp "$TARGET" "${TARGET}.bak_textaleidrett_$(date +%Y%m%d_%H%M%S)"
echo "   ✅ Afrit vistað: ${TARGET}.bak_textaleidrett_$(date +%Y%m%d_%H%M%S)"

# --- 1. BEYGINGARVILLUR OG STAFSETNING ---
echo ""
echo "🔧 Leiðrétti beygingarvillur og stafsetningu..."

# 1. "Telegram appið" → "Telegram-appið"
sed -i 's/Telegram appið/Telegram-appið/g' "$TARGET"

# 2. "Dragtu PDF skjöl hér" → "Dragðu PDF-skjöl hingað"
sed -i 's/Dragtu PDF skjöl hér/Dragðu PDF-skjöl hingað/g' "$TARGET"

# 3. "strengustu evrópskum" → "ströngustu evrópskum"
sed -i 's/strengustu evrópskum/ströngustu evrópskum/g' "$TARGET"

# 4. "er byggt á staðbundnum" → "er byggð á staðbundnum" (Alvitur = kvk.)
sed -i 's/Alvitur er byggt á staðbundnum/Alvitur er byggð á staðbundnum/g' "$TARGET"

# 5. "Full samræmi" → "Fullt samræmi"
sed -i 's/Full samræmi/Fullt samræmi/g' "$TARGET"

# 6. "Lokuð Gagnaherbergi" → "Lokuð gagnaherbergi"  (fyrirsögn)
sed -i 's/Lokuð Gagnaherbergi/Lokuð gagnaherbergi/g' "$TARGET"

# 7. "eyða óteljandi tímum" → "verja ómældum tíma"
sed -i 's/eyða óteljandi tímum/verja ómældum tíma/g' "$TARGET"

# 8. "á undir 90 sek" → "á innan við 90 sek"
sed -i 's/á undir 90 sek/á innan við 90 sek/g' "$TARGET"

# 9. "ekkert þýðingarþröskuldur" → "enginn þýðingarþröskuldur"
sed -i 's/ekkert þýðingarþröskuldur/enginn þýðingarþröskuldur/g' "$TARGET"

# 10. "íslensku málskilning" → "íslenskan málskilning" (þolfall kk.)
sed -i 's/íslensku málskilning/íslenskan málskilning/g' "$TARGET"

# 11. "Gervigreindarsveimur sem sameinar...sérhæfður" → "Gervigreindarkerfi sem sameinar...sérhæft"
sed -i 's/Gervigreindarsveimur sem sameinar skjalagreiningu, lagaleit og íslenskan málskilning — sérhæfður/Gervigreindarkerfi sem sameinar skjalagreiningu, lagaleit og íslenskan málskilning — sérhæft/g' "$TARGET"

# 12. "PDF, Word eða Excel skjölum" → "PDF-, Word- eða Excel-skjölum"
sed -i 's/PDF, Word eða Excel skjölum/PDF-, Word- eða Excel-skjölum/g' "$TARGET"

# 13. "due diligence og samningsrýni" → "áreiðanleikakönnun og samningsrýni"
sed -i 's/due diligence og samningsrýni/áreiðanleikakönnun og samningsrýni/g' "$TARGET"

# 14. "due diligence á samningum" → "áreiðanleikakönnun á samningum" (í umsögn)
sed -i 's/due diligence á samningum/áreiðanleikakönnun á samningum/g' "$TARGET"

# 15. "KPI greiningu, þróunargreiningur og" → "KPI-greiningu, þróunargreiningu og"
sed -i 's/KPI greiningu, þróunargreiningur og/KPI-greiningu, þróunargreiningu og/g' "$TARGET"

# 16. "Gull og Platínuáskrifendur" → "Gull- og platínuáskrifendur"
sed -i 's/Gull og Platínuáskrifendur/Gull- og platínuáskrifendur/g' "$TARGET"

# 17. "milli deilinga" → "milli deilda"
sed -i 's/milli deilinga/milli deilda/g' "$TARGET"

# 18. "greiningu á öruggan hátt" → "greiningum á öruggan hátt"
sed -i 's/greiningu á öruggan hátt/greiningum á öruggan hátt/g' "$TARGET"

# 19. "API aðgangur og samþætting" → "API-aðgangur og samþætting" (fyrirsögn)
sed -i 's/>API aðgangur og samþætting</>API-aðgangur og samþætting</g' "$TARGET"

# 20. "DMS eða innri" → "skjalastjórnunarkerfi eða innri"
sed -i 's/DMS eða innri/skjalastjórnunarkerfi eða innri/g' "$TARGET"

# 21. "prufuáskrift" → "prófunaráskrift"
sed -i 's/prufuáskrift/prófunaráskrift/g' "$TARGET"

# 22. "Íslenskt málskilningur" → "Íslenskur málskilningur"
sed -i 's/Íslenskt málskilningur/Íslenskur málskilningur/g' "$TARGET"

# 23. "deildar skriður" → "deildardrif"
sed -i 's/deildar skriður/deildardrif/g' "$TARGET"

# 24. "Pay-per-compute" → "Notkun á afkastareikningi"
sed -i 's/Pay-per-compute/Notkun á afkastareikningi/g' "$TARGET"

# 25. "nafnlægar vegna" → "nafnlausar vegna"
sed -i 's/nafnlægar vegna/nafnlausar vegna/g' "$TARGET"

# 26. "fær rétt í samningsákvæðin" → "fer rétt með samningsákvæðin"
sed -i 's/fær rétt í samningsákvæðin/fer rétt með samningsákvæðin/g' "$TARGET"

# 27. "Engin kreditkort. Engin binding. Hefjaðu" → "Ekkert kreditkort. Engin binding. Hefðu"
sed -i 's/Engin kreditkort\. Engin binding\. Hefjaðu/Ekkert kreditkort. Engin binding. Hefðu/g' "$TARGET"

# 28. "Zero-Data Policy" → "Zero-Data stefna" (fyrirsögn)
sed -i 's/Zero-Data Policy/Zero-Data stefna/g' "$TARGET"

# 29. "REST API aðgangur" → "REST API-aðgangur"  (í verðskrá)
sed -i 's/REST API aðgangur/REST API-aðgangur/g' "$TARGET"

# 30. Meta-tög: "gervigreindarsveimur" → "gervigreindarkerfi"
sed -i 's/Sérþjálfaður gervigreindarsveimur/Sérþjálfað gervigreindarkerfi/g' "$TARGET"

echo "   ✅ 30 leiðréttingar gerðar"

# --- 2. STAÐFESTING ---
echo ""
echo "🔍 Staðfesting — leita að eftirstandandi villum..."
ERRORS=0

check() {
  if grep -q "$1" "$TARGET"; then
    echo "   ⚠️  FINNST ENNÞÁ: $1"
    ERRORS=$((ERRORS + 1))
  else
    echo "   ✅ Lagað: $2"
  fi
}

check "Telegram appið" "Telegram-appið"
check "Dragtu PDF" "Dragðu PDF-skjöl"
check "strengustu evrópskum" "ströngustu"
check "er byggt á staðbundnum" "er byggð"
check "Full samræmi" "Fullt samræmi"
check "Lokuð Gagnaherbergi" "Lokuð gagnaherbergi"
check "óteljandi tímum" "ómældum tíma"
check "á undir 90" "á innan við 90"
check "ekkert þýðingarþröskuldur" "enginn þýðingarþröskuldur"
check "Íslenskt málskilningur" "Íslenskur málskilningur"
check "deildar skriður" "deildardrif"
check "nafnlægar vegna" "nafnlausar vegna"
check "fær rétt í samningsákvæðin" "fer rétt með"
check "þróunargreiningur og" "þróunargreiningu"

echo ""
if [ "$ERRORS" -eq 0 ]; then
  echo "✅ Allar leiðréttingar staðfestar!"
else
  echo "⚠️  $ERRORS villur enn eftir — athugaðu handvirkt."
fi

# --- 3. SYNTAX CHECK ---
echo ""
echo "🐍 Athuga Python syntax..."
if python3 -m py_compile "$TARGET"; then
  echo "   ✅ Python syntax í lagi"
else
  echo "   ❌ SYNTAX VILLA! Endurheimta afrit:"
  echo "   cp ${TARGET}.bak_textaleidrett_* $TARGET"
  exit 1
fi

# --- 4. ENDURRÆSA WEB SERVER ---
echo ""
echo "🔄 Endurræsi vefþjón..."
pkill -f "web_server" 2>/dev/null || true
sleep 2
cd /workspace/mimir_net/interfaces
nohup python3 -u web_server.py >> /workspace/web_server.log 2>&1 &
sleep 5

# --- 5. SMOKE TEST ---
echo ""
echo "🧪 Smoke test..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000)
if [ "$HTTP_CODE" = "200" ]; then
  echo "   ✅ HTTP 200 — síðan svarar"
else
  echo "   ❌ HTTP $HTTP_CODE — VANDAMÁL! Endurheimta afrit og endurræsa:"
  echo "   cp ${TARGET}.bak_textaleidrett_* $TARGET"
  echo "   pkill -f web_server; cd /workspace/mimir_net/interfaces; nohup python3 -u web_server.py >> /workspace/web_server.log 2>&1 &"
  exit 1
fi

# Athuga hvort leiðréttur texti birtist
if curl -s http://localhost:8000 | grep -q "ströngustu"; then
  echo "   ✅ Leiðréttur texti birtist á síðunni"
else
  echo "   ⚠️  Texti ekki fundinn — athugaðu handvirkt á alvitur.is"
fi

echo ""
echo "============================================"
echo "🏁 LOKIÐ! alvitur.is uppfærð með leiðréttum texta."
echo "   Afrit: ${TARGET}.bak_textaleidrett_*"
echo "   Endurheimta ef þarf: cp <afrit> $TARGET && pkill -f web_server && cd /workspace/mimir_net/interfaces && nohup python3 -u web_server.py >> /workspace/web_server.log 2>&1 &"
echo "============================================"
