"""
Report extraction: DOCX, XLSX, PPTX and PDF.

Each exporter takes the filtered list of reports plus a title/subtitle and
returns a BytesIO ready for send_file().
"""
from collections import Counter
from datetime import datetime
from io import BytesIO

import config as C

COLUMNS = ["ID", "Report Type", "District", "Activity", "Date / Period", "Location",
           "Participants", "Issue Tags", "Status", "Submitted By", "Description"]

MIMETYPES = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "pdf":  "application/pdf",
}


def row(r):
    return [
        r.get("id"),
        C.REPORT_TYPE_LABEL.get(r.get("rtype"), r.get("rtype")),
        r.get("district") or "",
        r.get("activity") or "",
        r.get("period") or "",
        r.get("location") or "",
        r.get("participants_total") or 0,
        ", ".join(r.get("tags") or []),
        r.get("status") or "",
        r.get("submitted_by") or "",
        r.get("description") or "",
    ]


def participants_text(r):
    p = r.get("participants") or {}
    parts = [f"{C.PARTICIPANT_LABEL.get(k, k)}: {v}" for k, v in p.items() if k != "total" and v]
    return "; ".join(parts)


def _stamp():
    return datetime.now().strftime("%d %b %Y, %H:%M")


# ─────────────────────────────────────────────
# Excel
# ─────────────────────────────────────────────
def to_xlsx(reports, title, subtitle):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Reports"
    ws.append([title])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append([subtitle])
    ws.append([f"Generated {_stamp()} · {len(reports)} reports"])
    ws.append([])
    header = COLUMNS + ["Participant Breakdown", "Remarks", "Admin Comments"] + \
        [f"Detail: {f['label']}" for f in _all_detail_fields()]
    ws.append(header)
    fill = PatternFill("solid", fgColor="1A7A4A")
    for c in ws[5]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = fill
    for r in reports:
        details = r.get("details") or {}
        ws.append(row(r) + [participants_text(r), r.get("remarks") or "",
                            " | ".join(c["text"] for c in r.get("comments") or [])] +
                  [details.get(f["key"], "") for f in _all_detail_fields()])
    widths = [7, 20, 22, 34, 22, 18, 12, 34, 10, 18, 60, 40, 30, 40]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for row_cells in ws.iter_rows(min_row=6):
        for c in row_cells:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A6"

    # Summary sheet
    s = wb.create_sheet("Summary")
    s.append(["By District", "Reports"])
    for d, n in Counter(r.get("district") for r in reports).most_common():
        s.append([d, n])
    s.append([])
    s.append(["By Report Type", "Reports"])
    for t in C.REPORT_TYPES:
        s.append([t["label"], sum(1 for r in reports if r.get("rtype") == t["key"])])
    s.append([])
    s.append(["By Activity Type", "Reports"])
    for a in C.ACTIVITY_NAMES:
        s.append([a, sum(1 for r in reports if r.get("activity") == a)])
    s.append([])
    s.append(["By Issue Tag", "Reports"])
    for t in C.ISSUE_TAGS:
        s.append([t, sum(1 for r in reports if t in (r.get("tags") or []))])
    s.column_dimensions["A"].width = 48
    for c in s["A"]:
        if c.value and s.cell(row=c.row, column=2).value == "Reports":
            c.font = Font(bold=True)

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def _all_detail_fields():
    seen, out = set(), []
    for fields in C.ACTIVITY_FIELDS.values():
        for f in fields:
            if f["key"] not in seen:
                seen.add(f["key"])
                out.append(f)
    return out


# ─────────────────────────────────────────────
# Word
# ─────────────────────────────────────────────
def to_docx(reports, title, subtitle):
    from docx import Document
    from docx.enum.section import WD_ORIENT
    from docx.shared import Cm, Pt

    doc = Document()
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width, sec.page_height = sec.page_height, sec.page_width
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, side, Cm(1.5))

    doc.add_paragraph(C.ORG_NAME).runs[0].bold = True
    doc.add_heading(title, level=1)
    doc.add_paragraph(f"{subtitle}\nGenerated {_stamp()} · {len(reports)} reports")

    if len(reports) == 1:
        _docx_single(doc, reports[0])
    else:
        cols = ["ID", "Report Type", "District", "Activity", "Date / Period",
                "Participants", "Issue Tags", "Status"]
        t = doc.add_table(rows=1, cols=len(cols))
        t.style = "Light Grid Accent 1"
        for i, h in enumerate(cols):
            t.rows[0].cells[i].text = h
        for r in reports:
            vals = row(r)
            cells = t.add_row().cells
            for i, v in enumerate([vals[0], vals[1], vals[2], vals[3], vals[4],
                                   vals[6], vals[7], vals[8]]):
                cells[i].text = str(v)
        for tr in t.rows:
            for c in tr.cells:
                for p in c.paragraphs:
                    for run in p.runs:
                        run.font.size = Pt(9)

        doc.add_heading("Report descriptions", level=2)
        for r in reports:
            p = doc.add_paragraph()
            p.add_run(f"#{r['id']} · {r.get('district')} · {r.get('period')}: ").bold = True
            p.add_run(r.get("description") or "")

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


