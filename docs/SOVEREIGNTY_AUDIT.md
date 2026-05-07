# Sovereign Deployment Audit — Alvitur A100 pod

**Date:** 2026-05-07  
**Pod:** `spotless_aquamarine_meerkat`  
**GPU:** A100 SXM 80 GB  
**Region:** EUR-IS-1 (RunPod label)  

## Physical datacenter
- **Operator:** Míla hf.
- **Address:** Stórhöfði 22-30, Reykjavík, Iceland
- **IP range:** 157.157.221.0/24 (MILA-DC)
- **Verified:** via RIPE database and IP whois

## Data flow
- All processing happens on the GPU inside the Icelandic datacenter.
- No data leaves Icelandic jurisdiction during normal operation.
- Model weights are loaded from Hugging Face (CDN, cached locally).

## Sub-processor chain
| Layer | Entity | Jurisdiction |
|---|---|---|
| Application | Alvitur / Orkuskipti ehf | Iceland |
| Cloud provider | RunPod, Inc. | USA (Delaware) |
| Datacenter operator | Míla hf. | Iceland |

## Compliance notes
- RunPod is a US company → subject to CLOUD Act.
- Mitigation: data never leaves Iceland; direct contract with Icelandic datacenter (atNorth) recommended for Stage 4 sovereign deployment.
- Míla holds ISO 27001 certification.
