#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime
from collections import defaultdict

def install_requirements():
    """Install required packages"""
    os.system("pip install reportlab pillow -q 2>/dev/null")

def load_batch_files(batch_files):
    """Load and parse all batch JSON files"""
    all_data = []
    for batch_file in batch_files:
        try:
            with open(batch_file, 'r') as f:
                data = json.load(f)
                all_data.append(data)
                print(f"  Loaded: {os.path.basename(batch_file)}")
        except Exception as e:
            print(f"  Error loading {batch_file}: {e}")
    return all_data

def aggregate_data(all_data):
    """Aggregate data from all batches"""
    summary = {
        'total_elements': 0,
        'calculated': 0,
        'skipped': 0,
        'total_co2_kg': 0.0,
        'total_mass_kg': 0.0,
        'batches_processed': len(all_data)
    }
    
    by_category = defaultdict(lambda: {
        'count': 0,
        'co2_kg': 0.0,
        'mass_kg': 0.0
    })
    
    all_detailed = []
    batch_summaries = []
    
    for batch_idx, batch in enumerate(all_data, 1):
        batch_name = batch.get('metadata', {}).get('source_file', f'Batch {batch_idx}')
        
        if 'summary' in batch:
            summary['total_elements'] += batch['summary'].get('total_elements', 0)
            summary['calculated'] += batch['summary'].get('calculated', 0)
            summary['skipped'] += batch['summary'].get('skipped', 0)
            summary['total_co2_kg'] += batch['summary'].get('total_co2_kg', 0.0)
            summary['total_mass_kg'] += batch['summary'].get('total_mass_kg', 0.0)
            
            batch_summaries.append({
                'name': batch_name,
                'total_elements': batch['summary'].get('total_elements', 0),
                'calculated': batch['summary'].get('calculated', 0),
                'skipped': batch['summary'].get('skipped', 0),
                'co2_kg': batch['summary'].get('total_co2_kg', 0.0),
                'mass_kg': batch['summary'].get('total_mass_kg', 0.0),
                'completeness': batch['summary'].get('completeness_pct', 0.0)
            })
        
        if 'by_category' in batch:
            for category, data in batch['by_category'].items():
                by_category[category]['count'] += data.get('count', 0)
                by_category[category]['co2_kg'] += data.get('co2_kg', 0.0)
                by_category[category]['mass_kg'] += data.get('mass_kg', 0.0)
        
        if 'detailed_results' in batch:
            all_detailed.extend(batch['detailed_results'])
    
    if summary['total_elements'] > 0:
        summary['completeness_pct'] = (summary['calculated'] / summary['total_elements']) * 100
    else:
        summary['completeness_pct'] = 0.0
    
    return summary, dict(by_category), all_detailed, batch_summaries

