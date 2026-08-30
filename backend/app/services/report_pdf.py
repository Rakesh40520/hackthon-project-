"""PDF report generation."""
from __future__ import annotations

import io
from datetime import datetime
from typing import Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models import ProcurementProject, Proposal, Requirement, RequirementEvaluation


def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle(name="H1Center", parent=s["Title"], alignment=1))
    s.add(ParagraphStyle(name="Subtle", parent=s["BodyText"], textColor=colors.grey))
    return s


def generate_pdf_report(
    project: ProcurementProject,
    proposals: List[Proposal],
    requirements: List[Requirement],
    evaluations: Dict[str, List[RequirementEvaluation]],
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, title=f"Procurement Report - {project.name}")
    styles = _styles()
    story: list = []

    story.append(Paragraph(f"Procurement Report: {project.name}", styles["H1Center"]))
    story.append(Paragraph(f"Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["Subtle"]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>Executive Summary</b>", styles["Heading2"]))
    eligible = [p for p in proposals if p.score and p.score.is_eligible]
    ineligible = [p for p in proposals if p.score and not p.score.is_eligible]
    story.append(Paragraph(
        f"Evaluated <b>{len(proposals)}</b> proposals against <b>{len(requirements)}</b> requirements. "
        f"<b>{len(eligible)}</b> are eligible; <b>{len(ineligible)}</b> are ineligible.", styles["BodyText"]
    ))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("<b>Project Overview</b>", styles["Heading2"]))
    overview_data = [
        ["Name", project.name],
        ["Category", project.category or "—"],
        ["Budget", f"{project.currency} {project.budget or '—'}"],
        ["Deadline", str(project.deadline) if project.deadline else "—"],
        ["Status", project.status.value],
    ]
    t = Table(overview_data, colWidths=[1.5 * inch, 4.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>Vendor Ranking</b>", styles["Heading2"]))
    rank_data = [["Rank", "Vendor", "Score", "Eligibility"]]
    sorted_props = sorted(
        [p for p in proposals if p.score],
        key=lambda p: (not p.score.is_eligible, -(p.score.total_score or 0)),
    )
    for i, p in enumerate(sorted_props, start=1):
        name = p.project_vendor.vendor.company_name if p.project_vendor and p.project_vendor.vendor else "—"
        rank_data.append([str(i), name, f"{p.score.total_score:.1f}", "Eligible" if p.score.is_eligible else "Ineligible"])
    t = Table(rank_data, colWidths=[0.6 * inch, 3.0 * inch, 1.0 * inch, 1.4 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>Pricing Comparison</b>", styles["Heading2"]))
    price_data = [["Vendor", "Year 1", "Year 3", "Year 5", "Currency"]]
    for p in sorted_props:
        name = p.project_vendor.vendor.company_name if p.project_vendor and p.project_vendor.vendor else "—"
        pr = p.pricing
        price_data.append([
            name,
            f"{pr.year1_total:.0f}" if pr and pr.year1_total else "—",
            f"{pr.year3_total:.0f}" if pr and pr.year3_total else "—",
            f"{pr.year5_total:.0f}" if pr and pr.year5_total else "—",
            pr.currency if pr and pr.currency else "—",
        ])
    t = Table(price_data, colWidths=[2.0 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 0.8 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.2 * inch))

    doc.build(story)
    return buf.getvalue()
