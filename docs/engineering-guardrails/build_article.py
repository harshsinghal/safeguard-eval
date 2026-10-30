"""Build the engineering article from editable prose and archived metrics.

Use the Codex bundled Python runtime. No inference or network access is needed.
The JSON holds prose; leaderboard cells always come from the frozen results.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
ARTICLE = ROOT / "article.json"
RESULTS = REPO / "published_runs/2026-10-29-leaderboard-decision-models/results.json"
OUT = ROOT / "output/policy-guardrails-engineering.docx"
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def set_font(style, name, size, bold=False):
    style.font.name = name
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = RGBColor(0, 0, 0)
    pr = style.element.get_or_add_rPr()
    fonts = pr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        pr.insert(0, fonts)
    for key in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(qn("w:" + key), name)
    for key in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
        fonts.attrib.pop(qn("w:" + key), None)
    color = pr.find(qn("w:color"))
    if color is not None:
        for key in ("themeColor", "themeTint", "themeShade"):
            color.attrib.pop(qn("w:" + key), None)


def hyperlink(p, label, target):
    if not target.startswith("https://"):
        path = (ROOT / target).resolve()
        assert path.is_file(), path
        target = os.path.relpath(path, OUT.parent)
    rid = p.part.relate_to(
        target,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    el = OxmlElement("w:hyperlink")
    el.set(qn("r:id"), rid)
    run, props = OxmlElement("w:r"), OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "214E65")
    props.append(color)
    under = OxmlElement("w:u")
    under.set(qn("w:val"), "single")
    props.append(under)
    run.append(props)
    t = OxmlElement("w:t")
    t.text = label
    run.append(t)
    el.append(run)
    p._p.append(el)


def rich_text(p, text):
    pos = 0
    for m in LINK.finditer(text):
        p.add_run(text[pos:m.start()])
        hyperlink(p, m.group(1), m.group(2))
        pos = m.end()
    p.add_run(text[pos:])


def table_rows(block, results):
    index = {
        ds: {r["group"]: r for r in data["profiles"]["balanced"]["rows"]}
        for ds, data in results["datasets"].items()
    }
    rows = []
    for group in block["groups"]:
        row = [block["labels"][group], block["families"][group]]
        for ds in ("wildguard", "hatexplain"):
            if group not in index[ds]:
                row.append("—")
                continue
            metrics = index[ds][group]["metrics"]
            dataset = results["datasets"][ds]
            assert metrics["unresolved"] == 0
            expected = ((1 - metrics["missed_violations"] / dataset["positives"])
                        + (1 - metrics["false_blocks"] / dataset["negatives"])) / 2
            assert abs(expected - metrics["balanced_accuracy"]) < 1e-10
            row.append(f"{100 * metrics['balanced_accuracy']:.2f}")
        rows.append(row)
    return rows


def add_table(doc, rows):
    table = doc.add_table(rows=1, cols=4)
    table.autofit = False
    widths = [2.45, 1.35, 1.3, 1.4]
    for col, width in zip(table.columns, widths):
        col.width = Inches(width)
    pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        node = OxmlElement("w:" + side)
        for key, val in {"val": "single", "sz": "4", "color": "D9D9D9"}.items():
            node.set(qn("w:" + key), val)
        borders.append(node)
    pr.append(borders)
    header = OxmlElement("w:tblHeader")
    table.rows[0]._tr.get_or_add_trPr().append(header)
    all_rows = [["Model tested", "Group", "WildGuard", "HateXplain"], *rows]
    for idx, values in enumerate(all_rows):
        row = table.rows[0] if idx == 0 else table.add_row()
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for j, (cell, value) in enumerate(zip(row.cells, values)):
            cell.width = Inches(widths[j])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cpr = cell._tc.get_or_add_tcPr()
            margins = OxmlElement("w:tcMar")
            for side in ("top", "left", "bottom", "right"):
                node = OxmlElement("w:" + side)
                node.set(qn("w:w"), "85")
                node.set(qn("w:type"), "dxa")
                margins.append(node)
            cpr.append(margins)
            if idx == 0:
                fill = OxmlElement("w:shd")
                fill.set(qn("w:fill"), "E5E7EB")
                cpr.append(fill)
            p = cell.paragraphs[0]
            p.style = doc.styles["Table Text"]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j < 2 else WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_with_next = idx == 0
            run = p.add_run(value)
            run.bold = idx == 0
    return table


def build():
    article, results = json.loads(ARTICLE.read_text()), json.loads(RESULTS.read_text())
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    sec.left_margin = sec.right_margin = Inches(1)
    sec.top_margin = sec.bottom_margin = Inches(.85)
    sec.footer_distance = Inches(.35)
    normal = doc.styles["Normal"]
    set_font(normal, "Georgia", 11.5)
    normal.paragraph_format.line_spacing = 1.1
    normal.paragraph_format.space_after = Pt(7)
    normal.paragraph_format.widow_control = True
    set_font(doc.styles["Title"], "Georgia", 25, True)
    doc.styles["Title"].paragraph_format.line_spacing = 1.03
    doc.styles["Title"].paragraph_format.space_after = Pt(9)
    doc.styles["Title"].paragraph_format.keep_with_next = True
    set_font(doc.styles["Subtitle"], "Georgia", 12)
    doc.styles["Subtitle"].paragraph_format.space_after = Pt(10)
    doc.styles["Subtitle"].paragraph_format.keep_with_next = True
    set_font(doc.styles["Heading 1"], "Georgia", 14, True)
    doc.styles["Heading 1"].paragraph_format.space_before = Pt(14)
    doc.styles["Heading 1"].paragraph_format.space_after = Pt(7)
    doc.styles["Heading 1"].paragraph_format.keep_with_next = True
    for name in ("Title", "Subtitle", "Heading 1"):
        for border in doc.styles[name].element.findall(".//" + qn("w:pBdr")):
            border.getparent().remove(border)
    for name, size in (("Table Text", 10.5), ("Article Note", 9.5)):
        style = doc.styles.add_style(name, 1)
        style.base_style = normal
        set_font(style, "Georgia", size)
        style.paragraph_format.line_spacing = 1.1
        style.paragraph_format.space_after = Pt(0 if name == "Table Text" else 8)
    doc.styles["Article Note"].paragraph_format.space_before = Pt(6)
    doc.add_paragraph(article["title"], "Title")
    doc.add_paragraph(article["subtitle"], "Subtitle")
    byline = doc.add_paragraph(f"By {article['author']}  |  {article['date']}")
    byline.runs[0].font.size = Pt(10)
    byline.paragraph_format.space_after = Pt(13)
    md = [f"# {article['title']}", "", article["subtitle"], "",
          f"*By {article['author']} · {article['date']}*", ""]
    built_rows = []
    body_words = 0
    for block in article["blocks"]:
        kind = block["type"]
        if kind == "h":
            assert re.fullmatch(r"[A-Za-z0-9 ]+", block["text"])
            doc.add_paragraph(block["text"], "Heading 1")
            md.append("## " + block["text"])
        elif kind in ("p", "note"):
            p = doc.add_paragraph(style="Article Note" if kind == "note" else "Normal")
            rich_text(p, block["text"])
            md.append(block["text"])
            body_words += len(LINK.sub(r"\1", block["text"]).split())
        elif kind == "steps":
            for i, text in enumerate(block["items"], 1):
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(.2)
                p.paragraph_format.first_line_indent = Inches(-.2)
                p.add_run(f"{i}. ")
                rich_text(p, text)
                md.append(f"{i}. {text}")
                body_words += len(text.split())
        elif kind == "leaderboard":
            cap = doc.add_paragraph(block["caption"])
            cap.runs[0].font.size = Pt(10.5)
            cap.runs[0].bold = True
            cap.paragraph_format.keep_with_next = True
            rows = table_rows(block, results)
            built_rows.extend(rows)
            add_table(doc, rows)
            md.extend([f"**{block['caption']}**", "",
                       "| Model tested | Group | WildGuard | HateXplain |",
                       "|---|---|---:|---:|"])
            md.extend("| " + " | ".join(row) + " |" for row in rows)
        else:
            raise ValueError(kind)
        md.append("")
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_font(doc.styles["Footer"], "Georgia", 9)
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    doc.core_properties.title = article["title"]
    doc.core_properties.author = article["author"]
    doc.core_properties.subject = "Engineering guide to policy-based text moderation"
    doc.core_properties.comments = ""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    md.extend(["[Editable Word version](output/policy-guardrails-engineering.docx)", ""])
    (ROOT / "README.md").write_text("\n".join(md))
    (ROOT / "generated").mkdir(exist_ok=True)
    manifest = {
        "article_sha256": hashlib.sha256(ARTICLE.read_bytes()).hexdigest(),
        "leaderboard_source": str(RESULTS.relative_to(REPO)),
        "leaderboard_sha256": hashlib.sha256(RESULTS.read_bytes()).hexdigest(),
        "body_words": body_words,
        "table": built_rows,
        "docx": str(OUT.relative_to(REPO)),
        "docx_sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
        "render_review_required": True,
    }
    (ROOT / "generated/build.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"docx": str(OUT), "body_words": body_words, "table_rows": len(built_rows)}))


if __name__ == "__main__":
    build()
