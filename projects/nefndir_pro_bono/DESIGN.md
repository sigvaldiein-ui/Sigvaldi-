# Sprint Nefndir – Hönnunarskjal

## 1. áfangi: Uppgötvun trés (3-4 klst)
- Endurkvæmur skanni frá rót /raduneyti/nefndir/
- Fyrir hvern hnút: sækja síðu, draga út stækkunarhlekki
- Byggja upp heilt tré í JSON
- Vista sem tree.json (hægt að hefja aftur ef hrun verður)

## 2. áfangi: Útdráttur laufa (2-3 klst)
- Finna alla laufhnúta í tree.json
- Fyrir hvern laufhnút: sækja síðu, draga út nafn, ráðuneyti, formann, nefndarmenn, lagagrundvöll
- Vista sem nefndir.json

## 3. áfangi: RAG auðgun (1-2 klst)
- Fyrir hverja nefnd: leita í Qdrant með lagatexta
- Fá 3 bestu samsvörunina
- Bæta tilvitnunum við nefndir.json

## 4. áfangi: Wayback söguleg gögn (3-4 klst)
- Sækja https://web.archive.org/web/<tími>/<url>
- 5 tímapunktar yfir 5 ár (2021-2026)
- Mismunur á kynjahlutfalli yfir tíma

## 5. áfangi: HTML skýrsla (2 klst)
- Samsvörun við sniðmát Vigfúsar (kynjahlutfall, tegund, ráðuneyti)
- Plotly gröf, fellivalmyndir (vanilla JS)

## Samtals: 11-15 klst
## Bindandi: Reynslugátt milli hvers áfanga
