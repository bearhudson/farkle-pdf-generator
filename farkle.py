import argparse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

PAGE_WIDTH = 8.5 * inch
MARGIN = 0.5 * inch
AVAILABLE_WIDTH = PAGE_WIDTH - (2 * MARGIN)
AVAILABLE_HEIGHT = 7.3 * inch 

class DiceGraphic(Flowable):
    def __init__(self, value, size=10): 
        Flowable.__init__(self)
        self.value = value
        self.size = size
        self.width = size
        self.height = size

    def draw(self):
        s = self.size
        r = s * 0.25 
        dot_r = s * 0.08
        self.canv.setLineWidth(0.5)
        self.canv.setStrokeColor(colors.black)
        self.canv.setFillColor(colors.white)
        self.canv.roundRect(0, 0, s, s, r, stroke=1, fill=1)
        l, c, r_pos = s * 0.25, s * 0.5, s * 0.75
        dots = {
            1: [(c, c)], 2: [(l, l), (r_pos, r_pos)], 3: [(l, l), (c, c), (r_pos, r_pos)],
            4: [(l, l), (l, r_pos), (r_pos, l), (r_pos, r_pos)],
            5: [(l, l), (l, r_pos), (c, c), (r_pos, l), (r_pos, r_pos)],
            6: [(l, l), (l, c), (l, r_pos), (r_pos, l), (r_pos, r_pos), (r_pos, c)]
        }
        self.canv.setFillColor(colors.black)
        for dx, dy in dots[self.value]:
            self.canv.circle(dx, dy, dot_r, fill=1)

class ScoreRow(Flowable):
    def __init__(self, die_val, multiplier, size=10):
        Flowable.__init__(self)
        self.die_val = die_val
        self.mult = multiplier
        self.size = size
        self.width = size + 22
        self.height = size

    def draw(self):
        die = DiceGraphic(self.die_val, size=self.size)
        die.drawOn(self.canv, 0, 0)
        self.canv.setFont("Helvetica-Bold", self.size)
        self.canv.drawString(self.size + 4, 1, f"x {self.mult}")

class DiceCombination(Flowable):
    def __init__(self, die_values, size=10, padding=2):
        Flowable.__init__(self)
        self.die_values = die_values
        self.size = size
        self.padding = padding
        self.width = len(die_values) * (size + padding) - padding
        self.height = size

    def draw(self):
        for i, val in enumerate(self.die_values):
            x = i * (self.size + self.padding)
            die = DiceGraphic(val, size=self.size)
            die.drawOn(self.canv, x, 0)

def generate_farkle_sheet(rounds, players, filename):
    doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=MARGIN, 
                             leftMargin=MARGIN, rightMargin=MARGIN, bottomMargin=MARGIN)
    elements = []
    styles = getSampleStyleSheet()
    scoring_style = ParagraphStyle('Scoring', parent=styles['Normal'], fontSize=8.5, leading=10, alignment=0)
    center_style = ParagraphStyle('Center', parent=styles['Normal'], fontSize=8.5, leading=10, alignment=1)

    # --- 1. CENTERED THREE-COLUMN SCORING REFERENCE ---
    # Column 1: Triplets
    col1_data = [[ScoreRow(1, 3), Paragraph("1,000 pts", scoring_style)]]
    for i in range(2, 7):
        col1_data.append([ScoreRow(i, 3), Paragraph(f"{i*100} pts", scoring_style)])
    
    # Column 2: Singles and "Kinds"
    col2_data = [
        [ScoreRow(1, 1), Paragraph("100 pts", scoring_style)],
        [ScoreRow(5, 1), Paragraph("50 pts", scoring_style)],
        [Paragraph("<b>4 Kind</b>", scoring_style), Paragraph("1,000", scoring_style)],
        [Paragraph("<b>5 Kind</b>", scoring_style), Paragraph("2,000", scoring_style)],
        [Paragraph("<b>6 Kind</b>", scoring_style), Paragraph("3,000", scoring_style)],
        [Paragraph("<b>4 Kind + Pair</b>", scoring_style), Paragraph("1,500", scoring_style)],
    ]

    # Column 3: Multi-dice Specials and Notes
    col3_data = [
        [DiceCombination([1,2,3,4,5,6]), Paragraph("1,500 (Straight)", scoring_style)],
        [DiceCombination([1,1,2,2,3,3]), Paragraph("1,500 (3 Pairs)", scoring_style)],
        [Spacer(1, 5), Spacer(1, 5)],
        [Paragraph("<i>500 to start</i>", center_style), ''],
        [Paragraph("<i>300 min bank</i>", center_style), ''],
    ]

    t1 = Table(col1_data, colWidths=[0.6*inch, 0.8*inch])
    t2 = Table(col2_data, colWidths=[0.9*inch, 0.6*inch])
    t3 = Table(col3_data, colWidths=[1.1*inch, 1.2*inch])
    
    inner_style = TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 0)])
    for t in [t1, t2, t3]: t.setStyle(inner_style)
    t3.setStyle(TableStyle([('SPAN', (0,3), (1,3)), ('SPAN', (0,4), (1,4))]))

    # Main outer table to center everything across the width
    main_ref_table = Table([[t1, t2, t3]], colWidths=[AVAILABLE_WIDTH/3]*3)
    main_ref_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1.2, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    
    elements.append(main_ref_table)
    elements.append(Spacer(1, 0.15*inch))

    # --- 2. DYNAMIC SCORE TABLE ---
    header = ['Round'] + [f'P{i+1}' if players > 6 else f'Player {i+1}' for i in range(players)]
    score_data = [header] + [[str(i)] + [''] * players for i in range(1, rounds + 1)] + [['TOTAL'] + [''] * players]

    col_widths = [0.6 * inch] + [(AVAILABLE_WIDTH - 0.6 * inch) / players] * players
    row_height = min(AVAILABLE_HEIGHT / (rounds + 2), 32)

    score_table = Table(score_data, colWidths=col_widths, rowHeights=row_height)
    score_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BOX', (0,0), (-1,-1), 1.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.black),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEABOVE', (0,-1), (-1,-1), 2.0, colors.black),
        ('BACKGROUND', (0,-1), (-1,-1), colors.whitesmoke),
    ]))
    
    elements.append(score_table)
    doc.build(elements)
    print(f"Generated centered sheet: {filename}")

def check_range(value, name, min_val, max_val):
    ivalue = int(value)
    if ivalue < min_val or ivalue > max_val:
        raise argparse.ArgumentTypeError(f"{name} must be between {min_val} and {max_val}.")
    return ivalue

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a centered Farkle Score Sheet.")
    parser.add_argument("-r", "--rounds", type=lambda x: check_range(x, "Rounds", 1, 20), default=20)
    parser.add_argument("-p", "--players", type=lambda x: check_range(x, "Players", 1, 8), default=5)
    parser.add_argument("-o", "--output", type=str, default="Farkle_Centered_Sheet.pdf")
    args = parser.parse_args()
    generate_farkle_sheet(args.rounds, args.players, args.output)
