#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
althingi_collector.py — Mímir gagnasöfnunarkerfi
=================================================
Sækir íslenskt textaefni frá opnu XML API Alþingis til þjálfunar á máltæknilíkönum.

API grunnslóð: https://www.althingi.is/altext/xml/

Uppbygging:
  saekja_raedur()   — Ræðulisti síðustu N daga
  saekja_thingmal() — Þingmálalisti tiltekinna þings
  saekja_dagskra()  — Dagskrá næsta þingfundar
  vista_jsonl()     — Vistar gögn í JSONL skrá
  keyra()           — Aðalfall sem kallar á allt

Höfundur: Mímir gagnasöfnunarkerfi
"""

import os
import json
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Stillingar
# ---------------------------------------------------------------------------

# Grunnslóð Alþingis XML API
API_GRUNNSLOD = "https://www.althingi.is/altext/xml"

# Útgáfumappa — algild slóð samkvæmt SOP v5.0
GAGNSMAPPA = "/home/user/workspace/mimir_net/data"

# Nafnrými í ræðu-XML skjölum (þarf til þáttunnar)
RAEDA_NAFNARYMI = "http://skema.althingi.is/skema"

# Biðtími á milli beiðna (kurteisi gagnvart þjóni)
BIDTIMI = 1.0

# Fyrirsögn HTTP beiðna
HEADERS = {
    "User-Agent": "Mimir-Gagnasoefnun/1.0 (menntaverkefni; althingi@mimir.is)"
}


# ---------------------------------------------------------------------------
# Hjálparföll
# ---------------------------------------------------------------------------

def _saekja_xml(slod: str) -> ET.Element | None:
    """
    Sækir XML skjal frá gefnum URL og skilar rótareiningu.
    Skilar None ef villa kemur upp eða þáttun mistekst.
    """
    try:
        svar = requests.get(slod, headers=HEADERS, timeout=30)
        svar.raise_for_status()
        # Althingi API notar stundum ISO-8859-1 og stundum UTF-8
        # requests gætir lesið encoding vitlægt; notum raw content
        efni = svar.content
        try:
            rot = ET.fromstring(efni)
        except ET.ParseError as e:
            print(f"  [VIÐVÖRUN] XML þáttun mistókst fyrir {slod}: {e}")
            return None
        return rot
    except requests.exceptions.Timeout:
        print(f"  [VILLA] Tímamörk (timeout) við sótt {slod}")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"  [VILLA] Tengingarvilll við {slod}: {e}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"  [VILLA] HTTP villa við {slod}: {e}")
        return None
    except Exception as e:
        print(f"  [VILLA] Óvænt villa við {slod}: {e}")
        return None


def _saekja_raedutexta(xml_slod: str) -> str:
    """
    Sækir texta einnar ræðu úr XML ræðuskjali.
    Ræðurnar eru í sérstaklegu XML sniði með nafnarými.
    Skilar tómum streng ef villa kemur upp.
    """
    if not xml_slod:
        return ""

    # Tryggja HTTPS
    xml_slod = xml_slod.replace("http://", "https://")

    try:
        svar = requests.get(xml_slod, headers=HEADERS, timeout=30)
        svar.raise_for_status()
        efni = svar.content

        try:
            rot = ET.fromstring(efni)
        except ET.ParseError as e:
            print(f"    [VIÐVÖRUN] Gat ekki þáttað ræðutexta {xml_slod}: {e}")
            return ""

        # Nafnarými er "http://skema.althingi.is/skema"
        ns = {"ns": RAEDA_NAFNARYMI}

        # Safna öllum textalínum úr <ns:ræðutexti> > <ns:mgr>
        textalinur = []
        raedutexti = rot.find("ns:ræðutexti", ns)
        if raedutexti is not None:
            for mgr in raedutexti.findall("ns:mgr", ns):
                # itertext() fær allt texta þar með innfelldar einingar
                lina = "".join(mgr.itertext()).strip()
                if lina:
                    textalinur.append(lina)

        return "\n\n".join(textalinur)

    except requests.exceptions.Timeout:
        print(f"    [VILLA] Tímamörk við sótt ræðutexta {xml_slod}")
        return ""
    except requests.exceptions.ConnectionError as e:
        print(f"    [VILLA] Tengingarvilll við ræðutexta {xml_slod}: {e}")
        return ""
    except requests.exceptions.HTTPError as e:
        print(f"    [VILLA] HTTP villa við ræðutexta {xml_slod}: {e}")
        return ""
    except Exception as e:
        print(f"    [VILLA] Óvænt villa við ræðutexta {xml_slod}: {e}")
        return ""


def _dagsetning_til_iso(dagur_strengur: str) -> str:
    """
    Umbreytir dagsetningarstreng á mismunandi sniðum í ISO 8601 (YYYY-MM-DD).
    Styður: DD.MM.YYYY, YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS
    Skilar upprunalegar streng óbreyttan ef umbreyting mistekst.
    """
    if not dagur_strengur:
        return ""

    # Athuga ISO snið fyrst (YYYY-MM-DD eða YYYY-MM-DDTHH:MM:SS)
    if len(dagur_strengur) >= 10 and dagur_strengur[4] == "-":
        return dagur_strengur[:10]

    # DD.MM.YYYY snið (notað í ræðulista Alþingis)
    if "." in dagur_strengur:
        hlutar = dagur_strengur.split(".")
        if len(hlutar) == 3:
            try:
                dagur, manudur, ar = hlutar
                return f"{ar.strip()}-{manudur.strip().zfill(2)}-{dagur.strip().zfill(2)}"
            except (ValueError, IndexError):
                pass

    return dagur_strengur


# ---------------------------------------------------------------------------
# Aðalföll gagnasöfnunar
# ---------------------------------------------------------------------------

def saekja_raedur(dagar: int = 100) -> list:
    """
    Sækir ræður frá Alþingi síðustu N daga.

    Notar: GET /altext/xml/raedulisti/?dagar=N
    Sækir einnig fullan texta hverrar ræðu úr xml-hlekk ræðunnar.

    Skilar lista af dict með reitunum:
      source, type, text, date, speaker, topic, collected_at
    """
    print(f"Sæki ræður síðustu {dagar} daga...")

    slod = f"{API_GRUNNSLOD}/raedulisti/?dagar={dagar}"
    rot = _saekja_xml(slod)

    if rot is None:
        print("  [VILLA] Gat ekki sótt ræðulista.")
        return []

    raedur_gogn = []
    raedur_xml = rot.findall("ræða")
    print(f"  Fann {len(raedur_xml)} ræður í lista...")

    soefnud = 0
    for i, raeda in enumerate(raedur_xml):
        # --- Lýsigögn ræðu ---

        # Ræðumaður
        raedumadur_el = raeda.find("ræðumaður")
        raedumadur = ""
        if raedumadur_el is not None:
            nafn_el = raedumadur_el.find("nafn")
            if nafn_el is not None and nafn_el.text:
                raedumadur = nafn_el.text.strip()

        # Dagsetning
        dagur_el = raeda.find("dagur")
        dagur_strengur = dagur_el.text.strip() if (dagur_el is not None and dagur_el.text) else ""
        dagur_iso = _dagsetning_til_iso(dagur_strengur)

        # Efni/mál
        efni = ""
        mal_el = raeda.find("mál")
        if mal_el is not None:
            heiti_el = mal_el.find("málsheiti")
            if heiti_el is not None and heiti_el.text:
                efni = heiti_el.text.strip()

        # XML slóð ræðutexta (til að sækja fullan texta)
        xml_raedutexti_slod = ""
        slodirEl = raeda.find("slóðir")
        if slodirEl is not None:
            xml_el = slodirEl.find("xml")
            if xml_el is not None and xml_el.text:
                xml_raedutexti_slod = xml_el.text.strip()

        # --- Sækja fullan texta ræðu ---
        raedutexti = ""
        if xml_raedutexti_slod:
            raedutexti = _saekja_raedutexta(xml_raedutexti_slod)
            time.sleep(BIDTIMI)  # Kurteisi gagnvart þjóni

        # Sía út ræður með tóman texta
        if not raedutexti.strip():
            continue

        # Búa til JSONL færslu
        faersla = {
            "source": "althingi",
            "type": "raeda",
            "text": raedutexti,
            "date": dagur_iso,
            "speaker": raedumadur,
            "topic": efni,
            "collected_at": datetime.now().isoformat()
        }
        raedur_gogn.append(faersla)
        soefnud += 1

        # Prenta framvindu á 10 frests bilum
        if (i + 1) % 10 == 0:
            print(f"  ... {i + 1}/{len(raedur_xml)} ræður afgreiddar, {soefnud} með texta")

    print(f"Fann {soefnud} ræður með texta (af {len(raedur_xml)} í lista).")
    return raedur_gogn


def saekja_thingmal(lthing: int = 145) -> list:
    """
    Sækir þingmálalista tiltekins löggjafarþings.

    Notar: GET /altext/xml/thingmalalisti/?lthing=N

    Skilar lista af dict með reitunum:
      source, type, text, date, speaker, topic, collected_at

    Athugið: Þingmálalisti hefur ekki dagsetningar eða ræðumenn;
    texti er settur saman úr málsheiti og efnisgreiningu.
    """
    print(f"Sæki þingmálalista {lthing}. þings...")

    slod = f"{API_GRUNNSLOD}/thingmalalisti/?lthing={lthing}"
    rot = _saekja_xml(slod)

    if rot is None:
        print("  [VILLA] Gat ekki sótt þingmálalista.")
        return []

    mal_gogn = []
    mal_xml = rot.findall("mál")
    print(f"  Fann {len(mal_xml)} þingmál...")

    for mal in mal_xml:
        # Málsheiti
        heiti_el = mal.find("málsheiti")
        heiti = heiti_el.text.strip() if (heiti_el is not None and heiti_el.text) else ""

        # Efnisgreining (undirheiti/lýsing)
        eing_el = mal.find("efnisgreining")
        efnisgreining = eing_el.text.strip() if (eing_el is not None and eing_el.text) else ""

        # Málstegund (Frumvarp til laga, Tillaga o.fl.)
        tegund_el = mal.find("málstegund")
        tegund = ""
        if tegund_el is not None:
            heiti2_el = tegund_el.find("heiti")
            if heiti2_el is not None and heiti2_el.text:
                tegund = heiti2_el.text.strip()

        # Málsnúmer og þingnúmer úr attributes
        malsnumer = mal.get("málsnúmer", "")
        thingnumer = mal.get("þingnúmer", "")

        # Setja saman lýsandi texta
        textalisti = []
        if heiti:
            textalisti.append(heiti)
        if efnisgreining:
            textalisti.append(efnisgreining)
        if tegund:
            textalisti.append(f"Tegund: {tegund}")
        if malsnumer:
            textalisti.append(f"Málsnúmer: {malsnumer} ({thingnumer}. þing)")

        texti = " — ".join(textalisti)

        # Sía út tóman texta
        if not texti.strip():
            continue

        faersla = {
            "source": "althingi",
            "type": "thingmal",
            "text": texti,
            "date": "",            # Þingmálalisti hefur ekki dagsetningar
            "speaker": "",         # Ekki við á hér
            "topic": heiti,
            "collected_at": datetime.now().isoformat()
        }
        mal_gogn.append(faersla)

    print(f"Fann {len(mal_gogn)} þingmál með texta.")
    time.sleep(BIDTIMI)  # Kurteisi gagnvart þjóni
    return mal_gogn


def saekja_dagskra() -> list:
    """
    Sækir dagskrá næsta þingfundar.

    Notar: GET /altext/xml/thingfundir/?lthing=N til að finna
    yfirstandandi þing og næsta fund, síðan sækir dagskrána með:
    GET /altext/xml/dagskra/thingfundur/?lthing=N&fundur=M

    Skilar lista af dict með reitunum:
      source, type, text, date, speaker, topic, collected_at
    """
    print("Sæki dagskrá þingfundar...")

    # Finna yfirstandandi þing
    try:
        lthing_slod = f"{API_GRUNNSLOD}/loggjafarthing/yfirstandandi/"
        rot_lthing = _saekja_xml(lthing_slod)
        lthing_numer = None

        if rot_lthing is not None:
            # Yfirstandandi þing — finna þingnúmer
            lthing_el = rot_lthing.find("löggjafarþing")
            if lthing_el is None:
                # Prófa annað tag-nafn
                lthing_el = rot_lthing.find("þing")
            if lthing_el is not None:
                numer_attr = lthing_el.get("númer") or lthing_el.get("numer")
                if numer_attr:
                    lthing_numer = int(numer_attr)
                elif lthing_el.text and lthing_el.text.strip().isdigit():
                    lthing_numer = int(lthing_el.text.strip())

        if lthing_numer is None:
            # Nota þekkt gildi ef API skilar engu
            lthing_numer = 157
            print(f"  [ATHUGASEMD] Gat ekki lesið þingnúmer, nota {lthing_numer}")

    except Exception as e:
        lthing_numer = 157
        print(f"  [VIÐVÖRUN] Villa við að finna þingnúmer: {e} — nota {lthing_numer}")

    time.sleep(BIDTIMI)

    # Sækja þingfundalista til að finna næsta fund
    fundalisti_slod = f"{API_GRUNNSLOD}/thingfundir/?lthing={lthing_numer}"
    rot_fundir = _saekja_xml(fundalisti_slod)

    if rot_fundir is None:
        print("  [VILLA] Gat ekki sótt þingfundalista.")
        return []

    time.sleep(BIDTIMI)

    # Finna næsta fund (síðast skráður fundur)
    thingfundir = rot_fundir.findall("þingfundur")
    if not thingfundir:
        print("  [VILLA] Engir þingfundir fundust.")
        return []

    # Taka síðasta fund (hæsta númer = nýjasti)
    naesti_fundur = thingfundir[-1]
    fundur_numer = naesti_fundur.get("númer") or naesti_fundur.get("numer", "1")

    # Finna fund sem hefur ekki lokið (fuslit er tómt) ef mögulegt
    for fundur in reversed(thingfundir):
        fuslit_el = fundur.find("fuslit")
        if fuslit_el is None or not fuslit_el.text:
            # Þessi fundur hefur ekki lokið — líklega næsti fundur
            fundur_numer = fundur.get("númer") or fundur.get("numer", fundur_numer)
            break

    print(f"  Sæki dagskrá fundar {fundur_numer} á {lthing_numer}. þingi...")

    # Sækja dagskrá þessa fundar
    dagskra_slod = f"{API_GRUNNSLOD}/dagskra/thingfundur/?lthing={lthing_numer}&fundur={fundur_numer}"
    rot_dagskra = _saekja_xml(dagskra_slod)

    if rot_dagskra is None:
        print("  [VILLA] Gat ekki sótt dagskrá.")
        return []

    time.sleep(BIDTIMI)

    # Lesa dagskrárliðir
    dagskra_gogn = []

    # Finna þingfund element (gæti verið beint í rót eða undir <þingfundur>)
    thingfundur_el = rot_dagskra.find("þingfundur")
    if thingfundur_el is None:
        thingfundur_el = rot_dagskra

    # Finna upphafsdagsetningu fundarins
    dagur_fundar = ""
    hefst_el = thingfundur_el.find("hefst")
    if hefst_el is not None:
        dagurtimi_el = hefst_el.find("dagurtími")
        if dagurtimi_el is not None and dagurtimi_el.text:
            dagur_fundar = _dagsetning_til_iso(dagurtimi_el.text.strip())
        else:
            dagur_el = hefst_el.find("dagur")
            if dagur_el is not None and dagur_el.text:
                dagur_fundar = _dagsetning_til_iso(dagur_el.text.strip())

    # Lesa dagskrárliðina
    dagskra_el = thingfundur_el.find("dagskrá")
    if dagskra_el is None:
        # Ef engin dagskrá, leita í rót
        dagskra_el = rot_dagskra.find("dagskrá")

    if dagskra_el is not None:
        lidur_xml = dagskra_el.findall("dagskrárliður")
    else:
        # Prova beint á rót
        lidur_xml = rot_dagskra.findall("dagskrárliður")

    for lidur in lidur_xml:
        # Lesa málsupplýsingar
        mal_el = lidur.find("mál")
        if mal_el is None:
            continue

        heiti_el = mal_el.find("málsheiti")
        malheiti = heiti_el.text.strip() if (heiti_el is not None and heiti_el.text) else ""

        eing_el = mal_el.find("efnisgreining")
        efnisgreining = eing_el.text.strip() if (eing_el is not None and eing_el.text) else ""

        tegund_el = mal_el.find("málstegund")
        tegund = tegund_el.text.strip() if (tegund_el is not None and tegund_el.text) else ""

        umraeda_el = lidur.find("umræða")
        umraeda = umraeda_el.text.strip() if (umraeda_el is not None and umraeda_el.text) else ""

        # Dagskrárliðanúmer
        lid_numer = lidur.get("númer", "")

        # Setja saman texta
        textalisti = []
        if malheiti:
            textalisti.append(malheiti)
        if efnisgreining:
            textalisti.append(efnisgreining)
        if tegund:
            textalisti.append(f"Tegund: {tegund}")
        if umraeda:
            textalisti.append(f"Umræða: {umraeda}")
        if lid_numer:
            textalisti.append(f"Liður {lid_numer} á dagskrá {fundur_numer}. þingfundar")

        texti = " — ".join(textalisti)

        # Sía út tóman texta
        if not texti.strip():
            continue

        faersla = {
            "source": "althingi",
            "type": "dagskra",
            "text": texti,
            "date": dagur_fundar,
            "speaker": "",
            "topic": malheiti,
            "collected_at": datetime.now().isoformat()
        }
        dagskra_gogn.append(faersla)

    print(f"Fann {len(dagskra_gogn)} dagskrárliði.")
    return dagskra_gogn


# ---------------------------------------------------------------------------
# Geymsla
# ---------------------------------------------------------------------------

def vista_jsonl(gogn: list, slod: str) -> None:
    """
    Vistar lista af færslum í JSONL skrá (ein JSON-lína á færslu).
    Búa til möppur ef þær eru ekki til.

    Args:
        gogn: Listi af dict sem á að vista
        slod: Algild skráarslóð
    """
    if not gogn:
        print(f"  [ATHUGASEMD] Engin gögn til að vista í {slod}")
        return

    try:
        # Búa til möppur ef þær eru ekki til
        mappa = os.path.dirname(slod)
        if mappa:
            os.makedirs(mappa, exist_ok=True)

        # Skrifa JSONL
        with open(slod, "w", encoding="utf-8") as f:
            for faersla in gogn:
                lina = json.dumps(faersla, ensure_ascii=False)
                f.write(lina + "\n")

        print(f"Vistað {len(gogn)} færslur í {slod}")

    except OSError as e:
        print(f"  [VILLA] Gat ekki vistað í {slod}: {e}")
    except Exception as e:
        print(f"  [VILLA] Óvænt villa við vistun í {slod}: {e}")


# ---------------------------------------------------------------------------
# Aðalfall
# ---------------------------------------------------------------------------

def keyra() -> None:
    """
    Aðalfall Mímir gagnasöfnunarkerfis fyrir Alþingi.

    Framkvæmir:
      1. Sækir ræður síðustu 100 daga
      2. Sækir þingmálalista 145. þings
      3. Sækir dagskrá næsta þingfundar
      4. Vistar allt í JSONL skrá með dagsetningarnafni
    """
    print("=" * 60)
    print("Mímir — Alþingi gagnasöfnun")
    print(f"Hefst: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Búa til gagnamöppu
    os.makedirs(GAGNSMAPPA, exist_ok=True)

    # Skráarheiti með deginum (SOP v5.0)
    dagsetning_i_dag = datetime.now().strftime("%Y-%m-%d")
    skraarnafn = f"althingi_{dagsetning_i_dag}.jsonl"
    skraarslod = os.path.join(GAGNSMAPPA, skraarnafn)

    # Safna öllum gögnum
    oll_gogn = []

    # --- 1. Ræður ---
    print()
    raedur = saekja_raedur(dagar=100)
    oll_gogn.extend(raedur)

    # --- 2. Þingmál ---
    print()
    thingmal = saekja_thingmal(lthing=145)
    oll_gogn.extend(thingmal)

    # --- 3. Dagskrá ---
    print()
    dagskra = saekja_dagskra()
    oll_gogn.extend(dagskra)

    # --- Vista ---
    print()
    print(f"Heildargögn: {len(oll_gogn)} færslur")
    vista_jsonl(oll_gogn, skraarslod)

    print()
    print("=" * 60)
    print(f"Lokið: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Vistað í: {skraarslod}")
    print(f"Ræður: {len(raedur)}, Þingmál: {len(thingmal)}, Dagskrárliðir: {len(dagskra)}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Keyrsla
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    keyra()
