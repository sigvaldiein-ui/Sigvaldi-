"""
Sprint 62 Patch B — Excel Pre-processor (Reiknivélar-Agent skref 1).

LLM getur ekki reiknað áreiðanlega. Þetta fall les Excel skjal með pandas,
reiknar raunverulegar summur, og skilar strúktúruðum markdown texta sem
LLM getur útskýrt án þess að reikna sjálft.

Höfundur: Alvitur Sprint 62.
"""
from __future__ import annotations
import io
import logging
from typing import Union

logger = logging.getLogger("alvitur.excel")

_AMOUNT_HINTS = ('upph', 'upphæð', 'amount', 'debet', 'kredit', 'fjárhæð', 'krón')
_DATE_HINTS = ('dags', 'date', 'dagsetn')
_CATEGORY_HINTS = ('tegund', 'type', 'flokk', 'textalyk')
_COUNTERPART_HINTS = ('mótaðil', 'motadil', 'counterp', 'viðtak', 'viðskiptam', 'lykill')
_BALANCE_HINTS = ('staða', 'stada', 'balance', 'saldo')

def _pick_column(df, hints):
    """Finna dálk sem matchar einhverja hint-string."""
    for col in df.columns:
        name = str(col).lower()
        if any(h in name for h in hints):
            return col
    return None

def _pick_amount_column(df):
    """Finna líklegasta upphæðardálk (numeric, með + og -)."""
    # Fyrst: nafnið gefur til kynna
    named = _pick_column(df, _AMOUNT_HINTS)
    if named is not None and df[named].dtype in ('int64', 'float64'):
        return named
    # Annars: fyrsti numeric dálkurinn með bæði + og - gildi
    for col in df.columns:
        if df[col].dtype in ('int64', 'float64'):
            non_null = df[col].dropna()
            if len(non_null) > 5 and non_null.abs().max() > 100:
                return col
    return None

def preprocess_excel(file_input: Union[bytes, str, io.BytesIO]) -> str:
    """
    Les Excel skjal og skilar markdown texta með raunverulegum útreikningum.

    Args:
        file_input: bytes (frá UploadFile.read()), path, eða BytesIO.

    Returns:
        Markdown-strengur með summum og raw gögnum. Aldrei kasta exception —
        skilar error-message í staðinn svo FastAPI fái ekki 500.
    """
    try:
        import pandas as pd
    except ImportError:
        return "[VILLA: pandas ekki sett upp á þjóni. Keyrðu: pip install pandas openpyxl]"

    try:
        if isinstance(file_input, bytes):
            data = io.BytesIO(file_input)
        elif isinstance(file_input, io.BytesIO):
            data = file_input
        else:
            data = file_input

        df = pd.read_excel(data, header=0)
    except Exception as e:
        logger.warning(f"[excel_preprocessor] read failed: {type(e).__name__}: {e}")
        return f"[VILLA við lestur Excel: {type(e).__name__}. Skjalið gæti verið skemmd eða dulkóðað.]"

    if df.shape[0] == 0:
        return "[Tómt Excel skjal — engar línur]"

    amount_col = _pick_amount_column(df)
    date_col = _pick_column(df, _DATE_HINTS)
    category_col = _pick_column(df, _CATEGORY_HINTS)
    counterpart_col = _pick_column(df, _COUNTERPART_HINTS)
    balance_col = _pick_column(df, _BALANCE_HINTS)
    out = []  # Járnreglur fjarlægðar — svar er hreint
    # out.append("")
    # out.append("")
    # out.append(f"- **Skjal**: {df.shape[0]} línur × {df.shape[1]} dálkar")
    out.append(f"- **Dálkar í skjali**: {', '.join(str(c) for c in df.columns)}")

    if date_col:
        try:
            dates = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
            valid = dates.dropna()
            if len(valid) > 0:
                out.append(f"- **Tímabil**: {valid.min().strftime('%Y-%m-%d')} til {valid.max().strftime('%Y-%m-%d')}")
        except Exception as e:
            logger.debug(f"[excel_preprocessor] date parse: {e}")

        s = df[amount_col].dropna()
        pos = s[s > 0]
        neg = s[s < 0]
        out.append(f"\n### 💰 HEILDARTÖLUR — BEINT ÚR SKJALI ({amount_col})")
        out.append(f"🔒 **SAMTALS INNHEIMT (allar jákvæðar):** {pos.sum():,.0f} kr  —  {len(pos)} færslur")
        out.append(f"🔒 **SAMTALS ÚTBORGUN (allar neikvæðar):** {neg.sum():,.0f} kr  —  {len(neg)} færslur")
        out.append(f"🔒 **NETTÓ HREYFING:** {s.sum():,.0f} kr")
        out.append(f"🔒 **HEILDARVELTA (|summa|):** {s.abs().sum():,.0f} kr")
        out.append(f"")

        if category_col:
            try:
                grp = df.groupby(category_col)[amount_col].agg(['sum', 'count']).sort_values('sum')
                out.append(f"\n### 📂 Samtölur eftir {category_col}")
                for idx, row in grp.iterrows():
                    out.append(f"- **{idx}**: {row['sum']:,.0f} kr ({int(row['count'])} færslur)")
            except Exception as e:
                logger.debug(f"[excel_preprocessor] groupby category: {e}")

        if counterpart_col:
            try:
                grp = df.groupby(counterpart_col)[amount_col].agg(['sum', 'count']).sort_values('sum')
                out.append(f"\n### 👥 Samtölur eftir {counterpart_col} (topp 10 stærstu útgjöld)")
                for idx, row in grp.head(10).iterrows():
                    out.append(f"- **{idx}**: {row['sum']:,.0f} kr ({int(row['count'])} færslur)")
                pos_side = grp[grp['sum'] > 0].tail(10)
                if len(pos_side) > 0:
                    out.append(f"\n**Innborganir (topp 10):**")
                    for idx, row in pos_side.iterrows():
                        out.append(f"- **{idx}**: {row['sum']:,.0f} kr ({int(row['count'])} færslur)")
            except Exception as e:
                logger.debug(f"[excel_preprocessor] groupby counterpart: {e}")

    if balance_col:
        try:
            bal = df[balance_col].dropna()
            if len(bal) >= 2:
                out.append(f"\n### 📈 Stöðubreyting ({balance_col})")
                out.append(f"- Fyrsta færsla: {bal.iloc[0]:,.0f} kr")
                out.append(f"- Síðasta færsla: {bal.iloc[-1]:,.0f} kr")
                out.append(f"- Breyting á tímabili: {bal.iloc[0] - bal.iloc[-1]:,.0f} kr")
        except Exception as e:
            logger.debug(f"[excel_preprocessor] balance: {e}")

    return "\n".join(out)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(preprocess_excel(sys.argv[1]))
    else:
        print("Notkun: python3 excel_preprocessor.py <path_to.xlsx>")
