import os
from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import io

TEMPLATE = "Amherst HVAC permit.pdf"
INPUT = "Customer_data.txt"
SIGNATURE = "signature.png"
OUTPUT_DIR = r"\\RPIDCROOT\RedirectedFolders\cef\Desktop"

# --- Read Customer Data ---
with open(INPUT, "r") as f:
    lines = [line.strip() for line in f if line.strip()]

# Customer info
customer_name = lines[0]
phone_number = lines[2]
second_address = lines[6] if len(lines) > 6 else ""  # Optional second address
street_address_parts = [part.strip() for part in lines[1].split(",")]
street_address = ", ".join(street_address_parts[:-2]) if len(street_address_parts) > 2 else street_address_parts[0]
city_state_zip = ", ".join(street_address_parts[-2:]) if len(street_address_parts) >= 2 else ""

# --- Prompts ---
estimated_value = input("Enter estimated cost: ")
description_of_work = input("Enter description of work: ")
permit_fee = input("Enter permit fee: ")

# --- Checkbox prompts (robust) ---
furnace_input = input("Heating equipment (yes/no)? ").strip().lower()
furnace_check = furnace_input in ["y", "yes"]

ac_input = input("AC equipment needed (yes/no)? ").strip().lower()
ac_needed = ac_input in ["y", "yes"]
if ac_needed:
    ac_option = input("AC type (new/replace)? ").strip().lower()
else:
    ac_option = None

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
c.drawString(*to_points_top_origin(1.45, 1.6), street_address)
c.drawString(*to_points_top_origin(1.84, 2.93), customer_name)
c.drawString(*to_points_top_origin(5.72, 2.93), phone_number)
c.drawString(*to_points_top_origin(1.91, 3.26), second_address)
c.drawString(*to_points_top_origin(2.35, 3.62), estimated_value)
c.drawString(*to_points_top_origin(2.31, 3.93), description_of_work)
c.drawString(*to_points_top_origin(6.18, 3.61), lines[4])  # Date of work
c.drawString(*to_points_top_origin(1.58, 8.3), f"${permit_fee}")  # Permit fee

# Draw signature image
try:
    sig = ImageReader(SIGNATURE)
    c.drawImage(sig, *to_points_top_origin(4.45, 8.75), width=100, height=50, mask='auto')
except Exception as e:
    print(f" Could not add signature image: {e}")

# Draw checkboxes (smaller size)
checkbox_size = 8  # points
if furnace_check:
    c.rect(*to_points_top_origin(0.4595, 4.27), checkbox_size, checkbox_size, fill=1)

if ac_needed:
    if ac_option == "new":
        c.rect(*to_points_top_origin(0.4595, 4.44), checkbox_size, checkbox_size, fill=1)
    elif ac_option == "replace":
        c.rect(*to_points_top_origin(0.4595, 4.61), checkbox_size, checkbox_size, fill=1)

c.save()
packet.seek(0)
overlay_pdf = PdfReader(packet)

# --- Merge overlay onto template ---
for page, overlay in zip(template_pdf.pages, overlay_pdf.pages):
    merger = PageMerge(page)
    merger.add(overlay).render()

# --- Output File ---
customer_last_name = customer_name.split()[-1]
output_filename = os.path.join(OUTPUT_DIR, f"{customer_last_name} permit app.pdf")
PdfWriter().write(output_filename, template_pdf)
print(f"✅ PDF created and saved as '{output_filename}'")

# --- Ask to delete the PDF ---
delete_pdf = input(f"Do you want to delete '{output_filename}'? (y/n): ").strip().lower()
if delete_pdf == "y":
    try:
        os.remove(output_filename)
        print(f" '{output_filename}' deleted.")
    except Exception as e:
        print(f" Could not delete file: {e}")
else:
    print(f" '{output_filename}' kept.")
