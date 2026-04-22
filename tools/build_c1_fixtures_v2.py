"""Rebuild sample_tables.pdf with REAL grid borders + verify via to_pandas()."""
from pathlib import Path
import fitz

OUT = Path("tests/fixtures/sample_tables.pdf")

def draw_table(page, x0, y0, rows, col_widths, row_h=22):
    n_rows = len(rows)
    n_cols = len(col_widths)
    xs = [x0]
    for w in col_widths:
        xs.append(xs[-1] + w)
    total_w = xs[-1] - x0
    total_h = n_rows * row_h
    for i in range(n_rows + 1):
        y = y0 + i * row_h
        page.draw_line(fitz.Point(x0, y), fitz.Point(x0 + total_w, y), width=0.8)
    for j in range(n_cols + 1):
        x = xs[j]
        page.draw_line(fitz.Point(x, y0), fitz.Point(x, y0 + total_h), width=0.8)
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            page.insert_text(fitz.Point(xs[c] + 4, y0 + r * row_h + 15),
                             str(cell), fontsize=10)

doc = fitz.open()
page = doc.new_page()
page.insert_text(fitz.Point(50, 50), "Sample Tables Document", fontsize=14)
draw_table(page, 50, 80,
           rows=[["Name", "Age", "City"],
                 ["Alice", "30", "Reykjavik"],
                 ["Bob", "25", "Akureyri"]],
           col_widths=[120, 60, 120])
draw_table(page, 50, 220,
           rows=[["Key", "Value"],
                 ["alpha", "42"],
                 ["beta", "99"]],
           col_widths=[120, 80])
doc.save(str(OUT))
doc.close()
print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")

d = fitz.open(str(OUT))
tf = d[0].find_tables()
print(f"PyMuPDF tables: {len(tf.tables)}")
if tf.tables:
    df = tf.tables[0].to_pandas()
    print(f"  table0 to_pandas -> shape={df.shape}, cols={list(df.columns)}")
    print(df.head().to_string(index=False))
d.close()

import pdfplumber
with pdfplumber.open(str(OUT)) as pdf:
    ts = pdf.pages[0].extract_tables()
    print(f"pdfplumber tables: {len(ts)}")
    if ts:
        print(f"  table0 first 2 rows: {ts[0][:2]}")
