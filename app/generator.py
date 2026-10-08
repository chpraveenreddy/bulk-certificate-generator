from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas


PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)


def draw_fitted_text(
    pdf,
    text,
    x,
    y,
    max_width,
    starting_size=28,
    min_size=10
):
    font_size = starting_size

    while font_size > min_size:
        width = pdf.stringWidth(
            text,
            "Helvetica-Bold",
            font_size
        )

        if width <= max_width:
            break

        font_size -= 1

    pdf.setFont("Helvetica-Bold", font_size)
    pdf.drawCentredString(x, y, text)


def render_certificate(
    output_path: str,
    event_name: str,
    issue_date: str,
    recipient_name: str,
    achievement: str
):
    output = Path(output_path)

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    pdf = canvas.Canvas(
        str(output),
        pagesize=landscape(A4)
    )

    # White background
    pdf.setFillColor(colors.white)

    pdf.rect(
        0,
        0,
        PAGE_WIDTH,
        PAGE_HEIGHT,
        fill=1,
        stroke=0
    )

    # Certificate border
    pdf.setStrokeColor(
        colors.HexColor("#1F4E79")
    )

    pdf.setLineWidth(5)

    pdf.rect(
        25,
        25,
        PAGE_WIDTH - 50,
        PAGE_HEIGHT - 50,
        fill=0,
        stroke=1
    )

    # Certificate title
    pdf.setFillColor(
        colors.HexColor("#1F4E79")
    )

    pdf.setFont(
        "Helvetica-Bold",
        34
    )

    pdf.drawCentredString(
        PAGE_WIDTH / 2,
        PAGE_HEIGHT - 100,
        "CERTIFICATE OF"
    )

    pdf.drawCentredString(
        PAGE_WIDTH / 2,
        PAGE_HEIGHT - 145,
        achievement.upper()
    )

    # Description
    pdf.setFillColor(colors.black)

    pdf.setFont(
        "Helvetica",
        16
    )

    pdf.drawCentredString(
        PAGE_WIDTH / 2,
        PAGE_HEIGHT - 205,
        "This certificate is proudly presented to"
    )

    # Recipient name
    draw_fitted_text(
        pdf,
        recipient_name,
        PAGE_WIDTH / 2,
        PAGE_HEIGHT - 260,
        PAGE_WIDTH - 160,
        starting_size=32
    )

    # Event name
    pdf.setFont(
        "Helvetica",
        16
    )

    pdf.drawCentredString(
        PAGE_WIDTH / 2,
        PAGE_HEIGHT - 315,
        f"for participating in {event_name}"
    )

    # Issue date
    pdf.setFont(
        "Helvetica",
        13
    )

    pdf.drawCentredString(
        PAGE_WIDTH / 2,
        90,
        f"Issue Date: {issue_date}"
    )

    pdf.save()