def generate_pdf_report(output_file, summary, by_category, batch_summaries, all_detailed):
    """Generate professional PDF report using reportlab"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    
    doc = SimpleDocTemplate(output_file, pagesize=A4, rightMargin=0.5*inch, leftMargin=0.5*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#1f4788'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=HexColor('#4a6fa5'),
        spaceAfter=6,
        alignment=TA_CENTER
    )
    
    summary_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=HexColor('#1f4788'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("CO2 IMPACT ANALYSIS REPORT", title_style))
    story.append(Paragraph("Sustainability Assessment for Building Project", subtitle_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", subtitle_style))
    story.append(Spacer(1, 1.5*cm))
    
    story.append(Paragraph("EXECUTIVE SUMMARY", summary_title))
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Elements Analyzed', f"{summary['total_elements']}"],
        ['Elements with CO2 Calculations', f"{summary['calculated']}"],
        ['Elements Skipped', f"{summary['skipped']}"],
        ['Data Completeness', f"{summary['completeness_pct']:.1f}%"],
        ['Total CO2 Impact', f"{summary['total_co2_kg']:,.2f} kg CO2-eq"],
        ['Total Mass', f"{summary['total_mass_kg']:,.2f} kg"],
        ['Batches Processed', f"{summary['batches_processed']}"],
    ]
    
    summary_table = Table(summary_data, colWidths=[3.5*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f0f0f0')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f9f9f9')]),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("BATCH PROCESSING SUMMARY", summary_title))
    
    batch_data = [['Batch File', 'Total', 'Calculated', 'Skipped', 'Completeness %', 'CO2 (kg CO2-eq)']]
    for batch in batch_summaries:
        batch_data.append([
            batch['name'],
            str(batch['total_elements']),
            str(batch['calculated']),
            str(batch['skipped']),
            f"{batch['completeness']:.1f}%",
            f"{batch['co2_kg']:,.2f}"
        ])
    
    batch_table = Table(batch_data, colWidths=[1.8*inch, 0.9*inch, 1*inch, 0.9*inch, 1.1*inch, 1.2*inch])
    batch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f9f9f9')]),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ]))
    
    story.append(batch_table)
    story.append(PageBreak())
    
    story.append(Paragraph("CO2 BREAKDOWN BY MATERIAL CATEGORY", summary_title))
    
    sorted_categories = sorted(by_category.items(), key=lambda x: x[1]['co2_kg'], reverse=True)
    
    category_data = [['Material Category', 'Elements', 'CO2 (kg CO2-eq)', 'Mass (kg)', '% of Total']]
    for category, data in sorted_categories:
        pct = (data['co2_kg'] / summary['total_co2_kg'] * 100) if summary['total_co2_kg'] > 0 else 0
        category_data.append([
            category.replace('_', ' ').title(),
            str(data['count']),
            f"{data['co2_kg']:,.2f}",
            f"{data['mass_kg']:,.2f}",
            f"{pct:.1f}%"
        ])
    
    category_table = Table(category_data, colWidths=[1.8*inch, 1*inch, 1.5*inch, 1.3*inch, 1.2*inch])
    category_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#4a6fa5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f9f9f9')]),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
    ]))
    
    story.append(category_table)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("DATA QUALITY ASSESSMENT", summary_title))
    
    quality_text = f"""
    <b>Completeness Analysis:</b> {summary['completeness_pct']:.1f}% of elements have been successfully calculated.
    This means {summary['calculated']} out of {summary['total_elements']} elements have CO2 impact data.
    <br/><br/>
    <b>Skipped Elements:</b> {summary['skipped']} elements could not be calculated due to missing volume or area data.
    These elements are classified by material type but lack quantitative geometry information.
    <br/><br/>
    <b>Key Data Gaps:</b>
    <br/>- Elements missing volume data (volume_m3: null)
    <br/>- Elements missing area data (area_m2: null)
    <br/>- Opening elements and voids (zero material content)
    <br/>- Unfilled wall geometries (thickness available but length/height missing)
    <br/><br/>
    <b>Recommendations for Improvement:</b>
    <br/>1. Ensure all structural elements have complete 3D geometry in the IFC model
    <br/>2. Verify that wall elements include both dimensions and area calculations
    <br/>3. Confirm volume data is extracted from element properties or calculated from geometry
    <br/>4. For improved accuracy, obtain density specifications for all materials
    """
    
    quality_style = ParagraphStyle(
        'QualityText',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=12,
        leading=14
    )
    
    story.append(Paragraph(quality_text, quality_style))
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("METHODOLOGY & DATABASE SOURCES", summary_title))
    
    methodology_text = """
    <b>Calculation Method:</b> Volume-based CO2 assessment using material density and embodied carbon factors.
    <br/><br/>
    <b>Database Source:</b> NIBE (Dutch National Database) - Standard CO2 factors for construction materials.
    This database provides industry-standard life cycle assessment (LCA) values for cradle-to-gate emissions.
    <br/><br/>
    <b>Scope:</b>
    <br/>- Cradle-to-gate emissions (from raw material extraction to factory gate)
    <br/>- Structural reinforcement included where applicable
    <br/>- Carbon sequestration considered for timber products (negative CO2)
    <br/><br/>
    <b>Data Quality Notes:</b>
    <br/>- Confidence levels vary by material type and data availability (0.75-0.85)
    <br/>- Generic factors used where specific material specifications unavailable
    <br/>- Estimated volumes calculated from area data where volume not directly available
    """
    
    story.append(Paragraph(methodology_text, quality_style))
    story.append(PageBreak())
    
    if all_detailed:
        story.append(Paragraph("SAMPLE OF CALCULATED ELEMENTS (First 20)", summary_title))
        
        detailed_data = [['Element Type', 'Material', 'CO2 (kg)', 'Mass (kg)', 'Confidence']]
        for item in all_detailed[:20]:
            detailed_data.append([
                item.get('element_type', 'unknown'),
                item.get('material_category', 'unknown'),
                f"{item.get('co2_kg', 0):.2f}",
                f"{item.get('mass_kg', 0):.2f}",
                f"{item.get('confidence', 0):.2f}"
            ])
        
        detailed_table = Table(detailed_data, colWidths=[1.5*inch, 1.3*inch, 1.2*inch, 1.2*inch, 1.3*inch])
        detailed_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f9f9f9')]),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ]))
        
        story.append(detailed_table)
        story.append(Spacer(1, 0.5*cm))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=HexColor('#666666'),
        alignment=TA_CENTER,
        spaceAfter=0
    )
    
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("---", footer_style))
    story.append(Paragraph(f"CO2 Impact Analysis Report | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
    story.append(Paragraph("NIBE Database | Cradle-to-Gate Embodied Carbon Assessment", footer_style))
    
    try:
        doc.build(story)
        return True
    except Exception as e:
        print(f"  PDF generation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    session_dir = "/app/workspace/.context/session_session_1765097211177_9vhg42"
    batch_files = [
        f"{session_dir}/co2_batch_1.json",
        f"{session_dir}/co2_batch_2.json",
        f"{session_dir}/co2_batch_3.json",
        f"{session_dir}/co2_batch_4.json",
        f"{session_dir}/co2_batch_5.json",
    ]
    
    output_file = f"{session_dir}/durability_report.pdf"
    
    print("="*70)
    print("CO2 SUSTAINABILITY REPORT GENERATOR")
    print("="*70)
    print()
    
    print("Step 1: Loading batch files...")
    all_data = load_batch_files(batch_files)
    print(f"Successfully loaded {len(all_data)} batch files\n")
    
    print("Step 2: Aggregating data from all batches...")
    summary, by_category, all_detailed, batch_summaries = aggregate_data(all_data)
    print(f"  Total elements analyzed: {summary['total_elements']}")
    print(f"  Elements calculated: {summary['calculated']}")
    print(f"  Elements skipped: {summary['skipped']}")
    print(f"  Data completeness: {summary['completeness_pct']:.1f}%")
    print(f"  Total CO2 impact: {summary['total_co2_kg']:,.2f} kg CO2-eq")
    print(f"  Total mass: {summary['total_mass_kg']:,.2f} kg\n")
    
    print("Step 3: CO2 breakdown by material category:")
    sorted_categories = sorted(by_category.items(), key=lambda x: x[1]['co2_kg'], reverse=True)
    for category, data in sorted_categories:
        pct = (data['co2_kg'] / summary['total_co2_kg'] * 100) if summary['total_co2_kg'] > 0 else 0
        print(f"  {category}: {data['co2_kg']:,.2f} kg CO2-eq ({pct:.1f}%) - {data['count']} elements")
    print()
    
    print("Step 4: Installing dependencies...")
    install_requirements()
    
    print("Step 5: Generating professional PDF report...")
    if generate_pdf_report(output_file, summary, by_category, batch_summaries, all_detailed):
        print(f"  SUCCESS: PDF report generated!")
        print(f"  Output file: {output_file}")
        
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            file_size_kb = file_size / 1024
            print(f"  File size: {file_size_kb:.1f} KB")
        print()
    else:
        print("  ERROR: Failed to generate PDF report")
        return False
    
    print("="*70)
    print("REPORT GENERATION COMPLETE")
    print("="*70)
    print()
    print(f"Output Location: {output_file}")
    print(f"Report includes:")
    print(f"  - Executive summary with key metrics")
    print(f"  - Batch processing summary")
    print(f"  - CO2 breakdown by material category")
    print(f"  - Data quality assessment with recommendations")
    print(f"  - Methodology and database source information")
    print(f"  - Sample of calculated elements")
    print()
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