def _docx_single(doc, r):
    for label, val in zip(COLUMNS, row(r)):
        if label == "Description":
            continue
        p = doc.add_paragraph()
        p.add_run(f"{label}: ").bold = True
        p.add_run(str(val))
    if participants_text(r):
        p = doc.add_paragraph()
        p.add_run("Participant breakdown: ").bold = True
        p.add_run(participants_text(r))
    for f in C.ACTIVITY_FIELDS.get(r.get("activity"), []):
        v = (r.get("details") or {}).get(f["key"])
        if v:
            p = doc.add_paragraph()
            p.add_run(f"{f['label']}: ").bold = True
            p.add_run(str(v))
    doc.add_heading("Description", level=2)
    doc.add_paragraph(r.get("description") or "")
    if r.get("remarks"):
        doc.add_heading("Remarks", level=2)
        doc.add_paragraph(r["remarks"])
    if r.get("comments"):
        doc.add_heading("Admin comments", level=2)
        for c in r["comments"]:
            doc.add_paragraph(f"{c.get('by')} ({str(c.get('at'))[:10]}): {c.get('text')}")
    files = (r.get("attachments") or []) + (r.get("archive_refs") or [])
    if files:
        doc.add_heading("Attachments", level=2)
        for f in files:
            doc.add_paragraph(f"{f.get('name')}", style="List Bullet")


# ─────────────────────────────────────────────
# PowerPoint
# ─────────────────────────────────────────────
def to_pptx(reports, title, subtitle):
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.dml.color import RGBColor
    from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
    from pptx.util import Inches, Pt

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    green = RGBColor(0x1A, 0x7A, 0x4A)

    s = prs.slides.add_slide(prs.slide_layouts[0])
    s.shapes.title.text = title
    s.placeholders[1].text = f"{C.ORG_NAME}\n{subtitle}\nGenerated {_stamp()} · {len(reports)} reports"

    def chart_slide(heading, pairs, kind=XL_CHART_TYPE.BAR_CLUSTERED):
        sl = prs.slides.add_slide(prs.slide_layouts[5])
        sl.shapes.title.text = heading
        cd = CategoryChartData()
        cd.categories = [p[0] for p in pairs]
        cd.add_series("Reports", [p[1] for p in pairs])
        gf = sl.shapes.add_chart(kind, Inches(0.7), Inches(1.4), Inches(12), Inches(5.8), cd)
        ch = gf.chart
        ch.has_legend = False
        plot = ch.plots[0]
        plot.has_data_labels = True                 # values shown on the chart itself
        plot.data_labels.font.size = Pt(12)
        plot.data_labels.number_format = "0"
        plot.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
        plot.series[0].format.fill.solid()
        plot.series[0].format.fill.fore_color.rgb = green
        ch.category_axis.tick_labels.font.size = Pt(11)

    dist = Counter(r.get("district") for r in reports)
    chart_slide("Reports by District", [(d, dist.get(d, 0)) for d in reversed(C.PERIODIC_DISTRICTS)])
    acts = Counter(r.get("activity") for r in reports)
    chart_slide("Reports by Activity Type",
                [(C.ACTIVITY_SHORT[a], acts.get(a, 0)) for a in reversed(C.ACTIVITY_NAMES)])
    chart_slide("Reports by Report Type",
                [(t["label"], sum(1 for r in reports if r.get("rtype") == t["key"]))
                 for t in C.REPORT_TYPES], XL_CHART_TYPE.COLUMN_CLUSTERED)

    cols = ["ID", "Type", "District", "Activity", "Date / Period", "Participants", "Status"]
    widths = [0.7, 1.4, 2.4, 3.6, 2.0, 1.2, 1.2]
    per = 12
    for start in range(0, len(reports), per):
        chunk = reports[start:start + per]
        sl = prs.slides.add_slide(prs.slide_layouts[5])
        sl.shapes.title.text = f"Reports {start + 1}–{start + len(chunk)} of {len(reports)}"
        tbl = sl.shapes.add_table(len(chunk) + 1, len(cols), Inches(0.4), Inches(1.4),
                                  Inches(sum(widths)), Inches(0.4 * (len(chunk) + 1))).table
        for i, w in enumerate(widths):
            tbl.columns[i].width = Inches(w)
        for i, h in enumerate(cols):
            tbl.cell(0, i).text = h
        for ri, r in enumerate(chunk, 1):
            v = row(r)
            for ci, val in enumerate([v[0], C.REPORT_TYPE_SHORT.get(r.get("rtype")), v[2],
                                      v[3], v[4], v[6], v[8]]):
                tbl.cell(ri, ci).text = str(val)
        for rr in tbl.rows:
            for c in rr.cells:
                for p in c.text_frame.paragraphs:
                    for run in p.runs:
                        run.font.size = Pt(11)

    buf = BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf


# ─────────────────────────────────────────────
# PDF
# ─────────────────────────────────────────────
def to_pdf(reports, title, subtitle):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from xml.sax.saxutils import escape

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=1.2 * cm,
                            rightMargin=1.2 * cm, topMargin=1.2 * cm, bottomMargin=1.2 * cm,
                            title=title)
    ss = getSampleStyleSheet()
    small = ss["BodyText"].clone("small", fontSize=8, leading=10)
    story = [Paragraph(escape(C.ORG_NAME), ss["Normal"]),
             Paragraph(escape(title), ss["Title"]),
             Paragraph(escape(f"{subtitle} · Generated {_stamp()} · {len(reports)} reports"),
                       ss["Normal"]),
             Spacer(1, 10)]
    cols = ["ID", "Type", "District", "Activity", "Date / Period", "Part.", "Issue Tags",
            "Status", "Description"]
    data = [cols]
    for r in reports:
        v = row(r)
        data.append([Paragraph(escape(str(x)), small) for x in
                     [v[0], C.REPORT_TYPE_SHORT.get(r.get("rtype")), v[2], v[3], v[4], v[6],
                      v[7], v[8], v[10]]])
    widths = [1.1, 1.8, 3.0, 4.0, 2.4, 1.1, 4.0, 1.7, 8.2]
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A7A4A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D4E4DA")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F7F5")]),
    ]))
    story.append(t)
    doc.build(story)
    buf.seek(0)
    return buf


EXPORTERS = {"docx": to_docx, "xlsx": to_xlsx, "pptx": to_pptx, "pdf": to_pdf}
