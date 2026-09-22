"""Convert a PDF page range with Docling and write readable results to ../outputs.

Usage: python check_docling_chunks.py <pdf> <first_page> <last_page>
Pages are 1-indexed PDF pages (gold evidence_page_num + 1).

Writes to ../outputs/<doc>_p<first>-<last>/:
  report.md        headings, stats, every chunk (both merge_peers settings)
  docling.md       Docling markdown export of the page range
  docling.json     Docling JSON export of the page range
"""
import json
import re
import sys
from pathlib import Path

from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker

pdf = Path(sys.argv[1])
first, last = int(sys.argv[2]), int(sys.argv[3])

out = Path(__file__).resolve().parent.parent / "outputs" / f"{pdf.stem}_p{first}-{last}"
out.mkdir(parents=True, exist_ok=True)

doc = DocumentConverter().convert(str(pdf), page_range=(first, last)).document

(out / "docling.md").write_text(doc.export_to_markdown(), encoding="utf-8")
(out / "docling.json").write_text(
    json.dumps(doc.export_to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
)

labels, headers, runin_missed = {}, [], []
for item, _ in doc.iterate_items():
    label = str(getattr(item, "label", None))
    labels[label] = labels.get(label, 0) + 1
    text = (getattr(item, "text", "") or "").strip()
    page = [p.page_no for p in getattr(item, "prov", [])]
    if "section_header" in label:
        headers.append((page, text[:80]))
    elif "text" in label and re.match(r"^[A-Z][^.]{2,60}:$", text):
        runin_missed.append((page, text))

lines = [f"# {pdf.stem}, PDF pages {first}-{last}", ""]
lines += ["## Item labels", "", f"`{labels}`", ""]
lines += [f"## Section headers ({len(headers)})", ""]
lines += [f"- p{h[0]}: {h[1]}" for h in headers] or ["(none)"]
lines += ["", f"## Run-in labels left as plain text ({len(runin_missed)})", ""]
lines += [f"- p{h[0]}: {h[1]}" for h in runin_missed] or ["(none)"]

summary = []
for merge in (True, False):
    chunks = list(HybridChunker(merge_peers=merge).chunk(doc))
    sizes = [len(c.text.split()) for c in chunks]
    tiny = sum(s < 20 for s in sizes)
    with_table = sum(
        any("table" in str(getattr(i, "label", "")) for i in c.meta.doc_items)
        for c in chunks
    )
    summary.append(
        f"merge_peers={merge}: {len(chunks)} chunks, {tiny} tiny (<20 words), "
        f"{with_table} contain table items"
    )
    lines += ["", f"## Chunks, merge_peers={merge}", "", summary[-1], ""]
    for i, c in enumerate(chunks):
        kinds = sorted({str(getattr(x, "label", "")).split(".")[-1] for x in c.meta.doc_items})
        lines += [
            f"### chunk {i} | {len(c.text.split())} words | items: {', '.join(kinds)}",
            f"heading path: {' > '.join(c.meta.headings or []) or '(none)'}",
            "",
            "```",
            c.text.strip(),
            "```",
            "",
        ]

(out / "report.md").write_text("\n".join(lines), encoding="utf-8")
print(f"{pdf.stem} p{first}-{last}: {out}")
for s in summary:
    print("  ", s)
