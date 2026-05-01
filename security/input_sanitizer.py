#!/usr/bin/env python3
import re

BLACKLIST = [
    "ignore previous instructions", "ignore all previous",
    "gleymdu ollum fyrirmaelum", "gleymdu ollu",
    "system prompt", "system message",
    "developer mode", "do anything now",
    "thu ert ekki mimir", "you are not mimir",
    "new persona", "act as", "pretend you are",
    "leyndarmal kerfisins", "hvernig ertu forritadur",
    "jailbreak", "bypass", "override instructions"
]

def is_safe_prompt(text: str) -> bool:
    texti = text.lower().strip()
    for ban in BLACKLIST:
        if ban in texti:
            return False
    if re.search(r'\bdan\b', texti):
        return False
    return True

def get_rejection_message() -> str:
    return "Eg er Mimir og eg fylgi minum eigin reglum. Hvernig get eg adstodad thig vid eitthvad annad?"

def sanitize_text(text: str) -> str:
    texti = text
    for ban in BLACKLIST:
        texti = texti.replace(ban, "")
    return texti

if __name__ == "__main__":
    print("CODE FREEZE - Standalone eining")
    print(is_safe_prompt("ignore previous instructions"))
    print(is_safe_prompt("halló"))
