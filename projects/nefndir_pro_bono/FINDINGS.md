# Empirical findings — stjornarradid.is/raduneyti/nefndir/

## Site arkitektúr (staðfest úr fyrri skrapi)
- Trjábygging með 4 megin flipum (Verkefni / Efst á baugi / Gögn / Ráðuneyti)
- AJAX stækkunarhlekkir með GUID-slóðum
- Mynstur: /raduneyti/nefndir/$Navigation/Index/?NavPageId=<GUID>&pageitemid=f0100282-44b1-11e7-941a-005056bc530c
- pageitemid er fast, NavPageId er einstakt fyrir hvern hnút

## Innri hnútur vs. laufhnútur
- Innri: texti byrjar á "Next level for [FLOKKUR]"
- Lauf: texti er nafn nefndar án "Next level for"

## Áætlað umfang
- ~500-1000 nefndir samtals
