import argparse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Constants for layout
PAGE_WIDTH = 8.5 * inch
PAGE_HEIGHT = 11 * inch
MARGIN = 0.5 * inch
AVAILABLE_WIDTH = PAGE_WIDTH - (2 * MARGIN)
# Space reserved for the scoring block and margins
AVAILABLE_HEIGHT = 7.5 * inch 

class DiceGraphic(Flowable):
    def __init__(self, value, size=10): 
        Flowable.__init__(self)
        self.value = value
        self.size = size
        self.width = size
        self.height = size

    def draw(self):
        s = self.size
        r = s * 0.25 # Rounded corners
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
    scoring_style = ParagraphStyle('Scoring', parent=styles['Normal'], fontSize=9, leading=11)

    # --- 1. SCORING REFERENCE BLOCK ---
    trips_rows = [
        [DiceCombination([1, 1, 1]), Paragraph("1,000 pts", scoring_style)],
        [DiceCombination([2, 2, 2]), Paragraph("200 pts", scoring_style)],
        [DiceCombination([3, 3, 3]), Paragraph("300 pts", scoring_style)],
        [DiceCombination([4, 4, 4]), Paragraph("400 pts", scoring_style)],
        [DiceCombination([5, 5, 5]), Paragraph("500 pts", scoring_style)],
        [DiceCombination([6, 6, 6]), Paragraph("600 pts", scoring_style)]
    ]
    specials_rows = [
        [DiceCombination([1]), Paragraph("100 pts", scoring_style)],
        [DiceCombination([5]), Paragraph("50 pts", scoring_style)],
        [DiceCombination([1,2,3,4,5,6]), Paragraph("1,500 pts (Straight)", scoring_style)],
        [DiceCombination([1,1,2,2,3,3]), Paragraph("1,500 pts (3 Pairs)", scoring_style)],
        [DiceCombination([4,4,4,6,6,6]), Paragraph("2,500 pts (2 Triplets)", scoring_style)],
        [Paragraph('<i>500 to start / 300 min bank</i>', scoring_style), '']
    ]

    trips_table = Table(trips_rows, colWidths=[0.8*inch, 0.8*inch])
    specials_table = Table(specials_rows, colWidths=[1.1*inch, 1.8*inch])
    inner_style = TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('BOTTOMPADDING', (0,0), (-1,-1), 3)])
    trips_table.setStyle(inner_style)
    specials_table.setStyle(inner_style)
    specials_table.setStyle(TableStyle([('SPAN', (0,5), (1,5))]))

    main_ref_table = Table([[trips_table, specials_table]], colWidths=[2.2*inch, 4.8*inch])
    main_ref_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1.2, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 12), ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(main_ref_table)
    elements.append(Spacer(1, 0.15*inch))

    # --- 2. DYNAMIC SCORE TABLE ---
    header = ['Round'] + [f'P{i+1}' if players > 6 else f'Player {i+1}' for i in range(players)]
    score_data = [header]
    for i in range(1, rounds + 1):
        score_data.append([str(i)] + [''] * players)
    score_data.append(['TOTAL'] + [''] * players)

    # Width Logic
    player_col_width = (AVAILABLE_WIDTH - 0.6 * inch) / players
    col_widths = [0.6 * inch] + [player_col_width] * players
    
    # Height Logic (ensures single page)
    row_height = AVAILABLE_HEIGHT / (rounds + 2)
    row_height = min(row_height, 32) # Max height for comfort
    row_height = max(row_height, 18) # Min height for utility

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
    print(f"Generated: {filename} ({players} players, {rounds} rounds)")

# Range checker for Argparse
def check_range(value, name, min_val, max_val):
    ivalue = int(value)
    if ivalue < min_val or ivalue > max_val:
        raise argparse.ArgumentTypeError(f"{name} must be between {min_val} and {max_val}.")
    return ivalue

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a Farkle Score Sheet PDF.")
    
    parser.add_argument("-r", "--rounds", type=lambda x: check_range(x, "Rounds", 1, 20), 
                        default=20, help="Number of rounds (1-20)")
    parser.add_argument("-p", "--players", type=lambda x: check_range(x, "Players", 1, 8), 
                        default=5, help="Number of players (1-8)")
    parser.add_argument("-o", "--output", type=str, 
                        default="Farkle_Score_Sheet.pdf", help="Filename")
    
    args = parser.parse_args()
    generate_farkle_sheet(args.rounds, args.players, args.output)
