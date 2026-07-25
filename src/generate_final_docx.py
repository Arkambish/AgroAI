"""Generate the FYP **Final Report** as a .docx conforming to the University of
Moratuwa, Faculty of IT guidelines (Karunananda 2006).

Produces: outputs/Final_Report_AgroAI.docx

Layout per guideline:
- A4, Times New Roman 12pt body, 1.5 line spacing
- Margins: left 1.5", top/right/bottom 1"
- Cover page + Title page (no page numbers)
- Pre-pages in lower-case Roman numerals (Abstract, Acknowledgements, Contents,
  List of Figures, List of Tables)
- Body in Arabic numerals starting at 1, page number centred at the bottom
- Chapter headings 18pt bold; section/subsection headings 12pt bold
- Every chapter opens with an "Introduction" section and closes with a "Summary"
- Citations [n] in text; reference list sorted alphabetically by first author
- Appendix A is "Individual's Contribution to the Project" (a full page each)

All quantitative results in this report come from the REAL collected dataset
(outputs/results_real/, 28 seasonal records). Synthetic-pipeline numbers appear
only where they are explicitly labelled as an architecture-validation reference.

Usage:  python src/generate_final_docx.py
"""

from __future__ import annotations

import os
import re
from typing import Iterable

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_BREAK
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Inches, Pt, RGBColor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, "outputs", "Final_Report_AgroAI.docx")

BODY_FONT = "Times New Roman"


# ---------- Low-level Word plumbing -----------------------------------------

def _add_field(paragraph, instr_text: str) -> None:
    """Insert a Word field (e.g. PAGE) into the given paragraph."""
    run = paragraph.add_run()
    fld_char_begin = OxmlElement("w:fldChar")
    fld_char_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instr_text
    fld_char_separate = OxmlElement("w:fldChar")
    fld_char_separate.set(qn("w:fldCharType"), "separate")
    fld_char_end = OxmlElement("w:fldChar")
    fld_char_end.set(qn("w:fldCharType"), "end")
    r = run._r
    r.append(fld_char_begin)
    r.append(instr)
    r.append(fld_char_separate)
    r.append(fld_char_end)


def _set_section_page_numbering(section, *, fmt: str, start: int | None = None) -> None:
    """fmt: 'decimal' | 'lowerRoman' | 'none'."""
    sect_pr = section._sectPr
    for existing in sect_pr.findall(qn("w:pgNumType")):
        sect_pr.remove(existing)
    pg_num_type = OxmlElement("w:pgNumType")
    pg_num_type.set(qn("w:fmt"), fmt)
    if start is not None:
        pg_num_type.set(qn("w:start"), str(start))
    sect_pr.append(pg_num_type)


def _configure_document(doc: Document) -> None:
    section = doc.sections[0]
    section.page_height = Inches(11.69)
    section.page_width = Inches(8.27)
    section.left_margin = Inches(1.5)
    section.right_margin = Inches(1.0)
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.header_distance = Inches(0.5)
    section.footer_distance = Inches(0.5)
    section.different_first_page_header_footer = True

    normal = doc.styles["Normal"]
    normal.font.name = BODY_FONT
    normal.font.size = Pt(12)
    pf = normal.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_after = Pt(6)


# ---------- Content primitives ----------------------------------------------

def _add_centered_runs(doc: Document, items: Iterable[tuple[str, int, bool]]) -> None:
    for text, size, bold in items:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.font.name = BODY_FONT
        run.font.size = Pt(size)
        run.font.bold = bold


def _spacer(doc: Document, blank_lines: int = 1) -> None:
    for _ in range(blank_lines):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)


