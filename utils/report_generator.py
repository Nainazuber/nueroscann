from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import io
from datetime import datetime
import json

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
        self.hospital_colors = {
            'primary': colors.HexColor('#005EB8'),  # NHS Blue
            'secondary': colors.HexColor('#003078'),  # Darker Blue
            'accent': colors.HexColor('#00A499'),  # Teal accent
            'light_bg': colors.HexColor('#F5F7FA'),  # Light background
            'border': colors.HexColor('#D0D5DD'),  # Border color
            'success': colors.HexColor('#007F3B'),  # Green
            'warning': colors.HexColor('#FFB81C'),  # Amber
            'danger': colors.HexColor('#DA291C'),  # Red
            'text': colors.HexColor('#212529'),  # Dark text
            'text_light': colors.HexColor('#6B7280')  # Light text
        }
    
    def _create_custom_styles(self):
        """Create professional medical report styles"""
        
        # Main Title - Hospital Report Header
        self.styles.add(ParagraphStyle(
            name='HospitalTitle',
            parent=self.styles['Title'],
            fontSize=26,
            textColor=colors.HexColor('#005EB8'),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=32
        ))
        
        # Subtitle
        self.styles.add(ParagraphStyle(
            name='HospitalSubtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#6B7280'),
            spaceAfter=25,
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=16
        ))
        
        # Section Headers
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#005EB8'),
            spaceBefore=15,
            spaceAfter=10,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            leading=20,
            borderWidth=0,
            borderColor=colors.HexColor('#005EB8'),
            borderPadding=(0, 0, 2, 0)
        ))
        
        # Sub-section Header
        self.styles.add(ParagraphStyle(
            name='SubSectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#003078'),
            spaceBefore=12,
            spaceAfter=8,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            leading=18
        ))
        
        # Normal text with medical styling
        self.styles.add(ParagraphStyle(
            name='MedicalText',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=15,
            spaceAfter=8,
            alignment=TA_JUSTIFY,
            fontName='Helvetica',
            textColor=colors.HexColor('#212529')
        ))
        
        # Bold medical text
        self.styles.add(ParagraphStyle(
            name='MedicalTextBold',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=15,
            spaceAfter=8,
            alignment=TA_JUSTIFY,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#212529')
        ))
        
        # Small print for disclaimers
        self.styles.add(ParagraphStyle(
            name='SmallPrint',
            parent=self.styles['Normal'],
            fontSize=8,
            leading=11,
            spaceAfter=4,
            alignment=TA_JUSTIFY,
            fontName='Helvetica-Oblique',
            textColor=colors.HexColor('#6B7280')
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#6B7280'),
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Value labels
        self.styles.add(ParagraphStyle(
            name='ValueLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#6B7280'),
            alignment=TA_LEFT,
            fontName='Helvetica',
            leading=14
        ))
        
        # Values
        self.styles.add(ParagraphStyle(
            name='Value',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#005EB8'),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            leading=16
        ))
    
    def create_letterhead(self):
        """Create hospital letterhead"""
        data = [[
            Paragraph("NEUROFACE MEDICAL CENTER", self.styles['HospitalTitle']),
        ]]
        
        table = Table(data, colWidths=[7*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        return table
    
    def create_patient_info_section(self, user, test_result):
        """Create professional patient information section with medical formatting"""
        
        # Patient demographics
        data = [
            ["PATIENT INFORMATION", ""],
            ["", ""],
            ["Patient Name:", user.username.upper()],
            ["Patient ID:", f"NF-{user.id:06d}"],
            ["Date of Birth:", f"{user.age if user.age else 'Not specified'} years"],
            ["Gender:", user.gender.replace('_', ' ').title()],
            ["Examination Date:", test_result.test_date.strftime("%B %d, %Y at %H:%M")],
            ["Report Date:", datetime.now().strftime("%B %d, %Y at %H:%M")],
            ["Referring Physician:", "Dr. A. Sharma (Neurology)"],
            ["Accession #:", f"NF-ACC-{test_result.id:06d}"]
        ]
        
        table = Table(data, colWidths=[2*inch, 4.5*inch])
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), self.hospital_colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            
            # Labels
            ('FONTNAME', (0, 2), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 2), (0, -1), self.hospital_colors['secondary']),
            ('ALIGN', (0, 2), (0, -1), 'RIGHT'),
            ('FONTSIZE', (0, 2), (0, -1), 10),
            
            # Values
            ('FONTNAME', (1, 2), (1, -1), 'Helvetica'),
            ('TEXTCOLOR', (1, 2), (1, -1), self.hospital_colors['text']),
            ('FONTSIZE', (1, 2), (1, -1), 10),
            
            # Grid and spacing
            ('GRID', (0, 1), (-1, -1), 0.5, self.hospital_colors['border']),
            ('BACKGROUND', (0, 1), (-1, -1), self.hospital_colors['light_bg']),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        return table
    
    def create_clinical_results_table(self, test_result):
        """Create clinical test results table with medical formatting"""
        
        # Determine status colors
        blink_count_status = self._get_status(test_result.blink_count, 15, 20)
        blink_rate_status = self._get_status(test_result.blink_rate, 15, 20)
        
        data = [
            ["CLINICAL MEASUREMENTS", "RESULT", "REFERENCE RANGE", "FLAG"],
            ["Blink Count", str(test_result.blink_count), "15-20", blink_count_status],
            ["Blink Rate", f"{test_result.blink_rate:.1f} /min", "15-20 /min", blink_rate_status],
            ["Test Duration", "60 seconds", "60 seconds", "Normal"]
        ]
        
        table = Table(data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.2*inch])
        
        # Base styles
        styles = [
            ('BACKGROUND', (0, 0), (-1, 0), self.hospital_colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, self.hospital_colors['border']),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]
        
        table.setStyle(TableStyle(styles))
        
        # Color code the flags
        for i, row in enumerate(data[1:], 1):
            status = row[3]
            if status == "Low":
                table.setStyle(TableStyle([('TEXTCOLOR', (3, i), (3, i), self.hospital_colors['danger'])]))
                table.setStyle(TableStyle([('FONTNAME', (3, i), (3, i), 'Helvetica-Bold')]))
            elif status == "High":
                table.setStyle(TableStyle([('TEXTCOLOR', (3, i), (3, i), self.hospital_colors['warning'])]))
                table.setStyle(TableStyle([('FONTNAME', (3, i), (3, i), 'Helvetica-Bold')]))
            else:
                table.setStyle(TableStyle([('TEXTCOLOR', (3, i), (3, i), self.hospital_colors['success'])]))
        
        return table
    
    def _get_status(self, value, low, high):
        """Get clinical flag based on value"""
        if value < low:
            return "LOW"
        elif value > high:
            return "HIGH"
        else:
            return "NORMAL"
    
    def create_professional_expression_chart(self, expressions):
        """Create clinical-style expression chart"""
        drawing = Drawing(450, 250)
        
        # Add title
        title = Paragraph("Facial Expression Analysis", self.styles['SectionHeader'])
        
        # Bar chart
        bc = VerticalBarChart()
        bc.x = 50
        bc.y = 50
        bc.height = 150
        bc.width = 350
        
        # Data
        values = list(expressions.values())
        bc.data = [values]
        
        # Styling
        bc.strokeColor = self.hospital_colors['border']
        bc.bars[0].fillColor = self.hospital_colors['primary']
        bc.bars[0].strokeColor = self.hospital_colors['secondary']
        bc.bars[0].strokeWidth = 1
        
        # Value axis
        bc.valueAxis.valueMin = 0
        bc.valueAxis.valueMax = 100
        bc.valueAxis.valueStep = 20
        bc.valueAxis.labelTextFormat = '%d%%'
        bc.valueAxis.labels.fontName = 'Helvetica'
        bc.valueAxis.labels.fontSize = 8
        
        # Category axis
        bc.categoryAxis.categoryNames = [key.title() for key in expressions.keys()]
        bc.categoryAxis.labels.fontName = 'Helvetica'
        bc.categoryAxis.labels.fontSize = 9
        bc.categoryAxis.labels.angle = 0
        
        # Grid
        bc.categoryAxis.gridStrokeColor = self.hospital_colors['border']
        bc.categoryAxis.gridStrokeWidth = 0.5
        
        # Add value labels on top of bars
        for i, value in enumerate(values):
            x = bc.x + (i + 0.5) * (bc.width / len(values))
            y = bc.y + value + 5
            drawing.add(self._create_text(f"{value}%", x, y, 8))
        
        drawing.add(bc)
        
        return drawing
    
    def _create_text(self, text, x, y, size):
        """Helper method to create text for chart"""
        from reportlab.graphics.shapes import String
        return String(x, y, text, fontSize=size, textAnchor='middle',
                     fontName='Helvetica-Bold')
    
    def create_clinical_assessment(self, conditions, confidence_scores):
        """Create clinical assessment section with professional medical language"""
        story = []
        
        story.append(Paragraph("CLINICAL ASSESSMENT", self.styles['SectionHeader']))
        story.append(Spacer(1, 5))
        
        if conditions and conditions[0] != 'No specific condition detected':
            primary_condition = conditions[0]
            confidence = confidence_scores.get(primary_condition, 0) if confidence_scores else 0
            
            # Create a highlighted box for primary finding
            data = [[
                Paragraph(f"<b>PRIMARY FINDING:</b> {primary_condition}", self.styles['MedicalTextBold']),
                Paragraph(f"<b>Confidence:</b> {confidence}%", self.styles['MedicalText'])
            ]]
            
            finding_table = Table(data, colWidths=[4*inch, 2*inch])
            finding_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), self.hospital_colors['light_bg']),
                ('BOX', (0, 0), (-1, -1), 1, self.hospital_colors['primary']),
                ('GRID', (0, 0), (-1, -1), 0.5, self.hospital_colors['border']),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(finding_table)
            story.append(Spacer(1, 10))
            
            # Clinical interpretation
            interpretation = self._get_clinical_interpretation(primary_condition)
            story.append(Paragraph("<b>Clinical Interpretation:</b>", self.styles['MedicalTextBold']))
            story.append(Paragraph(interpretation, self.styles['MedicalText']))
            
        else:
            story.append(Paragraph(
                "No significant clinical findings detected. All measured parameters are within normal reference ranges.",
                self.styles['MedicalText']
            ))
        
        return story
    
    def _get_clinical_interpretation(self, condition):
        """Get clinical interpretation text for each condition"""
        interpretations = {
            "Parkinson's Disease": "Reduced blink rate consistent with hypokinetic movement disorder. Recommend neurological evaluation for comprehensive assessment.",
            "ALS / Motor Neuron Disease": "Significantly reduced blink rate may indicate bulbar involvement. Urgent neurological consultation recommended.",
            "Hyperthyroidism": "Decreased blink rate with possible stare suggests thyroid dysfunction. Endocrine workup indicated.",
            "Dry Eye Syndrome": "Elevated blink rate suggests ocular surface irritation. Ophthalmological evaluation recommended.",
            "Stress & Anxiety Disorder": "Increased blink rate may reflect sympathetic activation. Consider stress management and mental health assessment.",
            "Tourette Syndrome / Tic Disorder": "Elevated and variable blink rate suggests possible tic disorder. Neurological evaluation recommended.",
            "Bell's Palsy": "Asymmetric blink pattern noted. Neurological assessment for facial nerve function indicated.",
            "Artison / Dry Eye Syndrome": "Mildly elevated blink rate suggests ocular surface discomfort. Artificial tears and eye rest recommended."
        }
        return interpretations.get(condition, "Clinical correlation with patient history and additional testing recommended.")
    
    def create_recommendations_section(self, recommendations):
        """Create professional recommendations section"""
        story = []
        
        story.append(Paragraph("RECOMMENDATIONS", self.styles['SectionHeader']))
        story.append(Spacer(1, 5))
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                story.append(Paragraph(f"{i}. {rec}", self.styles['MedicalText']))
        else:
            story.append(Paragraph(
                "1. Routine follow-up in 3-6 months\n"
                "2. Maintain regular eye care and screen hygiene\n"
                "3. Report any changes in symptoms to healthcare provider",
                self.styles['MedicalText']
            ))
        
        return story
    
    def create_medical_disclaimer(self):
        """Create comprehensive medical disclaimer"""
        disclaimer_text = """
        <b>IMPORTANT MEDICAL DISCLAIMER:</b> This report is generated by automated facial analysis 
        software and is intended for informational and screening purposes only. All findings should be reviewed and interpreted by a qualified 
        healthcare professional in the context of complete clinical history and examination. The 
        NeuroFace Medical Center recommends consultation with appropriate specialists for confirmation 
        of any findings and before making any medical decisions.
        
        This device has not been cleared by regulatory authorities for diagnostic use and should be 
        considered an adjunctive screening tool only.
        """
        
        return Paragraph(disclaimer_text, self.styles['SmallPrint'])
    
    def create_header(self, canvas, doc):
        """Create professional medical report header"""
        canvas.saveState()
        
        # Top border line
        canvas.setStrokeColor(self.hospital_colors['primary'])
        canvas.setLineWidth(2)
        canvas.line(0.5*inch, doc.pagesize[1] - 0.3*inch, doc.pagesize[0] - 0.5*inch, doc.pagesize[1] - 0.3*inch)
        
        # Hospital name
        canvas.setFont('Helvetica-Bold', 14)
        canvas.setFillColor(self.hospital_colors['primary'])
        canvas.drawString(0.75*inch, doc.pagesize[1] - 0.6*inch, "NEUROFACE MEDICAL CENTER")
        
        # Department
        canvas.setFont('Helvetica', 10)
        canvas.setFillColor(self.hospital_colors['text_light'])
        canvas.drawString(0.75*inch, doc.pagesize[1] - 0.8*inch, "Department of Neurology • Facial Analysis Laboratory")
        
        # Report ID
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(self.hospital_colors['text_light'])
        canvas.drawRightString(doc.pagesize[0] - 0.75*inch, doc.pagesize[1] - 0.6*inch, "CONFIDENTIAL MEDICAL REPORT")
        
        canvas.restoreState()
    
    def add_watermark(self, canvas, doc):
        """Add light watermark"""
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 50)
        canvas.setFillColorRGB(0.95, 0.95, 0.95)  # Very light grey
        canvas.translate(doc.pagesize[0]/2, doc.pagesize[1]/2)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, "NEUROFACE")
        canvas.restoreState()
    
    def create_footer(self, canvas, doc):
        """Create professional medical footer"""
        canvas.saveState()
        
        # Bottom line
        canvas.setStrokeColor(self.hospital_colors['border'])
        canvas.setLineWidth(0.5)
        canvas.line(0.5*inch, 0.75*inch, doc.pagesize[0] - 0.5*inch, 0.75*inch)
        
        # Footer text
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(self.hospital_colors['text_light'])
        
        # Page number
        page_num = f"Page {canvas.getPageNumber()}"
        canvas.drawRightString(doc.pagesize[0] - 0.75*inch, 0.5*inch, page_num)
        
        # Report date
        report_date = f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        canvas.drawString(0.75*inch, 0.5*inch, report_date)
        
        # Confidential
        canvas.drawCentredString(doc.pagesize[0]/2, 0.3*inch, "CONFIDENTIAL - FOR MEDICAL USE ONLY")
        
        canvas.restoreState()
    
    def generate_report(self, user, test_result, expressions, conditions, confidence_scores, recommendations):
        """Generate professional medical report"""
        buffer = io.BytesIO()
        
        # Create document with medical margins
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=1.5*inch,
            bottomMargin=1.2*inch,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch,
            title=f"NeuroFace Medical Report - {user.username}",
            author="NeuroFace Medical Center"
        )
        
        story = []
        
        # Hospital Letterhead
        story.append(self.create_letterhead())
        story.append(Spacer(1, 10))
        
        # Patient Information Section
        story.append(self.create_patient_info_section(user, test_result))
        story.append(Spacer(1, 20))
        
        # Clinical Measurements
        story.append(Paragraph("CLINICAL MEASUREMENTS", self.styles['SectionHeader']))
        story.append(Spacer(1, 5))
        story.append(self.create_clinical_results_table(test_result))
        story.append(Spacer(1, 20))
        
        # Facial Expression Analysis
        story.append(Paragraph("FACIAL EXPRESSION ANALYSIS", self.styles['SectionHeader']))
        story.append(Spacer(1, 5))
        story.append(self.create_professional_expression_chart(expressions))
        story.append(Spacer(1, 20))
        
        # Clinical Assessment
        story.extend(self.create_clinical_assessment(conditions, confidence_scores))
        story.append(Spacer(1, 15))
        
        # Recommendations
        story.extend(self.create_recommendations_section(recommendations))
        story.append(Spacer(1, 20))
        
        # Disclaimer
        story.append(self.create_medical_disclaimer())
        
        # Build document
        def add_page_elements(canvas, doc):
            self.add_watermark(canvas, doc)
            self.create_header(canvas, doc)
            self.create_footer(canvas, doc)

        doc.build(story, onFirstPage=add_page_elements, onLaterPages=add_page_elements)

        buffer.seek(0)
        return buffer.getvalue()

def generate_pdf_report(user, test_result, micro_expressions, conditions, confidence_scores, recommendations):
    """Main function to generate professional PDF medical report"""
    generator = ReportGenerator()
    return generator.generate_report(user, test_result, micro_expressions, conditions, confidence_scores, recommendations)