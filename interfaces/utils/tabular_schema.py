"""Tabular schema extraction — Sprint 71 Track B.2."""
from __future__ import annotations
import io
import logging

logger = logging.getLogger("alvitur.tabular")

MAX_TABULAR_SIZE = 20 * 1024 * 1024  # 20 MB — samræmi við MAX_PDF_SIZE


def extract_schema(file_data: bytes, filename: str) -> str:
    """Aldrei kastar — skilar error markdown ef mistekst."""
    if len(file_data) > MAX_TABULAR_SIZE:
        return f"<!-- Skjal of stórt: {len(file_data):,} bytes. Hámark er {MAX_TABULAR_SIZE:,} bytes (20 MB). -->"
    try:
        import pandas as pd

        fname = filename.lower()
        if fname.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_data))
        elif fname.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(file_data), engine="xlrd")
        else:
            df = pd.read_excel(io.BytesIO(file_data))

        if df.empty:
            return "<!-- Tómt skjal — engar raðir -->"

        return _build_schema_markdown(df, filename)

    except Exception as e:
        logger.error(f"[TABULAR] Schema extraction failed for {filename}: {e}")
        return f"<!-- Schema extraction error: {type(e).__name__}: {e} -->"


def _build_schema_markdown(df, filename: str) -> str:
    import pandas as pd

    parts = [
        f"## Töflureiknun: {filename}",
        f"- **Raðir:** {len(df)}",
        f"- **Dálkar:** {len(df.columns)}",
        "",
        "### Dálkar og tölfræði",
        "",
    ]

    for col in df.columns:
        dtype_str = str(df[col].dtype)
        parts.append(f"- **{col}** (`{dtype_str}`)")

        if pd.api.types.is_numeric_dtype(df[col]):
            s = df[col].dropna()
            if len(s) > 0:
                parts.append(f"  - Summa: {s.sum():,.2f}")
                parts.append(f"  - Meðaltal: {s.mean():,.2f}")
                parts.append(f"  - Lágmark: {s.min():,.2f}")
                parts.append(f"  - Hámark: {s.max():,.2f}")
                parts.append(f"  - Núllgildi: {int((s == 0).sum())}")

        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            parts.append(f"  - Frá: {df[col].min()}")
            parts.append(f"  - Til: {df[col].max()}")

        else:  # object, StringDtype, category, o.fl.
            unique = int(df[col].dropna().nunique())
            parts.append(f"  - Unique gildi: {unique}")
            if unique <= 10:
                top_vals = df[col].value_counts().head(5).to_dict()
                parts.append(f"  - Algengustu: {top_vals}")

    parts += [
        "",
        "### Sýnishorn (fyrstu 3 raðir)",
        "",
        df.head(3).to_string(index=False),
        "",
        "### Síðustu 2 raðir",
        "",
        df.tail(2).to_string(index=False),
    ]

    return "\n".join(parts)


def schema_to_prompt_injection(schema_text: str) -> str:
    return (
        "\n[SCHEMA INJECTION — EKKI REIKNA SJÁLFUR]\n"
        "Eftirfarandi er lýsigögn um töflureiknun. Þú SKALT nota þessar upplýsingar "
        "til að svara spurningunni. Þú mátt EKKI reyna að reikna summur eða meðaltöl "
        "í huganum — vísaðu í tölfræðina hér að neðan.\n\n"
        f"{schema_text}\n"
        "[END SCHEMA INJECTION]\n"
    )
