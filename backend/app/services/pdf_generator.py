"""
BudgetBound Professional Travel Itinerary and Budget Report PDF Generator

Generates formal, professionally typeset travel documents with:
- Proper A4 grid layout (20mm margins = 170mm content width)
- Balanced cover page composition
- Full-width tables with calculated column widths
- Intelligent pagination (sections share pages when appropriate)
- Consistent professional typography
- Rs. currency formatting (no symbols)
- Detailed day-by-day itinerary with proper table layout
- Comprehensive budget analysis
- Compact packing and document sections
"""

import io
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    KeepTogether, Flowable, CondPageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas


# ─────────────────────────────────────────────────────────────────────────────
# PROFESSIONAL COLOR PALETTE
# ─────────────────────────────────────────────────────────────────────────────

COLOR_NAVY = colors.HexColor('#0B1020')           # Main headings
COLOR_CHARCOAL = colors.HexColor('#2C3E50')       # Body text
COLOR_BLUE = colors.HexColor('#3B82F6')           # Emphasis/accents
COLOR_LIGHT_GREY = colors.HexColor('#E8EAED')     # Table headers, alternates
COLOR_GREY_BORDER = colors.HexColor('#D0D0D0')    # Borders
COLOR_PINK = colors.HexColor('#EC4899')           # Branding (minimal)


# ─────────────────────────────────────────────────────────────────────────────
# CURRENCY FORMATTING
# ─────────────────────────────────────────────────────────────────────────────

def format_currency(amount: float, decimals: int = 0) -> str:
    """Format amount in Indian Rupees using Rs. prefix."""
    if decimals == 0:
        return f"Rs. {amount:,.0f}"
    else:
        return f"Rs. {amount:,.2f}"


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM PAGE CANVAS
# ─────────────────────────────────────────────────────────────────────────────

class DetailedTravelCanvas(canvas.Canvas):
    """Canvas with professional headers and footers."""
    
    def __init__(self, *args, trip_title: str = "", **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.page_num = 0
        self.trip_title = trip_title
    
    def showPage(self):
        self.page_num += 1
        self._draw_footer()
        canvas.Canvas.showPage(self)
    
    def _draw_footer(self):
        """Draw footer on all pages."""
        page_width, page_height = A4
        footer_y = 0.6 * cm
        
        # Thin separator line
        self.setStrokeColor(COLOR_GREY_BORDER)
        self.setLineWidth(0.5)
        self.line(0.8 * cm, footer_y + 0.2 * cm, page_width - 0.8 * cm, footer_y + 0.2 * cm)
        
        # Left: BudgetBound branding
        self.setFont("Helvetica", 8)
        self.setFillColor(COLOR_CHARCOAL)
        self.drawString(0.8 * cm, footer_y, "BudgetBound")
        
        # Center: Trip title
        trip_text = f"{self.trip_title} | Travel Itinerary"
        self.drawCentredString(page_width / 2, footer_y, trip_text)
        
        # Right: Page number
        page_text = f"Page {self.page_num}"
        self.drawRightString(page_width - 0.8 * cm, footer_y, page_text)


# ─────────────────────────────────────────────────────────────────────────────
# PROFESSIONAL STYLES
# ─────────────────────────────────────────────────────────────────────────────

def create_styles():
    """Create professional typography system for formal document."""
    styles = {}
    
    # COVER PAGE - Restrained, formal
    styles['CoverTitle'] = ParagraphStyle(
        'CoverTitle',
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=COLOR_NAVY,
        spaceAfter=4,
        alignment=TA_CENTER,
        leading=28,
    )
    
    styles['CoverSubtitle'] = ParagraphStyle(
        'CoverSubtitle',
        fontName='Helvetica',
        fontSize=11,
        textColor=COLOR_CHARCOAL,
        spaceAfter=2,
        alignment=TA_CENTER,
        leading=13,
    )
    
    # DESTINATION TITLE ON COVER
    styles['DestinationTitle'] = ParagraphStyle(
        'DestinationTitle',
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=COLOR_NAVY,
        spaceAfter=2,
        alignment=TA_CENTER,
        leading=22,
    )
    
    styles['LocationSubtitle'] = ParagraphStyle(
        'LocationSubtitle',
        fontName='Helvetica',
        fontSize=10,
        textColor=COLOR_CHARCOAL,
        spaceAfter=8,
        alignment=TA_CENTER,
        leading=12,
    )
    
    # SECTION HEADERS - Consistent, professional
    styles['SectionHeader'] = ParagraphStyle(
        'SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=COLOR_NAVY,
        spaceBefore=6,
        spaceAfter=8,
        leading=17,
    )
    
    # SUBSECTION HEADERS
    styles['SubsectionHeader'] = ParagraphStyle(
        'SubsectionHeader',
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=COLOR_NAVY,
        spaceBefore=4,
        spaceAfter=5,
        leading=13,
    )
    
    # DAY HEADERS
    styles['DayHeader'] = ParagraphStyle(
        'DayHeader',
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=COLOR_NAVY,
        spaceBefore=6,
        spaceAfter=4,
        leading=13,
    )
    
    # BODY TEXT
    styles['BodyText'] = ParagraphStyle(
        'BodyText',
        fontName='Helvetica',
        fontSize=10,
        textColor=COLOR_CHARCOAL,
        leading=13,
        spaceAfter=0,
        alignment=TA_JUSTIFY,
    )
    
    styles['BodyTextLeft'] = ParagraphStyle(
        'BodyTextLeft',
        fontName='Helvetica',
        fontSize=10,
        textColor=COLOR_CHARCOAL,
        leading=13,
        spaceAfter=0,
        alignment=TA_LEFT,
    )
    
    # TABLE STYLES
    styles['TableHeader'] = ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=COLOR_NAVY,
        leading=11,
        alignment=TA_LEFT,
    )
    
    styles['TableCell'] = ParagraphStyle(
        'TableCell',
        fontName='Helvetica',
        fontSize=9,
        textColor=COLOR_CHARCOAL,
        leading=11,
        alignment=TA_LEFT,
    )
    
    styles['TableCellRight'] = ParagraphStyle(
        'TableCellRight',
        fontName='Helvetica',
        fontSize=9,
        textColor=COLOR_CHARCOAL,
        leading=11,
        alignment=TA_RIGHT,
    )
    
    styles['TableCellBold'] = ParagraphStyle(
        'TableCellBold',
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=COLOR_CHARCOAL,
        leading=11,
        alignment=TA_RIGHT,
    )
    
    styles['ListItem'] = ParagraphStyle(
        'ListItem',
        fontName='Helvetica',
        fontSize=9,
        textColor=COLOR_CHARCOAL,
        leading=11,
        leftIndent=0.2 * cm,
    )
    
    return styles


