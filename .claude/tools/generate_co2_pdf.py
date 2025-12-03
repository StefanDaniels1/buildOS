#!/usr/bin/env python3
"""
PDF Report Generator for buildOS CO2 Analysis
Generates professional sustainability reports from CO2 calculation data
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


def generate_co2_report_pdf(co2_report_file: str, ifc_filename: str, output_pdf: str):
    """
    Generate a professional PDF report from CO2 calculation data.

    Args:
        co2_report_file: Path to batch_X_co2_report.json
        ifc_filename: Original IFC file name
        output_pdf: Output PDF path
    """

    # Load CO2 report data
    with open(co2_report_file, 'r') as f:
        data = json.load(f)

    summary = data['summary']
    by_category = data.get('by_category', {})
    metadata = data.get('metadata', {})
    skipped = data.get('skipped_elements', [])

    # Create PDF
    doc = SimpleDocTemplate(output_pdf, pagesize=A4,
                           rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    body_style = styles['BodyText']
    body_style.fontSize = 11
    body_style.leading = 14

    # Title Page
    elements.append(Spacer(1, 3*cm))
    title = Paragraph("CO2 Impact Analysis Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 1*cm))

    subtitle = Paragraph(f"<b>Project:</b> {Path(ifc_filename).stem}", ParagraphStyle(
        'subtitle', parent=body_style, fontSize=14, alignment=TA_CENTER
    ))
    elements.append(subtitle)
    elements.append(Spacer(1, 0.5*cm))

    report_date = Paragraph(
        f"<b>Report Date:</b> {datetime.now().strftime('%d %B %Y')}",
        ParagraphStyle('date', parent=body_style, fontSize=12, alignment=TA_CENTER)
    )
    elements.append(report_date)
    elements.append(Spacer(1, 2*cm))

    # Summary box
    summary_data = [
        ['Total Elements Analyzed', f"{summary['total_elements']}"],
        ['Elements Calculated', f"{summary['calculated']} ({summary['completeness_pct']}%)"],
        ['Elements Skipped', f"{summary['skipped']}"],
        ['', ''],
        ['Total CO2 Impact', f"<b>{summary['total_co2_kg']:,.0f} kg CO2-eq</b>"],
        ['Total Mass', f"{summary['total_mass_kg']:,.0f} kg"],
    ]

    summary_table = Table(summary_data, colWidths=[8*cm, 6*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ECF0F1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (1, 4), (1, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTSIZE', (1, 4), (1, 4), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7'))
    ]))

    elements.append(summary_table)
    elements.append(PageBreak())

    # CO2 Breakdown by Material Category
    elements.append(Paragraph("CO2 Impact by Material Category", heading_style))
    elements.append(Spacer(1, 0.5*cm))

    # Create material breakdown table
    breakdown_data = [['Material Category', 'Element Count', 'CO2 Impact (kg)', 'Percentage']]

    for category, cat_data in by_category.items():
        breakdown_data.append([
            category.capitalize(),
            str(cat_data['count']),
            f"{cat_data['co2_kg']:,.2f}",
            f"{cat_data.get('percentage', 0):.1f}%"
        ])

    breakdown_table = Table(breakdown_data, colWidths=[4*cm, 3*cm, 4*cm, 3*cm])
    breakdown_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ECF0F1')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))

    elements.append(breakdown_table)
    elements.append(Spacer(1, 1*cm))

    # Data Quality Section
    elements.append(Paragraph("Data Quality & Completeness", heading_style))
    elements.append(Spacer(1, 0.3*cm))

    completeness_text = f"""
    This analysis achieved <b>{summary['completeness_pct']}%</b> completeness.
    {summary['calculated']} out of {summary['total_elements']} elements were successfully analyzed
    with CO2 impact calculations based on volume data and material properties extracted from the IFC model.
    """
    elements.append(Paragraph(completeness_text, body_style))
    elements.append(Spacer(1, 0.5*cm))

    if skipped:
        skipped_text = f"""
        <b>{summary['skipped']} elements were skipped</b> due to missing volume or material data.
        These elements may require manual review or additional BIM model refinement for complete analysis.
        """
        elements.append(Paragraph(skipped_text, body_style))

    elements.append(Spacer(1, 1*cm))

    # Methodology Section
    elements.append(Paragraph("Methodology", heading_style))
    elements.append(Spacer(1, 0.3*cm))

    methodology_text = f"""
    This CO2 analysis is based on the <b>{metadata.get('database_source', 'NIBE Dutch national database')}</b>.
    Embodied carbon values represent kg CO2-equivalent per kg of material, including:
    <br/><br/>
    • Material extraction and processing<br/>
    • Manufacturing and transport (cradle-to-gate)<br/>
    • Reinforcement steel for concrete elements<br/>
    • Carbon sequestration for timber products (negative values)<br/>
    <br/>
    Calculations use actual element volumes from the BIM model multiplied by material densities
    and embodied CO2 factors from the durability database (version {metadata.get('database_version', '1.0.0')}).
    """
    elements.append(Paragraph(methodology_text, body_style))
    elements.append(Spacer(1, 1*cm))

    # Footer note
    footer_text = f"""
    <i>Generated by buildOS - BIM AI CO2 Analysis System<br/>
    Report generated on {datetime.now().strftime('%d %B %Y at %H:%M')}<br/>
    Source: {Path(co2_report_file).name}</i>
    """
    elements.append(Spacer(1, 2*cm))
    elements.append(Paragraph(footer_text, ParagraphStyle(
        'footer', parent=body_style, fontSize=9, textColor=colors.grey, alignment=TA_CENTER
    )))

    # Build PDF
    doc.build(elements)

    return {
        'pdf_file': output_pdf,
        'pages': 2,  # Estimated
        'total_co2_kg': summary['total_co2_kg'],
        'completeness_pct': summary['completeness_pct']
    }


def main():
    """CLI entry point."""
    if len(sys.argv) < 4:
        print("Usage: python generate_co2_pdf.py <co2_report.json> <ifc_filename> <output.pdf>")
        print("\nExample:")
        print("  python generate_co2_pdf.py batch_1_co2_report.json Small_condo.ifc co2_report.pdf")
        sys.exit(1)

    co2_report_file = sys.argv[1]
    ifc_filename = sys.argv[2]
    output_pdf = sys.argv[3]

    if not Path(co2_report_file).exists():
        print(f"Error: CO2 report file not found: {co2_report_file}")
        sys.exit(1)

    print(f"\n📄 Generating PDF Report...")
    print(f"   Input: {co2_report_file}")
    print(f"   IFC: {ifc_filename}")
    print(f"   Output: {output_pdf}")

    try:
        result = generate_co2_report_pdf(co2_report_file, ifc_filename, output_pdf)

        print(f"\n✅ PDF Report Generated!")
        print(f"   File: {result['pdf_file']}")
        print(f"   Total CO2: {result['total_co2_kg']:,.0f} kg CO2-eq")
        print(f"   Completeness: {result['completeness_pct']}%")
        print()

    except Exception as e:
        print(f"\n❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
