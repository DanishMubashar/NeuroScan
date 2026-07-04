"""
NeuroScan AI - PDF Report Generation
"""

import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import streamlit as st


def generate_pdf_report(patient: dict, doctor: dict, scan_result: dict,
                         analysis: dict, image=None, save_path: str = None) -> bytes:

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             rightMargin=2*cm, leftMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    title_s = ParagraphStyle("T", parent=styles["Title"], fontSize=22,
                               textColor=colors.HexColor("#003366"),
                               alignment=TA_CENTER, spaceAfter=4)
    sub_s   = ParagraphStyle("S", parent=styles["Normal"], fontSize=10,
                               textColor=colors.HexColor("#0066cc"),
                               alignment=TA_CENTER, spaceAfter=3)
    h2_s    = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12,
                               textColor=colors.HexColor("#003366"),
                               spaceBefore=12, spaceAfter=5)
    norm_s  = ParagraphStyle("N", parent=styles["Normal"], fontSize=10, spaceAfter=4)
    disc_s  = ParagraphStyle("D", parent=styles["Normal"], fontSize=8,
                               textColor=colors.grey, alignment=TA_CENTER)
    date_s  = ParagraphStyle("DR", parent=styles["Normal"], fontSize=9,
                               textColor=colors.grey, alignment=TA_RIGHT)

    tbl_style = TableStyle([
        ("BACKGROUND",     (0, 0), (0, -1), colors.HexColor("#E8F0FE")),
        ("FONTNAME",       (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, -1), 10),
        ("GRID",           (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
        ("PADDING",        (0, 0), (-1, -1), 6),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
    ])

    story = []

    # Header
    story.append(Paragraph("🧠 NeuroScan AI", title_s))
    story.append(Paragraph("AI-Powered Brain Tumor Detection & Clinical Support System", sub_s))
    story.append(Paragraph("Medical Report — Confidential", sub_s))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#003366")))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"Report Generated: {datetime.now().strftime('%B %d, %Y — %I:%M %p')}", date_s
    ))
    story.append(Spacer(1, 0.4*cm))

    # Doctor info
    story.append(Paragraph("Physician Information", h2_s))
    t = Table([
        ["Name",      f"Dr. {doctor.get('name', 'N/A')}"],
        ["Specialty", doctor.get('specialty', 'N/A')],
        ["Email",     doctor.get('email', 'N/A')],
    ], colWidths=[4*cm, 12*cm])
    t.setStyle(tbl_style)
    story.append(t)

    # Patient info
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Patient Information", h2_s))
    t2 = Table([
        ["Full Name",       patient.get("full_name", "N/A")],
        ["Age",             str(patient.get("age", "N/A"))],
        ["Gender",          patient.get("gender", "N/A")],
        ["Phone",           patient.get("phone", "N/A") or "N/A"],
        ["Email",           patient.get("email", "N/A") or "N/A"],
        ["Medical History", patient.get("medical_history", "None") or "None"],
    ], colWidths=[4*cm, 12*cm])
    t2.setStyle(tbl_style)
    story.append(t2)

    # AI Results
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("AI Diagnosis Results", h2_s))
    pred  = scan_result.get("predicted_class", "N/A").upper()
    conf  = scan_result.get("confidence", 0)
    res   = "TUMOR DETECTED" if pred != "NOTUMOR" else "NO TUMOR DETECTED"
    sev   = scan_result.get("info", {}).get("severity", "N/A")
    rc    = "#FF4B4B" if pred != "NOTUMOR" else "#00C851"
    t3    = Table([
        ["AI Prediction", pred],
        ["Confidence",    f"{conf:.2f}%"],
        ["Result",        res],
        ["Severity",      sev],
    ], colWidths=[4*cm, 12*cm])
    ts3 = TableStyle(tbl_style._cmds + [
        ("BACKGROUND", (1, 2), (1, 2), colors.HexColor(rc + "33")),
        ("FONTNAME",   (1, 2), (1, 2), "Helvetica-Bold"),
    ])
    t3.setStyle(ts3)
    story.append(t3)

    # Tumor analysis
    if analysis.get("has_tumor"):
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph("Tumor Analysis", h2_s))
        bb = analysis.get("bounding_box", {})
        t4 = Table([
            ["Tumor Area",     f"{analysis.get('tumor_area', 0):.2f} pixels"],
            ["Image Coverage", f"{analysis.get('tumor_percentage', 0):.2f}%"],
            ["Size Category",  analysis.get("tumor_size_category", "N/A")],
            ["Perimeter",      f"{analysis.get('perimeter', 0):.2f} pixels"],
            ["Center",         str(analysis.get("center", "N/A"))],
            ["Bounding Box",   f"x={bb.get('x')}, y={bb.get('y')}, w={bb.get('w')}, h={bb.get('h')}"],
        ], colWidths=[4*cm, 12*cm])
        t4.setStyle(tbl_style)
        story.append(t4)

    # Clinical notes
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Clinical Notes & Recommendations", h2_s))
    for note in analysis.get("clinical_notes", []):
        story.append(Paragraph(f"• {note}", norm_s))
    action = scan_result.get("info", {}).get("action", "Consult a specialist.")
    story.append(Spacer(1, 0.1*cm))
    story.append(Paragraph(f"<b>Recommended Action:</b> {action}", norm_s))

    # Disclaimer
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "<i><b>Disclaimer:</b> This report is generated by NeuroScan AI and is intended to "
        "assist medical professionals only. It does not replace professional medical diagnosis. "
        "Final decisions must be made by qualified healthcare professionals.</i>", disc_s
    ))
    story.append(Spacer(1, 0.1*cm))
    story.append(Paragraph(
        "NeuroScan AI  |  Department of Computer Science, University of Sahiwal", disc_s
    ))

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes


def render_report_download(pdf_bytes: bytes, patient_name: str, scan_id: int):
    fname = f"NeuroScanAI_{patient_name.replace(' ', '_')}_Scan{scan_id}.pdf"
    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_bytes,
        file_name=fname,
        mime="application/pdf",
        use_container_width=True,
        type="primary"
    )