def _heading(doc: Document, text: str, *, level: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    if level == "chapter":
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(12)
        size, bold = 18, True
    else:
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(6)
        size, bold = 12, True
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = BODY_FONT


def _chapter_title(doc: Document, number: str, title: str) -> None:
    """Guideline Appendix A layout: right-aligned 'Chapter N', then the title."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.space_after = Pt(18)
    run = p.add_run(f"Chapter {number}")
    run.font.size = Pt(18)
    run.font.bold = True
    run.font.name = BODY_FONT
    _heading(doc, title, level="chapter")


def _para(doc: Document, text: str, *, justify: bool = True) -> None:
    p = doc.add_paragraph()
    if justify:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = p.add_run(text)
    run.font.name = BODY_FONT
    run.font.size = Pt(12)


def _bullet(doc: Document, text: str) -> None:
    p = doc.add_paragraph(style="List Bullet")
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = p.add_run(text)
    run.font.name = BODY_FONT
    run.font.size = Pt(12)


def _code(doc: Document, text: str) -> None:
    """Monospaced listing block (used inside appendices)."""
    for line in text.split("\n"):
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.left_indent = Inches(0.3)
        run = p.add_run(line if line else " ")
        run.font.name = "Courier New"
        run.font.size = Pt(9)


def _figure(doc: Document, image_path: str, caption: str, *, width_inches: float = 5.5) -> None:
    if not os.path.exists(image_path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"[Figure asset missing: {os.path.relpath(image_path, ROOT)}]")
        run.italic = True
        run.font.name = BODY_FONT
        run.font.size = Pt(11)
    else:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(image_path, width=Inches(width_inches))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap_run = cap.add_run(caption)
    cap_run.font.name = BODY_FONT
    cap_run.font.size = Pt(11)
    cap_run.italic = True
    cap.paragraph_format.space_after = Pt(12)


def _placeholder(doc: Document, label: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"[ Insert screenshot here — {label} ]")
    run.italic = True
    run.font.name = BODY_FONT
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0x88, 0x88, 0x88)
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(18)


def _page_break(doc: Document) -> None:
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)


def _section_break(doc: Document):
    new_section = doc.add_section(WD_SECTION.NEW_PAGE)
    new_section.page_height = Inches(11.69)
    new_section.page_width = Inches(8.27)
    new_section.left_margin = Inches(1.5)
    new_section.right_margin = Inches(1.0)
    new_section.top_margin = Inches(1.0)
    new_section.bottom_margin = Inches(1.0)
    return new_section


def _add_centered_footer_pagenum(section, fmt: str, start: int | None = None) -> None:
    _set_section_page_numbering(section, fmt=fmt, start=start)
    footer = section.footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.text = ""
    _add_field(p, "PAGE")


def _add_table(doc: Document, header: list[str], rows: list[list[str]], caption: str) -> None:
    """Caption ABOVE the table, per the guideline sample (Appendix B)."""
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = cap.add_run(caption)
    cr.italic = True
    cr.font.name = BODY_FONT
    cr.font.size = Pt(11)
    cap.paragraph_format.space_before = Pt(12)
    cap.paragraph_format.space_after = Pt(6)
    cap.paragraph_format.keep_with_next = True

    table = doc.add_table(rows=1 + len(rows), cols=len(header))
    table.style = "Table Grid"
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for j, h in enumerate(header):
        cell = table.rows[0].cells[j]
        cell.text = ""
        run = cell.paragraphs[0].add_run(h)
        run.font.bold = True
        run.font.name = BODY_FONT
        run.font.size = Pt(10)
        cell.paragraphs[0].paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        cell.paragraphs[0].paragraph_format.space_after = Pt(2)
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            cell = table.rows[i].cells[j]
            cell.text = ""
            run = cell.paragraphs[0].add_run(val)
            run.font.name = BODY_FONT
            run.font.size = Pt(10)
            cell.paragraphs[0].paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
            cell.paragraphs[0].paragraph_format.space_after = Pt(2)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)


_CITE_RE = re.compile(r"\[(\d+)\]")
_CITE_MAP: dict[int, int] = {}


def citation_order(chapters: list[list[tuple]]) -> list[int]:
    """Authoring numbers in order of first citation across the body text.

    Code blocks are excluded because they contain literal square brackets that
    are not citations.
    """
    seen: list[int] = []
    for chapter in chapters:
        for kind, payload in chapter:
            if kind in ("p", "bullet", "h2", "h3"):
                texts = [payload]
            elif kind == "table":
                texts = [v for row in payload[1] for v in row]
            else:
                continue
            for text in texts:
                for n in (int(x) for x in _CITE_RE.findall(text)):
                    if n not in seen:
                        seen.append(n)
    return seen


def build_citation_map(ordered: list[tuple]) -> dict[int, int]:
    """Map each reference's authoring number onto its emitted number.

    The prose is authored against stable numbers; the emitted numbers depend on
    whether the list is ordered alphabetically (Faculty guideline) or by first
    citation (strict IEEE). This map keeps the in-text citations correct either
    way. `ordered` is the reference list already in emission order.
    """
    return {num: i for i, (num, _key, _text) in enumerate(ordered, start=1)}


def _renumber(text: str) -> str:
    """Rewrite [n] citation tokens using the alphabetical-order numbering."""
    if not _CITE_MAP:
        return text
    return _CITE_RE.sub(
        lambda m: f"[{_CITE_MAP.get(int(m.group(1)), m.group(1))}]", text
    )


def _emit(doc: Document, items: list[tuple]) -> None:
    """Render a chapter defined as a list of (kind, payload) tuples.

      ("chapter", ("1", "Introduction"))   chapter number + title block
      ("h2", "1.1 Introduction")           section heading
      ("h3", "1.2.1 Sub-section")          subsection heading
      ("p",  "Long paragraph ...")
      ("bullet", "list item")
      ("code", "listing text")
      ("fig", ("path", "Figure 3.1: Caption"))
      ("table", (header, rows, "Table 3.1: Caption"))
      ("ph", "screenshot label")
      ("pagebreak", None)
    """
    for kind, payload in items:
        if kind == "chapter":
            number, title = payload
            _chapter_title(doc, number, title)
        elif kind == "h1":
            _heading(doc, payload, level="chapter")
        elif kind == "h2":
            _heading(doc, payload, level="section")
        elif kind == "h3":
            _heading(doc, payload, level="subsection")
        elif kind == "p":
            _para(doc, _renumber(payload))
        elif kind == "bullet":
            _bullet(doc, _renumber(payload))
        elif kind == "code":
            _code(doc, payload)  # never renumbered: code contains literal brackets
        elif kind == "fig":
            path, caption = payload
            _figure(doc, os.path.join(ROOT, path), caption)
        elif kind == "table":
            header, rows, caption = payload
            _add_table(doc, header,
                       [[_renumber(v) for v in row] for row in rows], caption)
        elif kind == "ph":
            _placeholder(doc, payload)
        elif kind == "pagebreak":
            _page_break(doc)
        else:
            raise ValueError(f"Unknown emit kind: {kind}")


# ---------- Cover and title pages -------------------------------------------

GROUP_MEMBERS = [
    ("214019K", "Arkam B.H.M."),
    ("214192G", "Sharuja B."),
    ("214193K", "Shathurya P."),
]

PROJECT_TITLE_LINE_1 = "AI-Powered Harvest Yield Prediction"
PROJECT_TITLE_LINE_2 = "for Non-Cash Crops (Big Onion) in Sri Lanka"
SUPERVISOR = "Dr. Firdhous M.F.M."


def _add_member_table(doc: Document) -> None:
    table = doc.add_table(rows=len(GROUP_MEMBERS), cols=2)
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for i, (idx, name) in enumerate(GROUP_MEMBERS):
        c0, c1 = table.cell(i, 0), table.cell(i, 1)
        c0.text = idx
        c1.text = name
        for c in (c0, c1):
            c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            for para in c.paragraphs:
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in para.runs:
                    run.font.name = BODY_FONT
                    run.font.size = Pt(12)
    for row in table.rows:
        for cell in row.cells:
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_borders = OxmlElement("w:tcBorders")
            for edge in ("top", "left", "bottom", "right"):
                b = OxmlElement(f"w:{edge}")
                b.set(qn("w:val"), "nil")
                tc_borders.append(b)
            tc_pr.append(tc_borders)


def _front_matter_block(doc: Document, *, with_supervisor: bool) -> None:
    _spacer(doc, 3)
    _add_centered_runs(doc, [("Final Report", 16, True)])
    _spacer(doc, 1)
    _add_centered_runs(doc, [("Level 4", 14, True)])
    _spacer(doc, 4)
    _add_centered_runs(doc, [(PROJECT_TITLE_LINE_1, 14, True),
                             (PROJECT_TITLE_LINE_2, 14, True)])
    _spacer(doc, 4)
    _add_centered_runs(doc, [("Group Name: Agro AI", 12, False)])
    _spacer(doc, 1)
    _add_member_table(doc)
    if with_supervisor:
        _spacer(doc, 2)
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r1 = p.add_run("Supervised by: ")
        r1.font.bold = True
        r1.font.name = BODY_FONT
        r1.font.size = Pt(12)
        r2 = p.add_run(SUPERVISOR)
        r2.font.name = BODY_FONT
        r2.font.size = Pt(12)
        _spacer(doc, 3)
    else:
        _spacer(doc, 5)
    _add_centered_runs(doc, [("Faculty of Information Technology", 12, False),
                             ("University of Moratuwa", 12, False),
                             ("2026", 12, False)])


def add_cover_page(doc: Document) -> None:
    _front_matter_block(doc, with_supervisor=False)
    _page_break(doc)


def add_title_page(doc: Document) -> None:
    _front_matter_block(doc, with_supervisor=True)


# ---------- Pre-pages --------------------------------------------------------

ABSTRACT_TEXT = (
    "Sri Lanka consumes roughly 220,000 metric tons of big onion (Allium cepa) "
    "each year while domestic cultivation supplies only part of that demand, so "
    "the balance is imported at a substantial foreign-exchange cost. Unlike "
    "paddy, big onion has no systematic crop-cutting survey methodology, which "
    "means yield figures are compiled from subjective field assessments and only "
    "become available after the harvest is already in. This project designs, "
    "implements and evaluates an artificial-intelligence system that forecasts "
    "big onion yield before harvest for the four major producing districts of "
    "Matale, Anuradhapura, Polonnaruwa and Kurunegala. The system serves the "
    "Department of Census and Statistics, the Department of Agriculture, "
    "district agricultural officers and farmer organisations. It ingests four "
    "data streams — historical district yield records, daily weather "
    "observations, satellite-derived vegetation and land-surface-temperature "
    "indices, and gridded soil properties — aggregates them to one record per "
    "district, season and year, and engineers thirty-two predictors spanning "
    "weather aggregates, vegetation dynamics, yield history, soil and "
    "interaction terms. Nine predictors are produced by models trained and "
    "compared under a single protocol: Random Forest, XGBoost and Support "
    "Vector Regression; LSTM, Bidirectional LSTM, one-dimensional CNN and a "
    "hybrid CNN-LSTM with explicit season-indicator injection; a symbolic "
    "regression model that returns a readable closed-form equation; and a "
    "physics-residual hybrid that couples a calibrated agronomic water-heat-"
    "thermal-time backbone with a learned residual correction. A constrained "
    "convex stacking layer combines them. Every model is evaluated with "
    "Leave-One-Year-Out cross-validation, paired statistical significance "
    "testing and split-conformal prediction intervals, so that no result "
    "depends on a single arbitrary train-test split. On the twenty-eight "
    "seasonal records that were actually collected, the physics-residual hybrid "
    "is the strongest model with a coefficient of determination of 0.091 and a "
    "root mean squared error of 3.90 metric tons per hectare, ahead of Random "
    "Forest at 0.020, while every deep model falls below the mean predictor. "
    "The measured outcome is that at this sample size the mechanistic prior and "
    "the evaluation protocol carry the result, not model capacity. Predictions, "
    "comparison metrics, the symbolic equation, calibrated intervals and SHAP "
    "attributions are served over a Flask REST interface and presented in a "
    "Next.js decision-support dashboard."
)

ACKNOWLEDGEMENTS_TEXT = (
    "We extend our sincere gratitude to our supervisor, Dr. Firdhous M.F.M. of "
    "the Faculty of Information Technology, University of Moratuwa, for his "
    "guidance, patience and continued support throughout this project. We are "
    "grateful to the Department of Census and Statistics of Sri Lanka for "
    "publishing the big onion survey reports, to the Department of Agriculture "
    "for the HORDI cultivation guidelines that shaped our agronomic "
    "assumptions, to NASA POWER and the Climate Hazards Group for open access "
    "to weather and rainfall records, to the European Space Agency Copernicus "
    "programme and the MODIS Science Team for satellite imagery, and to the "
    "ISRIC SoilGrids team for global soil property maps. We also thank the "
    "Faculty of Information Technology for providing the academic environment "
    "and computing facilities that made this work possible, and our families "
    "and colleagues for their encouragement over the course of the year."
)

TOC_ENTRIES = [
    ("Abstract", "i"),
    ("Acknowledgements", "ii"),
    ("Contents", "iii"),
    ("List of Figures", "vi"),
    ("List of Tables", "vii"),
    ("Chapter 1 — Forecasting Big Onion Yield in Sri Lanka", "1"),
    ("    1.1 Introduction", "1"),
    ("    1.2 Background and Motivation", "2"),
    ("    1.3 Aim and Objectives", "5"),
    ("    1.4 The Proposed Solution", "6"),
    ("    1.5 Structure of the Report", "8"),
    ("    1.6 Summary", "9"),
    ("Chapter 2 — Crop Yield Prediction: A Review of Others' Work", "10"),
    ("    2.1 Introduction", "10"),
    ("    2.2 Classical Machine Learning for Yield Prediction", "10"),
    ("    2.3 Deep Learning and Hybrid Architectures", "13"),
    ("    2.4 Mechanistic and Hybrid Process-Based Models", "15"),
    ("    2.5 Yield Prediction Research in Sri Lanka", "17"),
    ("    2.6 Onion-Specific Research", "18"),
    ("    2.7 Comparison of Existing Approaches", "19"),
    ("    2.8 Research Gaps Identified", "21"),
    ("    2.9 Summary", "23"),
    ("Chapter 3 — Technologies Adapted for Data-Scarce Yield Prediction", "24"),
    ("    3.1 Introduction", "24"),
    ("    3.2 Data Acquisition Technologies", "24"),
    ("    3.3 Classical Machine Learning Technologies", "27"),
    ("    3.4 Deep Learning Technologies", "29"),
    ("    3.5 Symbolic Regression", "31"),
    ("    3.6 Physics-Informed Residual Modelling", "32"),
    ("    3.7 Ensemble Stacking", "34"),
    ("    3.8 Conformal Prediction and Explainability", "35"),
    ("    3.9 Evaluation Technology: Leave-One-Year-Out CV", "37"),
    ("    3.10 Software and Tools", "38"),
    ("    3.11 Summary", "39"),
    ("Chapter 4 — The Agro AI Approach", "40"),
    ("    4.1 Introduction", "40"),
    ("    4.2 Users", "40"),
    ("    4.3 Inputs and Outputs", "42"),
    ("    4.4 Process: The Nine-Stage Pipeline", "44"),
    ("    4.5 Top-Level System Architecture", "47"),
    ("    4.6 Walkthrough of a Single Prediction", "49"),
    ("    4.7 System Requirements", "50"),
    ("    4.8 Summary", "51"),
    ("Chapter 5 — Analysis and Design of the Prediction System", "52"),
    ("    5.1 Introduction", "52"),
    ("    5.2 Data Flow Design", "52"),
    ("    5.3 Feature Engineering Design", "54"),
    ("    5.4 Classical Model Design", "57"),
    ("    5.5 Deep Model Design and the Hybrid CNN-LSTM", "58"),
    ("    5.6 Physics-Residual Hybrid Design", "61"),
    ("    5.7 Stacking Layer Design", "63"),
    ("    5.8 Uncertainty and Explainability Design", "64"),
    ("    5.9 Serving and Dashboard Design", "65"),
    ("    5.10 Summary", "67"),
    ("Chapter 6 — Implementation", "68"),
    ("    6.1 Introduction", "68"),
    ("    6.2 Repository Layout and Tooling", "68"),
    ("    6.3 Data Loading and Preprocessing", "70"),
    ("    6.4 Feature Engineering", "72"),
    ("    6.5 Classical Model Implementation", "73"),
    ("    6.6 Deep Model Implementation", "75"),
    ("    6.7 Symbolic Regression Implementation", "77"),
    ("    6.8 Physics-Residual Implementation", "78"),
    ("    6.9 Stacking, Conformal and SHAP Implementation", "80"),
    ("    6.10 Ablation Study Implementation", "82"),
    ("    6.11 Serving Layer and Dashboard", "83"),
    ("    6.12 Summary", "85"),
    ("Chapter 7 — Evaluation and Results", "86"),
    ("    7.1 Introduction", "86"),
    ("    7.2 The Evaluation Dataset", "86"),
    ("    7.3 Evaluation Protocol and Metrics", "88"),
    ("    7.4 Model Comparison Results", "90"),
    ("    7.5 Does the Mechanistic Backbone Help?", "93"),
    ("    7.6 Does Stacking Help?", "95"),
    ("    7.7 The Symbolic Equation", "97"),
    ("    7.8 Data-Source Ablation", "98"),
    ("    7.9 Per-District Behaviour", "100"),
    ("    7.10 Calibrated Uncertainty", "101"),
    ("    7.11 Feature Attribution", "103"),
    ("    7.12 Architecture Validation on Synthetic Data", "105"),
    ("    7.13 Summary", "107"),
    ("Chapter 8 — Discussion, Conclusion and Further Work", "108"),
    ("    8.1 Introduction", "108"),
    ("    8.2 Interpretation of the Results", "108"),
    ("    8.3 How This Work Differs from Others", "111"),
    ("    8.4 Contributions of This Research", "113"),
    ("    8.5 Threats to Validity and Limitations", "115"),
    ("    8.6 Further Work", "117"),
    ("    8.7 Conclusion", "119"),
    ("    8.8 Summary", "120"),
    ("References", "121"),
    ("Appendix A — Individual's Contribution to the Project", "125"),
    ("Appendix B — Configuration and Code Excerpts", "129"),
    ("Appendix C — Extended Result Tables", "134"),
    ("Appendix D — Dashboard Screenshots", "138"),
]

FIGURE_LIST = [
    ("Figure 4.1 — Top-level architecture of the proposed system", "48"),
    ("Figure 4.2 — The nine-stage processing pipeline", "46"),
    ("Figure 5.1 — Data flow through the prediction system", "53"),
    ("Figure 5.2 — Hybrid CNN-LSTM architecture with season-indicator injection", "60"),
    ("Figure 5.3 — Logical data schema of the processed store", "66"),
    ("Figure 6.1 — Training curve of the hybrid CNN-LSTM on the collected data", "76"),
    ("Figure 7.1 — Model comparison on the collected dataset", "91"),
    ("Figure 7.2 — Actual against predicted yield, Random Forest", "92"),
    ("Figure 7.3 — Residual distribution, Random Forest", "93"),
    ("Figure 7.4 — Data-source ablation on the collected dataset", "99"),
    ("Figure 7.5 — SHAP mean absolute attribution, top fifteen predictors", "103"),
    ("Figure 7.6 — SHAP summary plot", "104"),
    ("Figure 7.7 — SHAP dependence for the temperature-humidity interaction", "105"),
    ("Figure 7.8 — Model comparison on the synthetic reference dataset", "106"),
]

TABLE_LIST = [
    ("Table 2.1 — Comparison of existing yield-prediction approaches", "20"),
    ("Table 3.1 — Data sources adopted by the system", "25"),
    ("Table 3.2 — Software and tools", "38"),
    ("Table 4.1 — User groups and their information needs", "41"),
    ("Table 4.2 — System inputs and outputs", "43"),
    ("Table 5.1 — The thirty-two engineered predictors by group", "55"),
    ("Table 5.2 — Model inventory and design rationale", "57"),
    ("Table 6.1 — Pipeline modules and their source files", "69"),
    ("Table 6.2 — REST endpoints exposed by the serving layer", "84"),
    ("Table 7.1 — Composition of the collected evaluation dataset", "87"),
    ("Table 7.2 — Model comparison under Leave-One-Year-Out CV", "90"),
    ("Table 7.3 — Physics-residual with and without the mechanistic backbone", "94"),
    ("Table 7.4 — Stacking combiners and their learned weights", "96"),
    ("Table 7.5 — Data-source ablation results", "98"),
    ("Table 7.6 — Per-district predictability", "100"),
    ("Table 7.7 — Split-conformal interval half-widths at ninety per cent", "102"),
    ("Table 7.8 — Synthetic-data model comparison (architecture validation)", "106"),
    ("Table 8.1 — Positioning against the closest prior work", "112"),
    ("Table A.1 — Distribution of individual contributions", "128"),
    ("Table C.1 — Fold-by-fold errors for the physics-residual hybrid", "134"),
    ("Table C.2 — Full SHAP attribution ranking", "136"),
]


def _dotted_entry(doc: Document, label: str, page: str, *, bold: bool) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.tab_stops.add_tab_stop(Inches(5.4), WD_ALIGN_PARAGRAPH.RIGHT, leader=2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    run = p.add_run(label)
    run.font.name = BODY_FONT
    run.font.size = Pt(12)
    run.font.bold = bold
    p.add_run("\t").font.name = BODY_FONT
    page_run = p.add_run(page)
    page_run.font.name = BODY_FONT
    page_run.font.size = Pt(12)
    page_run.font.bold = bold


def _prepage_heading(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.font.bold = True
    run.font.size = Pt(16)
    run.font.name = BODY_FONT
    p.paragraph_format.space_after = Pt(18)


def add_pre_pages(doc: Document) -> None:
    _prepage_heading(doc, "Abstract")
    _para(doc, ABSTRACT_TEXT)
    _page_break(doc)

    _prepage_heading(doc, "Acknowledgements")
    _para(doc, ACKNOWLEDGEMENTS_TEXT)
    _page_break(doc)

    _prepage_heading(doc, "Contents")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run("Page")
    r.font.name = BODY_FONT
    r.font.size = Pt(12)
    for label, page in TOC_ENTRIES:
        _dotted_entry(doc, label, page, bold=not label.startswith("    "))
    _page_break(doc)

    _prepage_heading(doc, "List of Figures")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run("Page")
    r.font.name = BODY_FONT
    r.font.size = Pt(12)
    for label, page in FIGURE_LIST:
        _dotted_entry(doc, label, page, bold=False)
    _page_break(doc)

    _prepage_heading(doc, "List of Tables")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run("Page")
    r.font.name = BODY_FONT
    r.font.size = Pt(12)
    for label, page in TABLE_LIST:
        _dotted_entry(doc, label, page, bold=False)


# ---------- Build ------------------------------------------------------------

def build() -> str:
    import final_report_content as C

    # Resolve in-text citation numbers against the emitted reference order
    # before any prose is emitted.
    order = citation_order(C.ALL_CHAPTERS)
    _CITE_MAP.clear()
    _CITE_MAP.update(build_citation_map(C.ordered_references(order)))

    doc = Document()
    _configure_document(doc)

    # Section 1 — cover + title page, no page numbers.
    add_cover_page(doc)
    add_title_page(doc)
    _set_section_page_numbering(doc.sections[0], fmt="decimal")
    doc.sections[0].footer.is_linked_to_previous = False

    # Section 2 — pre-pages, lower-case Roman numerals restarting at i.
    pre_section = _section_break(doc)
    pre_section.different_first_page_header_footer = False
    _add_centered_footer_pagenum(pre_section, "lowerRoman", start=1)
    add_pre_pages(doc)

    # Section 3 — body, Arabic numerals restarting at 1.
    body_section = _section_break(doc)
    body_section.different_first_page_header_footer = False
    _add_centered_footer_pagenum(body_section, "decimal", start=1)

    for chapter in C.ALL_CHAPTERS:
        _emit(doc, chapter)
        _page_break(doc)

    C.add_references(doc, _heading, lambda d, t: _para(d, _renumber(t)),
                     _page_break, BODY_FONT, citation_order=order)
    for appendix in C.ALL_APPENDICES:
        _emit(doc, appendix)
        _page_break(doc)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    doc.save(OUT_PATH)
    return OUT_PATH


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    path = build()
    print(f"Final report written to: {path}")
