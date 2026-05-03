
---

## 3. maí 2026 — Viðbótargreining

### Qdrant Collection Stærð
| Collection | Chunks | Stærð | Meðalstærð per chunk |
|------------|--------|-------|----------------------|
| `alvitur_laws_v2` | 23.621 | 259,8 MB | ~11 KB |

### Spá um Vöxt (áætlað)
| Þáttur | Núverandi stærð | Áætlaður vöxtur | Tími að 50 GB |
|--------|-----------------|-----------------|---------------|
| Kóði + docs (.git) | 190 MB | ~10-20 MB/viku | > 10 ár |
| Data (embedding) | 317 MB | ~200-500 MB/viku | > 2 ár |
| Cache (HF) | 2,2 GB | Stöðugt nema nýtt líkan bætist við | > 2 ár |
| **Samtals** | **~22 GB** | **~300-500 MB/viku** | **~2027+** |

> **Athugið:** Stærstu stökkin verða við K4 (allar reglugerðir) og K5 (BÍN orðabók). Áætluð stækkun við K4: ~1-3 GB.

### Backup Staða
| Hvað | Hvar | Staða |
|------|------|-------|
| Kóði + stillingar | GitHub (`sigvaldiein-ui/Sigvaldi-`) | ✅ Lifandi, pushað eftir hvern fasa |
| `requirements.txt` | GitHub | ✅ 303 pakkar |
| `.env.example` | GitHub | ✅ Sniðmát, engir lyklar |
| Qdrant `storage.sqlite` | Aðeins á MFS diski | ⚠️ **Ekkert off-site backup** |
| Hugging Face cache | Aðeins á MFS diski | ⚠️ Hægt að endurhlaða en tekur tíma |

> **Tillaga:** Taka backup af `storage.sqlite` (260 MB) og geyma á GitHub LFS eða S3 sameign.
