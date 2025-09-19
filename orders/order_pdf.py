from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from io import BytesIO

def generate_order_pdf(order):
    """
    Generate a professional PDF invoice for an order.
    Returns a BytesIO object containing the PDF.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 20)
    c.drawString(30, height - 50, "Order Invoice")

    c.setFont("Helvetica", 12)
    c.drawString(30, height - 80, f"Order ID: {order.order_id}")
    c.drawString(30, height - 100, f"Order Number: {order.order_number}")
    c.drawString(30, height - 120, f"Shop: {order.shop.shop_name}")
    c.drawString(30, height - 140, f"Dispatcher: {getattr(order.dispatcher, 'name', '-')}")
    c.drawString(30, height - 160, f"Delivery Rider: {getattr(order.delivery_rider, 'name', '-')}")
    c.drawString(30, height - 180, f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}")

    # Table header
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, height - 220, "Product")
    c.drawString(250, height - 220, "Unit Price")
    c.drawString(350, height - 220, "Qty")
    c.drawString(420, height - 220, "Discount")
    c.drawString(500, height - 220, "Subtotal")

    # Table rows
    y = height - 240
    c.setFont("Helvetica", 12)
    for item in order.items.all():
        subtotal = (item.discount_price or item.unit_price) * item.quantity

        c.drawString(30, y, item.product.name)
        c.drawRightString(300, y, f"{item.unit_price}")
        c.drawRightString(380, y, str(item.quantity))
        c.drawRightString(460, y, str(item.discount_price or "-"))
        c.drawRightString(550, y, f"{subtotal}")

        y -= 20
        if y < 80:
            c.showPage()
            y = height - 80

    # Totals
    c.setFont("Helvetica-Bold", 12)
    c.line(30, y - 10, 550, y - 10)
    y -= 30
    c.drawRightString(550, y, f"Subtotal: {order.subtotal}")
    y -= 20
    c.drawRightString(550, y, f"Total: {order.total_amount}")

    # Footer
    y -= 50
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(colors.grey)
    c.drawCentredString(width / 2, y, "Thank you for your order!")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
