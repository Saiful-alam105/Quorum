"""Build the Quorum project-show slide deck (docs/presentation-slides.pptx).

Generates a native PowerPoint file (real text + tables, no rasterized slides)
using python-pptx. Run:  python scripts/build_slides.py
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "presentation-slides.pptx"

BG = RGBColor(0x0B, 0x0D, 0x12)
CARD = RGBColor(0x12, 0x15, 0x1C)
HEADER_CELL = RGBColor(0x1B, 0x1F, 0x2A)
BORDER = RGBColor(0x2A, 0x30, 0x40)
VIOLET = RGBColor(0xA5, 0x94, 0xF9)
VIOLET_DEEP = RGBColor(0x71, 0x60, 0xDC)
GREEN = RGBColor(0x3E, 0xCF, 0x6E)
TEXT = RGBColor(0xE8, 0xEC, 0xF3)
MUTED = RGBColor(0x8F, 0x96, 0xA6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREEN_SOFT = RGBColor(0x7E, 0xE2, 0xA8)

FONT = "Segoe UI"


def new_slide(prs: Presentation):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG
    return slide


def top_bar(slide) -> None:
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(6.667), Inches(0.12)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = VIOLET_DEEP
    bar.line.fill.background()
    bar2 = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(6.667), Inches(0), Inches(6.666), Inches(0.12)
    )
    bar2.fill.solid()
    bar2.fill.fore_color.rgb = GREEN
    bar2.line.fill.background()


def textbox(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    lines: list[tuple[str, int, bool, RGBColor, str]],
    anchor: str = "top",
) -> None:
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP if anchor == "top" else MSO_ANCHOR.MIDDLE
    for i, (text, size, bold, color, align) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER}[align]
        run = p.add_run()
        run.text = text
        run.font.name = FONT
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color
    return box


def title(slide, text: str) -> None:
    textbox(
        slide,
        0.6,
        0.5,
        12.1,
        0.9,
        [(text, 40, True, VIOLET, "l")],
    )


def add_table(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    headers: list[str],
    rows: list[list[str]],
    col_widths: list[float] | None = None,
    font_size: int = 15,
) -> None:
    shape = slide.shapes.add_table(
        len(rows) + 1, len(headers), Inches(x), Inches(y), Inches(w), Inches(h)
    )
    table = shape.table
    if col_widths:
        total = sum(col_widths)
        for i, cw in enumerate(col_widths):
            table.columns[i].width = Inches(w * cw / total)

    for j, header in enumerate(headers):
        cell = table.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = HEADER_CELL
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        run = p.add_run()
        run.text = header
        run.font.name = FONT
        run.font.size = Pt(font_size)
        run.font.bold = True
        run.font.color.rgb = VIOLET

    for i, row in enumerate(rows, start=1):
        for j, value in enumerate(row):
            cell = table.cell(i, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            run = p.add_run()
            run.text = value
            run.font.name = FONT
            run.font.size = Pt(font_size)
            run.font.bold = j == 0
            run.font.color.rgb = WHITE if j == 0 else TEXT

    for i in range(len(rows) + 1):
        for j in range(len(headers)):
            table.cell(i, j).fill.solid()


def bullets(slide, x: float, y: float, items: list[tuple[str, RGBColor, int, bool]]) -> None:
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(12.1), Inches(4.6))
    tf = box.text_frame
    tf.word_wrap = True
    for i, (text, color, size, bold) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(8)
        run = p.add_run()
        run.text = "•  " + text
        run.font.name = FONT
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color


def quote(slide, text: str, y: float = 5.9) -> None:
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(y), Inches(0.08), Inches(0.6))
    bar.fill.solid()
    bar.fill.fore_color.rgb = GREEN
    bar.line.fill.background()
    textbox(
        slide,
        0.85,
        y - 0.05,
        11.8,
        0.8,
        [(text, 20, False, GREEN_SOFT, "l")],
    )


def build() -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # ---- Slide 1: Title / Team ----
    slide = new_slide(prs)
    top_bar(slide)
    logo = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.09), Inches(0.8), Inches(1.15), Inches(1.15)
    )
    logo.fill.solid()
    logo.fill.fore_color.rgb = VIOLET_DEEP
    logo.line.fill.background()
    logo.adjustments[0] = 0.25
    ltf = logo.text_frame
    ltf.vertical_anchor = MSO_ANCHOR.MIDDLE
    lp = ltf.paragraphs[0]
    lp.alignment = PP_ALIGN.CENTER
    lrun = lp.add_run()
    lrun.text = "Q"
    lrun.font.name = FONT
    lrun.font.size = Pt(52)
    lrun.font.bold = True
    lrun.font.color.rgb = WHITE

    textbox(
        slide,
        0.6,
        2.15,
        12.1,
        1.0,
        [("Quorum", 54, True, VIOLET, "c")],
    )
    textbox(
        slide,
        0.6,
        3.15,
        12.1,
        0.6,
        [("AI-Powered GitHub Pull Request Reviewer", 22, False, MUTED, "c")],
    )
    textbox(
        slide,
        0.6,
        3.85,
        12.1,
        0.9,
        [
            ("Faculty:  Zobaer Ibn Razzaque", 16, False, TEXT, "c"),
            ("CSE 3422 Software Engineering Laboratory — Section C", 16, False, TEXT, "c"),
        ],
    )
    textbox(
        slide,
        0.6,
        5.15,
        12.1,
        0.5,
        [("Team Members", 20, True, WHITE, "c")],
    )
    add_table(
        slide,
        3.4,
        5.7,
        6.5,
        1.5,
        ["Member", "ID", "Role"],
        [
            ["Saiful Alam", "0112320105", "Backend, AI Analysis Pipeline, Web Dashboard"],
            ["Sabbir Ahmed", "011222279", "Documentation & Project Support"],
        ],
        col_widths=[1.4, 1.3, 2.4],
        font_size=13,
    )

    # ---- Slide 2: Introduction ----
    slide = new_slide(prs)
    top_bar(slide)
    title(slide, "Introduction")
    textbox(
        slide,
        0.6,
        1.6,
        12.1,
        0.6,
        [("The problem", 22, True, WHITE, "l")],
    )
    bullets(
        slide,
        0.6,
        2.2,
        [
            ("Merging code is risky — hidden bugs, security vulnerabilities, broken tests", TEXT, 18, False),
            ('"Looks fine to me" is not evidence', TEXT, 18, False),
        ],
    )
    textbox(
        slide,
        0.6,
        3.7,
        12.1,
        0.6,
        [("Quorum's answer", 22, True, WHITE, "l")],
    )
    bullets(
        slide,
        0.6,
        4.3,
        [
            ("Scans every Pull Request for security issues (Semgrep)", TEXT, 18, False),
            ("Writes real tests and runs them in a secure Docker sandbox", TEXT, 18, False),
            ("Measures test coverage automatically", TEXT, 18, False),
            ("Gives one clear, evidence-based answer: Merge Readiness Score 0–100", TEXT, 18, False),
        ],
    )
    quote(slide, "Turn \u201ctrust me\u201d into \u201cprove it.\u201d", 6.6)

    # ---- Slide 3: Feature Breakdown ----
    slide = new_slide(prs)
    top_bar(slide)
    title(slide, "Feature Breakdown")
    bullets(
        slide,
        0.6,
        1.6,
        [
            ("GitHub App + OAuth login — sign in with GitHub", TEXT, 18, False),
            ("Repository discovery — see all repos, one-click Connect / Disconnect", TEXT, 18, False),
            ("Create Pull Requests from Quorum — Base + Compare, suggested titles", TEXT, 18, False),
            ("Merge / Close PRs — no need to leave the app", TEXT, 18, False),
            ("AI Analysis Pipeline:", TEXT, 18, True),
            ("   Extract diff  →  Semgrep security scan  →  Security Agent (LLM)", TEXT, 17, False),
            ("   Generate tests  →  run in Docker sandbox  →  measure coverage", TEXT, 17, False),
            ("Merge Readiness Score 0–100 with an explainable breakdown", TEXT, 18, False),
            ("Auto review comment posted on the PR", TEXT, 18, False),
            ("Ask Quorum — evidence-grounded chatbot for each review", TEXT, 18, False),
        ],
    )

    # ---- Slide 4: What's different ----
    slide = new_slide(prs)
    top_bar(slide)
    title(slide, "What's Different from Other PR Review Apps")
    add_table(
        slide,
        0.6,
        1.7,
        12.1,
        4.4,
        ["Other AI reviewers", "Quorum"],
        [
            ["Just post an AI comment", "Generates & runs real tests, measures coverage"],
            ["LLM decides a score", "Deterministic 0–100 score with exact breakdown"],
            ["Findings can be hallucinated", "Every finding maps to real Semgrep evidence"],
            ["Only comments on GitHub", "Full workflow app — connect, create, merge, close"],
            ["Run code on your machine", "Runs in a hardened, sandboxed Docker container"],
            ["Generic chatbot", "Chatbot grounded only in that review's evidence"],
        ],
        col_widths=[1.3, 1.3],
        font_size=15,
    )

    # ---- Slide 5: Git / Timeline ----
    slide = new_slide(prs)
    top_bar(slide)
    title(slide, "Git — Timeline & Contribution")
    textbox(
        slide,
        0.6,
        1.5,
        12.1,
        0.6,
        [("Project timeline:  Aug 8 → Sep 29, 2026 (~7 weeks)   ·   196 commits", 18, True, WHITE, "l")],
    )
    add_table(
        slide,
        0.6,
        2.3,
        12.1,
        2.6,
        ["Member", "Commits", "Main contribution"],
        [
            ["Saiful Alam", "165", "Backend architecture, GitHub App/OAuth, AI pipeline (Semgrep, sandbox, scoring), dashboard, webhooks"],
            ["Sabbir Ahmed", "11", "Documentation, demo checklists, architecture & project-update docs"],
        ],
        col_widths=[1.3, 1.0, 3.6],
        font_size=15,
    )
    textbox(
        slide,
        0.6,
        5.4,
        12.1,
        0.6,
        [("Live demo: git log · GitHub Insights → Contributors", 16, False, MUTED, "l")],
    )

    # ---- Slide 6: Testing ----
    slide = new_slide(prs)
    top_bar(slide)
    title(slide, "Testing")
    bullets(
        slide,
        0.6,
        1.7,
        [
            ("Backend — pytest", TEXT, 20, True),
            ("   679 tests passing (webhooks, auth, API, pipeline stages, security, scoring, chat)", TEXT, 18, False),
            ("Frontend — npm test", TEXT, 20, True),
            ("   119 tests passing (Vitest + Testing Library)", TEXT, 18, False),
            ("Per-PR coverage — measured live inside the sandbox for every review", TEXT, 18, False),
        ],
    )
    textbox(
        slide,
        0.6,
        5.6,
        12.1,
        0.6,
        [("Live demo: run the suites in the terminal", 16, False, MUTED, "l")],
    )

    # ---- Slide 7: Thank You ----
    slide = new_slide(prs)
    top_bar(slide)
    textbox(
        slide,
        0.6,
        2.5,
        12.1,
        1.2,
        [("Thank You!", 60, True, VIOLET, "c")],
    )
    textbox(
        slide,
        0.6,
        3.9,
        12.1,
        0.9,
        [("Quorum — evidence-based Pull Request reviews, from 0 to 100.", 22, False, TEXT, "c")],
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)
    print(f"Saved {OUT}")


if __name__ == "__main__":
    build()