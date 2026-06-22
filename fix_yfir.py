with open('core/agents/yfir_erindreki.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip_until_else = False
for i, line in enumerate(lines):
    # Lína sem inniheldur DEBUG2 - sleppa
    if 'DEBUG2' in line:
        continue
    # Eftir að hafa séð if search_context: og næsta lína er import sys, þá erum við í DEBUG2 blokk
    # Við sleppum líka import sys ef hún er beint á eftir if search_context
    if line.strip() == 'import sys' and i > 0 and 'if search_context:' in lines[i-1]:
        continue
    # Ef línan er tóm og við erum á milli def og docstring, sleppum
    new_lines.append(line)

# Nú tryggjum við að docstring-ið sé rétt staðsett: strax eftir def línuna, án auka lína
final_lines = []
i = 0
while i < len(new_lines):
    line = new_lines[i]
    final_lines.append(line)
    # Ef þetta er def handle(...):
    if 'async def handle(self, query: str,' in line:
        # Næstu línur eftir def ættu að vera docstring
        # Við förum framhjá tómum línum og import sys
        j = i + 1
        while j < len(new_lines) and (new_lines[j].strip() == '' or new_lines[j].strip() == 'import sys'):
            j += 1
        # Næsta lína ætti að vera docstring-ið
        if j < len(new_lines) and new_lines[j].strip().startswith('"""'):
            # Setjum docstring-ið strax á eftir def línunni
            # Við höfum nú þegar bætt def línunni við, nú bætum við docstringinu beint á eftir
            final_lines.append(new_lines[j])
            i = j  # Hoppa yfir í þessa línu
        # Sleppum öðrum línum sem voru á milli
    i += 1

with open('core/agents/yfir_erindreki.py', 'w') as f:
    f.writelines(final_lines)

print("DEBUG2 fjarlægð, docstring lagfært")
