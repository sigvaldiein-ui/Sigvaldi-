"""Sprint 64 C1 fixture builder (ASCII only to avoid WebSocket UTF-8 issues)."""
from pathlib import Path
import fitz

out = Path("tests/fixtures")
out.mkdir(parents=True, exist_ok=True)

# Sample PDF with table
doc = fitz.open()
page = doc.new_page()
html = """
<h3>Annual Report 2025</h3>
<table border="1" cellpadding="6">
<tr><th>Item</th><th>Amount ISK</th><th>Share</th></tr>
<tr><td>Revenue</td><td>1200000</td><td>100%</td></tr>
<tr><td>Expenses</td><td>450000</td><td>37%</td></tr>
<tr><td>Profit</td><td>750000</td><td>63%</td></tr>
</table>
"""
page.insert_htmlbox(fitz.Rect(50, 50, 500, 400), html)
doc.save(str(out / "sample_tables.pdf"))
doc.close()
print("sample_tables.pdf OK")

# Empty PDF
d2 = fitz.open()
d2.new_page()
d2.save(str(out / "empty_notable.pdf"))
d2.close()
print("empty_notable.pdf OK")
