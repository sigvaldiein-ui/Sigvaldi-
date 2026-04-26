"""Örugg Pandas kóðasniðmát — Sprint 71 Track B.3b.

LLM fær lista af sniðmátum með schema, velur eitt,
og skilar parametrum. Við keyrum kóðann — engin exec().
"""
from __future__ import annotations
import io
import logging

logger = logging.getLogger("alvitur.templates")

TEMPLATES = {
    "column_sum": {
        "lýsing": "Summa eins dálks",
        "params": {"column": "Nafn dálks (numeric)"},
        "dæmi": '{"template": "column_sum", "params": {"column": "upphaed"}}',
    },
    "groupby_sum": {
        "lýsing": "Summa eftir flokkunardálki",
        "params": {"column": "Nafn numeric dálks", "groupby": "Nafn flokkunardálks"},
        "dæmi": '{"template": "groupby_sum", "params": {"column": "upphaed", "groupby": "motadili"}}',
    },
    "groupby_mean": {
        "lýsing": "Meðaltal eftir flokkunardálki",
        "params": {"column": "Nafn numeric dálks", "groupby": "Nafn flokkunardálks"},
        "dæmi": '{"template": "groupby_mean", "params": {"column": "upphaed", "groupby": "tegund"}}',
    },
    "column_stats": {
        "lýsing": "Lýsandi tölfræði fyrir einn dálk",
        "params": {"column": "Nafn dálks (numeric)"},
        "dæmi": '{"template": "column_stats", "params": {"column": "upphaed"}}',
    },
    "top_n": {
        "lýsing": "Top N raðir eftir dálki",
        "params": {"column": "Nafn dálks til að raða eftir", "n": "Fjöldi raða (sjálfgefið 5)"},
        "dæmi": '{"template": "top_n", "params": {"column": "upphaed", "n": 10}}',
    },
    "bottom_n": {
        "lýsing": "Bottom N raðir eftir dálki",
        "params": {"column": "Nafn dálks", "n": "Fjöldi raða (sjálfgefið 5)"},
        "dæmi": '{"template": "bottom_n", "params": {"column": "upphaed", "n": 5}}',
    },
    "filter_by_value": {
        "lýsing": "Sía raðir þar sem dálkur er stærri/minni en gildi",
        "params": {"column": "Nafn dálks", "operator": "> eða < eða ==", "value": "Gildi"},
        "dæmi": '{"template": "filter_by_value", "params": {"column": "upphaed", "operator": ">", "value": 100000}}',
    },
    "filter_by_date_range": {
        "lýsing": "Sía raðir eftir dagsetningabili",
        "params": {"date_column": "Nafn dagsetningardálks", "from": "YYYY-MM-DD", "to": "YYYY-MM-DD"},
        "dæmi": '{"template": "filter_by_date_range", "params": {"date_column": "dagsetning", "from": "2024-01-01", "to": "2024-12-31"}}',
    },
    "count_by": {
        "lýsing": "Fjöldi raða eftir flokkunardálki",
        "params": {"groupby": "Nafn flokkunardálks"},
        "dæmi": '{"template": "count_by", "params": {"groupby": "motadili"}}',
    },
    "pivot_sum": {
        "lýsing": "Pivot tafla — summa eftir tveimur víddum",
        "params": {"values": "Nafn numeric dálks", "index": "Nafn dálks fyrir raðir", "columns": "Nafn dálks fyrir dálka"},
        "dæmi": '{"template": "pivot_sum", "params": {"values": "upphaed", "index": "motadili", "columns": "tegund"}}',
    },
}


def get_templates_for_llm() -> str:
    """Skilar sniðmátum á formi sem LLM skilur — til að setja í system prompt."""
    lines = ["### Tiltæk kóðasniðmát — veldu eitt og skilaðu JSON:", ""]
    for name, meta in TEMPLATES.items():
        lines.append(f"- **{name}**: {meta['lýsing']}")
        lines.append(f"  Params: {meta['params']}")
        lines.append(f"  Dæmi: `{meta['dæmi']}`")
        lines.append("")
    lines += [
        "Skilaðu EINUNGIS JSON á þessu formi ef töluleg greining er beðin um:",
        '`{"template": "<nafn>", "params": {...}}`',
        "Ef spurningin er ekki töluleg, svaraðu venjulega í texta.",
    ]
    return "\n".join(lines)


def execute_template(file_data: bytes, filename: str, template_name: str, params: dict) -> str:
    """Keyrir sniðmát á skjal. Aldrei kastar — skilar markdown."""
    try:
        import pandas as pd
        fname = filename.lower()
        if fname.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_data))
        elif fname.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(file_data), engine="xlrd")
        else:
            df = pd.read_excel(io.BytesIO(file_data))

        if template_name not in TEMPLATES:
            return f"<!-- Óþekkt sniðmát: {template_name} -->"

        return _run_template(df, template_name, params)

    except Exception as e:
        logger.error(f"[TEMPLATES] execute failed {template_name}: {e}")
        return f"<!-- Template error: {type(e).__name__}: {e} -->"


