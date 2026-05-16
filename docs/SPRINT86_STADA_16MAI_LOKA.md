# Sprint 86 — Lokaskýrsla 16. maí 2026

## Klárað í dag

| Verk | Staða |
|------|-------|
| Alþingi XML API | ✅ Virkt og staðfest með tilvitnunum |
| Vísindavefur HÍ (lifandi leit) | ✅ Virkt, samþætt í RRF keðju |
| Qdrant safnsnafn lagað | ✅ `alvitur_laws_v2` virkt |
| SearchLawTool tengt við rétt safn | ✅ Empirical prófað |

## Empirical sönnun

- `"Hvað er fjárlög 2026?"` → Alþingi tilvitnun staðfest
- `"Hvað er hantaveira?"` → Vísindavefur tilvitnun staðfest

## Gagnagjafar sem reyndust ónothæfir

| Gjafi | Ástæða |
|-------|--------|
| Seðlabanki NSDP | API svarar ekki |
| Hagstofa PX-Web | Flókin slóðagerð |
| Personuvernd.is | Redirect á island.is |
| Dómstólar RSS | Redirect á island.is |

## Næstu skref

1. Rannsaka Hagstofu PX-Web betur
2. Skoða reglugerd.is
3. Dýpka Vísindavef með leitarsíðu-scrapi
