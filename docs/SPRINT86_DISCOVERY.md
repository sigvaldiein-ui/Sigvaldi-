
---

## 5. Gagnastraumar — kortlagning frá Aðal (16. maí 2026)

### A — Tilbúið að nota (API/RSS, opið, einfalt)

| Heimild | Format | Slóð |
|---|---|---|
| Dómstólar RSS | RSS | https://www.domstolar.is/domstolasyslan/thjonusta/askrift-ad-efni-a-vef/ |
| Alþingi XML | XML | https://www.althingi.is/altext/xml/ |
| Hagstofa API | JSON | https://px.hagstofa.is |
| Seðlabanki NSDP | JSON | https://data.sedlabanki.is |

### B — Aðgengilegt en þarf smá vinnu

| Heimild | Format | Athugasemd |
|---|---|---|
| reglugerd.is | HTML | ~3.000+ reglugerðir, engin API |
| personuvernd.is | HTML | Álit og ákvarðanir |
| ust.is | HTML | Umhverfisstofnun — opinberar skýrslur |

### C — Mögulegt en flókið

| Heimild | Vandinn |
|---|---|
| island.is API | X-Road — krefst skráningar |
| haestirettur.is dómar | Enginn bulk download |

### Forgangsröðun næstu gagnagjafa

1. **Dómstólar RSS** — auðveldast, sama mynstur og stjornartidindi fetcher
2. **Hagstofa PX-Web API** — Python library, CC BY, finance domain
3. **personuvernd.is** — mikilvægt fyrir legal domain