# ─────────────────────────────────────────────────────────────────────────────
# PDF GENERATOR CLASS
# ─────────────────────────────────────────────────────────────────────────────

class DetailedTravelItineraryPDF:
    """Generate a professional, formally-typeset travel itinerary and budget report."""
    
    # Page dimensions (A4 = 210 x 297 mm)
    PAGE_WIDTH = 210 * mm
    PAGE_HEIGHT = 297 * mm
    MARGIN = 20 * mm
    CONTENT_WIDTH = PAGE_WIDTH - (2 * MARGIN)  # 170 mm
    
    def __init__(self, trip, user, styles):
        self.trip = trip
        self.user = user
        self.styles = styles
    
    def generate(self) -> bytes:
        """Generate and return PDF bytes."""
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=self.MARGIN / mm * cm / 10,
            leftMargin=self.MARGIN / mm * cm / 10,
            topMargin=20,
            bottomMargin=20,
            title=f"Travel Itinerary - {self.trip.destination.name}",
            author="BudgetBound",
        )
        
        story = []
        
        # Page 1: Cover + Destination + Budget (combined when possible)
        story.extend(self._build_cover_and_summary())
        story.extend(self._build_destination_info())
        story.extend(self._build_budget_section())
        
        # Intelligent break before itinerary
        story.append(CondPageBreak(height=5 * cm))
        
        # Daily Itinerary (may span multiple pages)
        story.extend(self._build_daily_itinerary())
        
        # Optional sections
        if self.trip.packing_items:
            story.append(CondPageBreak(height=3 * cm))
            story.extend(self._build_packing_section())
        
        if self.trip.documents:
            story.append(CondPageBreak(height=3 * cm))
            story.extend(self._build_documents_section())
        
        # Build PDF
        doc.build(
            story,
            canvasmaker=lambda fname, **kw: DetailedTravelCanvas(
                fname,
                trip_title=self.trip.destination.name,
                **kw
            )
        )
        
        buffer.seek(0)
        return buffer.getvalue()
    
    # ─────────────────────────────────────────────────────────────────────────
    # COVER PAGE - Balanced, formal composition
    # ─────────────────────────────────────────────────────────────────────────
    
    def _build_cover_and_summary(self) -> List[Flowable]:
        """Build balanced cover page with trip summary."""
        story = []
        
        # Compact spacing (not wasteful)
        story.append(Spacer(1, 0.8 * cm))
        
        # BudgetBound branding (subtle)
        story.append(Paragraph("BudgetBound", ParagraphStyle(
            'BrandName',
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=COLOR_PINK,
            alignment=TA_CENTER,
            spaceAfter=3,
        )))
        
        # Main title (24pt, not 32pt)
        story.append(Paragraph(
            "Travel Itinerary & Budget Report",
            self.styles['CoverTitle']
        ))
        
        # Blue divider line
        divider_table = Table([['']], colWidths=[17 * cm])
        divider_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), COLOR_BLUE),
            ('ROWBACKGROUNDS', (0, 0), (0, 0), [COLOR_BLUE]),
            ('LINEABOVE', (0, 0), (0, 0), 2, COLOR_BLUE),
            ('LINEBELOW', (0, 0), (0, 0), 0, colors.white),
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (0, 0), 2),
            ('BOTTOMPADDING', (0, 0), (0, 0), 2),
        ]))
        story.append(divider_table)
        
        story.append(Spacer(1, 0.5 * cm))
        
        # Destination and location
        story.append(Paragraph(
            self.trip.destination.name.upper(),
            self.styles['DestinationTitle']
        ))
        
        story.append(Paragraph(
            f"{self.trip.destination.state}, India",
            self.styles['LocationSubtitle']
        ))
        
        # Trip summary: Compact, full-width table
        summary_data = [
            [
                Paragraph("<b>Duration</b>", self.styles['TableHeader']),
                Paragraph(f"{self.trip.days} days", self.styles['TableCell']),
                Paragraph("<b>Travelers</b>", self.styles['TableHeader']),
                Paragraph(str(self.trip.travelers_count), self.styles['TableCell']),
            ],
        ]
        
        if self.trip.start_date or self.trip.transport_mode or self.trip.hotel_tier:
            summary_data.append([
                Paragraph("<b>Transport</b>", self.styles['TableHeader']),
                Paragraph(self.trip.transport_mode or "-", self.styles['TableCell']),
                Paragraph("<b>Hotel Tier</b>", self.styles['TableHeader']),
                Paragraph(self.trip.hotel_tier or "-", self.styles['TableCell']),
            ])
        
        if self.trip.travel_type:
            summary_data.append([
                Paragraph("<b>Travel Type</b>", self.styles['TableHeader']),
                Paragraph(self.trip.travel_type, self.styles['TableCell']),
                Paragraph("", self.styles['TableHeader']),
                Paragraph("", self.styles['TableCell']),
            ])
        
        summary_table = Table(summary_data, colWidths=[2.4 * cm, 3.8 * cm, 2.4 * cm, 3.8 * cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), COLOR_LIGHT_GREY),
            ('BACKGROUND', (2, 0), (2, -1), COLOR_LIGHT_GREY),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('BACKGROUND', (3, 0), (3, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, COLOR_GREY_BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0.15 * cm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0.15 * cm),
            ('TOPPADDING', (0, 0), (-1, -1), 0.12 * cm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.12 * cm),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        
        story.append(summary_table)
        
        story.append(Spacer(1, 0.6 * cm))
        
        # Budget Overview (concise, inline)
        story.append(Paragraph("<b>Budget Overview</b>", self.styles['SubsectionHeader']))
        
        planned = self.trip.budget
        estimated = self.trip.total_estimated_cost
        remaining = planned - estimated
        
        budget_data = [
            [
                Paragraph(format_currency(planned), self.styles['TableCellBold']),
                Paragraph(format_currency(estimated), self.styles['TableCellBold']),
                Paragraph(format_currency(abs(remaining)), self.styles['TableCellBold']),
            ]
        ]
        
        budget_table = Table(budget_data, colWidths=[5.7 * cm, 5.7 * cm, 5.7 * cm])
        budget_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_LIGHT_GREY),
            ('GRID', (0, 0), (-1, -1), 0.5, COLOR_GREY_BORDER),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0.2 * cm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0.2 * cm),
            ('TOPPADDING', (0, 0), (-1, -1), 0.15 * cm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.15 * cm),
        ]))
        
        # Header above budget values
        story.append(Table([[
            Paragraph("Planned Budget", self.styles['TableHeader']),
            Paragraph("Estimated Cost", self.styles['TableHeader']),
            Paragraph("Remaining", self.styles['TableHeader']),
        ]], colWidths=[5.7 * cm, 5.7 * cm, 5.7 * cm], style=TableStyle([
            ('ALIGN', (0, 0), (-1, 0), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, 0), 0.2 * cm),
            ('RIGHTPADDING', (0, 0), (-1, 0), 0.2 * cm),
        ])))
        
        story.append(budget_table)
        
        return story
    
    # ─────────────────────────────────────────────────────────────────────────
    # DESTINATION OVERVIEW - Compact, full-width
    # ─────────────────────────────────────────────────────────────────────────
    
    def _build_destination_info(self) -> List[Flowable]:
        """Build destination details section."""
        story = []
        
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph("Destination Overview", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2 * cm))
        
        # Destination description
        story.append(Paragraph(
            self.trip.destination.description,
            self.styles['BodyText']
        ))
        
        story.append(Spacer(1, 0.3 * cm))
        
        # Key information in full-width table
        info_data = [
            [
                Paragraph("<b>Category</b>", self.styles['TableHeader']),
                Paragraph(self.trip.destination.category, self.styles['TableCell']),
                Paragraph("<b>Best Season</b>", self.styles['TableHeader']),
                Paragraph(self.trip.destination.best_season, self.styles['TableCell']),
                Paragraph("<b>Rating</b>", self.styles['TableHeader']),
                Paragraph(f"{self.trip.destination.rating}/5", self.styles['TableCell']),
            ]
        ]
        
        info_table = Table(info_data, colWidths=[2.3 * cm, 2.5 * cm, 2.8 * cm, 2.9 * cm, 1.5 * cm, 1.8 * cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), COLOR_LIGHT_GREY),
            ('BACKGROUND', (2, 0), (2, 0), COLOR_LIGHT_GREY),
            ('BACKGROUND', (4, 0), (4, 0), COLOR_LIGHT_GREY),
            ('GRID', (0, 0), (-1, -1), 0.5, COLOR_GREY_BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0.15 * cm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0.15 * cm),
            ('TOPPADDING', (0, 0), (-1, -1), 0.12 * cm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.12 * cm),
        ]))
        
        story.append(info_table)
        
        story.append(Spacer(1, 0.3 * cm))
        
        # Attractions
        story.append(Paragraph("<b>Main Attractions & Activities</b>", self.styles['SubsectionHeader']))
        
        if isinstance(self.trip.destination.attractions, list):
            for attraction in self.trip.destination.attractions:
                story.append(Paragraph(f"• {attraction}", self.styles['ListItem']))
        
        return story
    
    # ─────────────────────────────────────────────────────────────────────────
    # BUDGET SECTION - Full-width tables, intelligent layout
    # ─────────────────────────────────────────────────────────────────────────
    
    def _build_budget_section(self) -> List[Flowable]:
        """Build budget summary and breakdown on same page."""
        story = []
        
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph("Budget Analysis", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2 * cm))
        
        # Summary: Concise, full-width
        planned = self.trip.budget
        estimated = self.trip.total_estimated_cost
        remaining = planned - estimated
        utilization = (estimated / planned * 100) if planned > 0 else 0
        
        summary_data = [
            [
                Paragraph("<b>Planned Budget</b>", self.styles['TableHeader']),
                Paragraph(format_currency(planned), self.styles['TableCellBold']),
                Paragraph("<b>Estimated Cost</b>", self.styles['TableHeader']),
                Paragraph(format_currency(estimated), self.styles['TableCellBold']),
                Paragraph("<b>Utilization</b>", self.styles['TableHeader']),
                Paragraph(f"{utilization:.0f}%", self.styles['TableCellBold']),
            ]
        ]
        
        summary_table = Table(summary_data, colWidths=[2.6 * cm, 2.5 * cm, 2.6 * cm, 2.5 * cm, 2.4 * cm, 2.0 * cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), COLOR_LIGHT_GREY),
            ('BACKGROUND', (2, 0), (2, 0), COLOR_LIGHT_GREY),
            ('BACKGROUND', (4, 0), (4, 0), COLOR_LIGHT_GREY),
            ('GRID', (0, 0), (-1, -1), 0.5, COLOR_GREY_BORDER),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('ALIGN', (3, 0), (3, 0), 'RIGHT'),
            ('ALIGN', (5, 0), (5, 0), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, 0), 0.15 * cm),
            ('RIGHTPADDING', (0, 0), (-1, 0), 0.15 * cm),
            ('TOPPADDING', (0, 0), (-1, 0), 0.12 * cm),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 0.12 * cm),
        ]))
        
        story.append(summary_table)
        
        story.append(Spacer(1, 0.3 * cm))
        
        # Category breakdown: Full-width table
        if self.trip.budget_allocation:
            story.append(Paragraph("<b>Expense Breakdown</b>", self.styles['SubsectionHeader']))
            
            alloc = self.trip.budget_allocation
            categories = [
                ("Accommodation", alloc.hotel_cost),
                ("Food & Dining", alloc.food_cost),
                ("Activities", alloc.activities_cost),
                ("Local Transport", alloc.local_transport_cost),
                ("Long-Distance Transport", alloc.transport_cost),
                ("Taxes & Fees", alloc.taxes_fees_cost),
                ("Emergency Reserve", alloc.emergency_reserve),
            ]
            
            total = sum(cost for _, cost in categories)
            
            breakdown_data = [
                [
                    Paragraph("<b>Expense Category</b>", self.styles['TableHeader']),
                    Paragraph("<b>Estimated Amount</b>", self.styles['TableHeader']),
                    Paragraph("<b>Share of Budget</b>", self.styles['TableHeader']),
                ]
            ]
            
            for cat_name, cat_cost in categories:
                pct = (cat_cost / total * 100) if total > 0 else 0
                breakdown_data.append([
                    Paragraph(cat_name, self.styles['TableCell']),
                    Paragraph(format_currency(cat_cost), self.styles['TableCellRight']),
                    Paragraph(f"{pct:.1f}%", self.styles['TableCellRight']),
                ])
            
            breakdown_table = Table(breakdown_data, colWidths=[6.0 * cm, 4.0 * cm, 4.0 * cm])
            breakdown_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), COLOR_LIGHT_GREY),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, COLOR_GREY_BORDER),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (1, 0), (2, -1), 'RIGHT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0.2 * cm),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0.2 * cm),
                ('TOPPADDING', (0, 0), (-1, -1), 0.12 * cm),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0.12 * cm),
            ]))
            
            story.append(breakdown_table)
        
        return story
    
    # ─────────────────────────────────────────────────────────────────────────
    # DAILY ITINERARY - Properly-sized columns, consistent formatting
    # ─────────────────────────────────────────────────────────────────────────
    
    def _build_daily_itinerary(self) -> List[Flowable]:
        """Build day-by-day itinerary with calculated column widths."""
        story = []
        
        story.append(Paragraph("Daily Itinerary", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2 * cm))
        
        # Table width: 170mm (full content width)
        # Column proportions: Time 20% | Activity 65% | Cost 15%
        time_width = 3.4 * cm
        activity_width = 11.05 * cm
        cost_width = 2.55 * cm
        
        itineraries = sorted(self.trip.itineraries, key=lambda x: x.day_number)
        
        for itinerary in itineraries:
            day_num = itinerary.day_number
            day_title = itinerary.description or "Exploration"
            
            # Day header: Compact, not overly long
            day_text = f"DAY {day_num:02d}"
            if day_title:
                # Truncate title if too long
                if len(day_title) > 45:
                    day_title = day_title[:42] + "..."
                day_text = f"{day_text} - {day_title.upper()}"
            
            story.append(Paragraph(
                day_text,
                self.styles['DayHeader']
            ))
            
            # Activities table
            activities = itinerary.activities if isinstance(itinerary.activities, list) else []
            
            if activities:
                # Build table with explicit column widths
                activity_data = [
                    [
                        Paragraph("<b>Time</b>", self.styles['TableHeader']),
                        Paragraph("<b>Activity and Details</b>", self.styles['TableHeader']),
                        Paragraph("<b>Cost</b>", self.styles['TableHeader']),
                    ]
                ]
                
                for activity in activities:
                    time_str = activity.get('time', '')
                    title_str = activity.get('title', 'Activity')
                    cost_val = activity.get('cost', 0)
                    notes_str = activity.get('notes', '')
                    
                    # Combine title and notes for activity
                    activity_text = title_str
                    if notes_str:
                        activity_text = f"{title_str}\n{notes_str}"
                    
                    cost_text = format_currency(cost_val) if cost_val > 0 else "Included"
                    
                    activity_data.append([
                        Paragraph(time_str, self.styles['TableCell']),
                        Paragraph(activity_text, self.styles['TableCell']),
                        Paragraph(cost_text, self.styles['TableCellRight']),
                    ])
                
                # Table with explicit column widths (total: 170mm)
                activity_table = Table(
                    activity_data,
                    colWidths=[time_width, activity_width, cost_width]
                )
                
                activity_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), COLOR_LIGHT_GREY),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 0.5, COLOR_GREY_BORDER),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0.2 * cm),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0.2 * cm),
                    ('TOPPADDING', (0, 0), (-1, -1), 0.12 * cm),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0.12 * cm),
                    ('ROWHEIGHT', (0, 1), (-1, -1), None),  # Allow natural row height
                ]))
                
                story.append(activity_table)
            
            story.append(Spacer(1, 0.25 * cm))
        
        return story
    
    # ─────────────────────────────────────────────────────────────────────────
    # PACKING CHECKLIST - Compact, two-column layout
    # ─────────────────────────────────────────────────────────────────────────
    
    def _build_packing_section(self) -> List[Flowable]:
        """Build packing checklist with compact layout."""
        story = []
        
        story.append(Paragraph("Packing Checklist", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2 * cm))
        
        if self.trip.packing_items:
            items = list(self.trip.packing_items)
            mid_point = (len(items) + 1) // 2
            
            # Two-column packing list
            packing_data = [
                [
                    Paragraph("<b>Item</b>", self.styles['TableHeader']),
                    Paragraph("<b>✓</b>", self.styles['TableHeader']),
                    Paragraph("<b>Item</b>", self.styles['TableHeader']),
                    Paragraph("<b>✓</b>", self.styles['TableHeader']),
                ]
            ]
            
            for i in range(mid_point):
                left_item = items[i]
                left_status = "✓" if left_item.checked else "-"
                
                if i + mid_point < len(items):
                    right_item = items[i + mid_point]
                    right_status = "✓" if right_item.checked else "-"
                else:
                    right_item = None
                    right_status = ""
                
                row = [
                    Paragraph(left_item.name, self.styles['TableCell']),
                    Paragraph(left_status, self.styles['TableCell']),
                    Paragraph(right_item.name if right_item else "", self.styles['TableCell']),
                    Paragraph(right_status, self.styles['TableCell']),
                ]
                packing_data.append(row)
            
            packing_table = Table(packing_data, colWidths=[4.5 * cm, 0.7 * cm, 4.5 * cm, 0.7 * cm])
            packing_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), COLOR_LIGHT_GREY),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, COLOR_GREY_BORDER),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('ALIGN', (3, 0), (3, -1), 'CENTER'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0.12 * cm),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0.12 * cm),
                ('TOPPADDING', (0, 0), (-1, -1), 0.1 * cm),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0.1 * cm),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
            ]))
            
            story.append(packing_table)
        
        return story
    
    # ─────────────────────────────────────────────────────────────────────────
    # TRAVEL DOCUMENTS - Compact table
    # ─────────────────────────────────────────────────────────────────────────
    
    def _build_documents_section(self) -> List[Flowable]:
        """Build travel documents section."""
        story = []
        
        story.append(Paragraph("Travel Documents", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.2 * cm))
        
        if self.trip.documents:
            docs_data = [
                [
                    Paragraph("<b>Category</b>", self.styles['TableHeader']),
                    Paragraph("<b>Filename</b>", self.styles['TableHeader']),
                    Paragraph("<b>Uploaded</b>", self.styles['TableHeader']),
                ]
            ]
            
            for doc in self.trip.documents:
                upload_date = doc.uploaded_at.strftime("%Y-%m-%d") if doc.uploaded_at else "-"
                docs_data.append([
                    Paragraph(doc.category, self.styles['TableCell']),
                    Paragraph(doc.filename, self.styles['TableCell']),
                    Paragraph(upload_date, self.styles['TableCell']),
                ])
            
            docs_table = Table(docs_data, colWidths=[2.8 * cm, 8.2 * cm, 2.8 * cm])
            docs_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), COLOR_LIGHT_GREY),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, COLOR_GREY_BORDER),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0.15 * cm),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0.15 * cm),
                ('TOPPADDING', (0, 0), (-1, -1), 0.12 * cm),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0.12 * cm),
            ]))
            
            story.append(docs_table)
        
        return story


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def generate_premium_trip_pdf(trip, user) -> bytes:
    """
    Generate a comprehensive travel itinerary and budget PDF.
    
    Args:
        trip: Trip model instance
        user: User model instance
    
    Returns:
        bytes: PDF file content
    """
    styles = create_styles()
    generator = DetailedTravelItineraryPDF(trip, user, styles)
    return generator.generate()
