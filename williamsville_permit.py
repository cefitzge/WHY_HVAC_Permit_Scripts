import os
import re
from datetime import datetime
from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import io

TEMPLATE = "Williamsville HVAC permit.pdf"
INPUT = "Customer_data.txt"
SIGNATURE = "Dollendorf_sig.png"

# --- Read Customer Data ---
with open(INPUT, "r") as f:
    lines = [line.strip() for line in f if line.strip()]

# Customer info
customer_name = lines[0]

# Street address (number + street only)
street_address_full = lines[1].split(",")[0].strip()

# Check for second address line (if exists at end of file)
second_address = ""
if len(lines) > 6:
    second_address = lines[-1].strip()

# Phone number format XXX XXX-XXXX
phone_number_raw = lines[2].replace("(", "").replace(")", "").replace(" ", "")
phone_number = f"{phone_number_raw[:3]} {phone_number_raw[3:]}"  # keeps dash intact

# Date of job (from file)
date_of_job = lines[4]  # MM/DD/YYYY

# --- Prompts ---
estimated_cost = input("Enter estimated cost: ")

heat_check = input("Repair/replace heating? (y/n): ").strip().lower() == "y"
ac_check = input("Doing AC work? (y/n): ").strip().lower() == "y"

ac_new = ac_replace = False
if ac_check:
    ac_type = input("Is it new or replacement AC? (new/replace): ").strip().lower()
    ac_new = ac_type == "new"
    ac_replace = ac_type == "replace"

# Today's date (MM/DD/YY)
today = datetime.now().strftime("%m/%d/%y")

# --- Load template for page size ---
template_pdf = PdfReader(TEMPLATE)
page0 = template_pdf.pages[0]
try:
    llx = float(page0.MediaBox[0])
    lly = float(page0.MediaBox[1])
    urx = float(page0.MediaBox[2])
    ury = float(page0.MediaBox[3])
    page_width_pts = urx - llx
    page_height_pts = ury - lly
except Exception:
    page_width_pts, page_height_pts = letter

def to_points_top_origin(x_in_inches, y_in_inches):
    x_pts = x_in_inches * 72.0
    y_pts_from_top = y_in_inches * 72.0
    y_pts = page_height_pts - y_pts_from_top
    return x_pts, y_pts

# --- Create overlay PDF ---
packet = io.BytesIO()
c = canvas.Canvas(packet, pagesize=(page_width_pts, page_height_pts))
c.setFont("Helvetica", 10)

# Draw text fields
c.drawString(*to_points_top_origin(1.65, 2.71), street_address_full)
c.drawString(*to_points_top_origin(1.52, 4.03), estimated_cost)
c.drawString(*to_points_top_origin(1.02, 4.72), customer_name)

# Second address or same as job address
if second_address:
    c.drawString(*to_points_top_origin(1.14, 5.00), second_address)
else:
    c.drawString(*to_points_top_origin(1.14, 5.00), street_address_full)

# Phone number
c.drawString(*to_points_top_origin(5.78, 4.68), phone_number)

# Job date
c.drawString(*to_points_top_origin(1.96, 6.49), date_of_job)

# Today's date
c.drawString(*to_points_top_origin(6.46, 9.00), today)

# Draw signature
try:
    sig = ImageReader(SIGNATURE)
    c.drawImage(sig, *to_points_top_origin(1.84, 9.36), width=100, height=50, mask='auto')
except Exception as e:
    print(f"⚠️ Could not add signature image: {e}")

# --- Checkboxes ---
checkbox_size = 8

# Always checked box
c.rect(*to_points_top_origin(2.53, 5.47), checkbox_size, checkbox_size, fill=1)

if heat_check:
    c.rect(*to_points_top_origin(5.02, 5.93), checkbox_size, checkbox_size, fill=1)
if ac_new:
    c.rect(*to_points_top_origin(2.51, 6.20), checkbox_size, checkbox_size, fill=1)
if ac_replace:
    c.rect(*to_points_top_origin(5.02, 6.20), checkbox_size, checkbox_size, fill=1)

c.save()
packet.seek(0)
overlay_pdf = PdfReader(packet)

# --- Merge overlay onto template ---
for page, overlay in zip(template_pdf.pages, overlay_pdf.pages):
    merger = PageMerge(page)
    merger.add(overlay).render()

# --- Output File ---
customer_last_name = customer_name.split()[-1]
output_filename = f"{customer_last_name} Williamsville permit.pdf"
PdfWriter().write(output_filename, template_pdf)
print(f"✅ PDF created and saved as '{output_filename}'")

# --- Ask to print ---
print_now = input("Do you want to print this PDF? (y/n): ").strip().lower()
if print_now == "y":
    os.startfile(output_filename, "print")
    print("📄 Sent to printer.")
else:
    print("❌ Printing skipped. You can review or fix the PDF.")

# --- Ask to delete the PDF ---
delete_pdf = input(f"Do you want to delete '{output_filename}'? (y/n): ").strip().lower()
if delete_pdf == "y":
    try:
        os.remove(output_filename)
        print(f"🗑️ '{output_filename}' deleted.")
    except Exception as e:
        print(f"⚠️ Could not delete file: {e}")
else:
    print(f"✅ '{output_filename}' kept.")
    print(f"✅ '{output_filename}' kept.")
