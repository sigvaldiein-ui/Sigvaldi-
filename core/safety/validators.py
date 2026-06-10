
"""Validators fyrir PII Sentry — vartala, Luhn, IBAN."""

KT_WEIGHTS = (3, 2, 7, 6, 5, 4, 3, 2)

def kt_valid(d10: str) -> bool:
    """Íslensk kennitala: DDMMÁÁ (6) + 2 tilviljanastafir + vartala (9.) + aldarstafur (10.).
    Mod-11 með vægjum 3,2,7,6,5,4,3,2 á fyrstu 8 stafi."""
    if len(d10) != 10 or not d10.isdigit():
        return False
    s = sum(w * int(c) for w, c in zip(KT_WEIGHTS, d10[:8]))
    r = s % 11
    v = 0 if r == 0 else 11 - r
    if v == 10:
        return False
    if int(d10[8]) != v:
        return False
    return d10[9] in "0987"

def kt_is_company(d10: str) -> bool:
    """Fyrirtækja-kt: fyrstu tveir stafir 41–71."""
    return len(d10) == 10 and d10.isdigit() and 41 <= int(d10[:2]) <= 71

def luhn_valid(digits: str) -> bool:
    """Luhn-algrím fyrir kortanúmer."""
    if not digits.isdigit() or len(digits) < 13:
        return False
    s = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        s += n
    return s % 10 == 0

def iban_is_valid(iban: str) -> bool:
    """IBAN mod-97 tékk."""
    iban = iban.replace(" ", "").replace("-", "").upper()
    if not iban.startswith("IS") or len(iban) < 26:
        return False
    rearranged = iban[4:] + "IS" + iban[2:4]
    numeric = ""
    for ch in rearranged:
        if ch.isdigit():
            numeric += ch
        else:
            numeric += str(ord(ch) - 55)
    try:
        return int(numeric) % 97 == 1
    except:
        return False