def _run_template(df, name: str, p: dict) -> str:
    if name == "column_sum":
        col = p["column"]
        total = df[col].sum()
        return f"**Summa {col}:** {total:,.2f}\n\nFjöldi raða: {len(df)}"

    elif name == "groupby_sum":
        col, gb = p["column"], p["groupby"]
        grouped = df.groupby(gb)[col].sum().sort_values(ascending=False)
        lines = [f"### Summa {col} eftir {gb}", ""]
        for idx, val in grouped.items():
            lines.append(f"- **{idx}**: {val:,.2f}")
        return "\n".join(lines)

    elif name == "groupby_mean":
        col, gb = p["column"], p["groupby"]
        grouped = df.groupby(gb)[col].mean().sort_values(ascending=False)
        lines = [f"### Meðaltal {col} eftir {gb}", ""]
        for idx, val in grouped.items():
            lines.append(f"- **{idx}**: {val:,.2f}")
        return "\n".join(lines)

    elif name == "column_stats":
        col = p["column"]
        stats = df[col].describe()
        lines = [f"### Tölfræði fyrir {col}", ""]
        for stat_name, val in stats.items():
            lines.append(f"- **{stat_name}**: {val:,.2f}")
        return "\n".join(lines)

    elif name == "top_n":
        col, n = p["column"], int(p.get("n", 5))
        top = df.nlargest(n, col)
        return f"### Top {n} eftir {col}\n\n{top.to_string(index=False)}"

    elif name == "bottom_n":
        col, n = p["column"], int(p.get("n", 5))
        bottom = df.nsmallest(n, col)
        return f"### Bottom {n} eftir {col}\n\n{bottom.to_string(index=False)}"

    elif name == "filter_by_value":
        col, op, val = p["column"], p["operator"], p["value"]
        ops = {">": lambda a, b: a > b, "<": lambda a, b: a < b, "==": lambda a, b: a == b}
        if op not in ops:
            return f"<!-- Óþekktur operator: {op} -->"
        filtered = df[ops[op](df[col], val)]
        return f"### Raðir þar sem {col} {op} {val} ({len(filtered)} raðir)\n\n{filtered.to_string(index=False)}"

    elif name == "filter_by_date_range":
        import pandas as pd
        date_col = p["date_column"]
        df[date_col] = pd.to_datetime(df[date_col])
        mask = (df[date_col] >= p["from"]) & (df[date_col] <= p["to"])
        filtered = df[mask]
        return f"### Raðir frá {p['from']} til {p['to']} ({len(filtered)} raðir)\n\n{filtered.to_string(index=False)}"

    elif name == "count_by":
        gb = p["groupby"]
        counts = df.groupby(gb).size().sort_values(ascending=False)
        lines = [f"### Fjöldi raða eftir {gb}", ""]
        for idx, val in counts.items():
            lines.append(f"- **{idx}**: {val}")
        return "\n".join(lines)

    elif name == "pivot_sum":
        import pandas as pd
        pivot = pd.pivot_table(df, values=p["values"], index=p["index"],
                               columns=p["columns"], aggfunc="sum", fill_value=0)
        return f"### Pivot: {p['values']} eftir {p['index']} × {p['columns']}\n\n{pivot.to_string()}"

    return f"<!-- Ekkert sniðmát: {name} -->"


import json as _json
import re as _re


def build_tabular_system_prompt(schema_text: str) -> str:
    """Byggir system prompt með schema + template lista fyrir LLM."""
    templates_help = get_templates_for_llm()
    return f"""Þú ert aðstoðarmaður sem greinir töflugögn. Þú færð schema um skjal og spurningu frá notanda.

SVARAÐU ALLTAF Á ÍSLENSKU.

MIKILVÆGT: Þú mátt EKKI reikna summur, meðaltöl eða aðra tölfræði í huganum.
Notaðu í staðinn kóðasniðmátin hér að neðan.

SVAR-FORM — skilaðu ALLTAF þessum JSON:
{{
  "template": "nafn sniðmáts eða null",
  "params": {{}},
  "explanation": "Útskýring á íslensku"
}}

{schema_text}

{templates_help}"""


def parse_llm_template_response(llm_text: str) -> dict:
    """Dregur út template + params úr LLM svari. Aldrei kastar."""
    try:
        # Reyna beint JSON parse fyrst
        stripped = llm_text.strip()
        if stripped.startswith("{"):
            return _json.loads(stripped)
    except (_json.JSONDecodeError, ValueError):
        pass
    try:
        # Finna JSON blokk inni í texta (t.d. ```json ... ```)
        m = _re.search(r'\{[^{}]*"template"[^{}]*\}', llm_text, _re.DOTALL)
        if m:
            return _json.loads(m.group())
    except (_json.JSONDecodeError, AttributeError):
        pass
    # Fallback — engin template, textasvar
    return {"template": None, "params": {}, "explanation": llm_text[:800]}
