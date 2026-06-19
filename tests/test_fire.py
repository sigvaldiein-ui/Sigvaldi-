import sys, os
sys.path.insert(0, '/workspace/Sigvaldi-')

from interfaces.chat_routes import _validate_response

# Söfnun heimilda – byggt á raunverulegu RAG-úttaki
citations = [
    {
        "title": "Lög um útsenda starfsmenn 2007 nr. 45",
        "snippet": "5. gr. Réttur til launa í veikinda- og slysatilvikum.",
    },
    {
        "title": "Lög um réttindi og skyldur starfsmanna ríkisins 1996 nr. 70",
        "snippet": "12. gr. Starfsmenn skulu eiga rétt til launa í veikindaforföllum.",
    },
]

print("=" * 60)
print("ELDSKÍRN – Fire test")
print("=" * 60)

# --- Próf 1: Grundað (á að vera True) ---
grundað = "Samkvæmt 5. gr. laga nr. 45/2007 á starfsmaður rétt til launa í veikindum."
ok1, _ = _validate_response(grundað, citations)
print(f"\nPróf 1 (grunduð tilvísun):")
print(f"  Svar: {grundað}")
print(f"  grounding_ok: {ok1}")

# --- Próf 2: Hallúsínerað (á að vera False) ---
uppspuni = "Samkvæmt lögum nr. 73/1995 um veikindarétt á starfsmaður rétt til 30 daga."
ok2, _ = _validate_response(uppspuni, citations)
print(f"\nPróf 2 (uppspuni – nr. 73/1995 er ekki í heimildum):")
print(f"  Svar: {uppspuni}")
print(f"  grounding_ok: {ok2}")

print("\n" + "=" * 60)
if ok1 and not ok2:
    print("NIÐURSTAÐA: Vörðurinn aðgreinir rétt (ELDSKÍRN STAÐIST)")
elif ok1 and ok2:
    print("NIÐURSTAÐA: Vörðurinn HAFNAR EKKI uppspuna (ófullnægjandi)")
elif not ok1:
    print("NIÐURSTAÐA: Vörðurinn hafnar LÍKA grunduðu svari (of strangur)")
else:
    print("NIÐURSTAÐA: Óvænt samsetning – athuga þarf")
print("=" * 60)
