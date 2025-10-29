import os
import re
import io
from datetime import datetime
from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

# --- File Locations ---
TEMPLATE = "Cheektowaga permit.pdf"
INPUT = "Customer_data.txt"
SIGNATURE = "Dollendorf_sig.png"
OUTPUT_DIR = r"\\RPIDCROOT\RedirectedFolders\cef\Desktop"

# --- Read Customer Data ---
with open(INPUT, "r") as f:
    lines = [line.strip() for line in f if line.strip()]

customer_name = lines[0]

# Street address (number + street only)
street_address_full = lines[1].split(",")[0].strip()

# Zip last 3 digits
zip_match = re.search(r"\b\d{5}\b", lines[1])
zip_last3 = zip_match.group(0)[-3:] if zip_match else ""

# Format phone number: XXX XXX-XXXX
phone_number_raw = lines[2].replace("(", "").replace(")", "").replace(" ", "  ")
phone_number = f"{phone_number_raw[:3]} {phone_number_raw[3:]}"  # keeps the dash in the remaining part

# --- Today's Date ---
today = datetime.today()
month = str(today.month).zfill(2)
day = str(today.day).zfill(2)
year = str(today.year)[-2:]

# --- Prompts ---
estimated_cost = input("Enter estimated cost: ")

boiler_input = input("Replacing a boiler? (y/n): ").strip().lower()
boiler_check = boiler_input in ["y", "yes"]

if not boiler_check:
    furnace_check = True  # automatically yes if no boiler
else:
    furnace_input = input("Furnace/ductwork work? (y/n): ").strip().lower()
    furnace_check = furnace_input in ["y", "yes"]

# --- Load Template ---
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
    """Convert inches from top-left to PDF points (bottom-left origin)."""
    x_pts = x_in_inches * 72.0
    y_pts_from_top = y_in_inches * 72.0
    y_pts = page_height_pts - y_pts_from_top
    return x_pts, y_pts

# --- Create Overlay ---
packet = io.BytesIO()
c = canvas.Canvas(packet, pagesize=(page_width_pts, page_height_pts))
c.setFont("Helvetica", 10)

# Text fields
c.drawString(*to_points_top_origin(0.56, 3.60), customer_name)
c.drawString(*to_points_top_origin(0.56, 3.18), street_address_full)
c.drawString(*to_points_top_origin(7.5, 3.19), zip_last3)
c.drawString(*to_points_top_origin(5.02, 3.62), phone_number)
c.drawString(*to_points_top_origin(6.82, 8.07), estimated_cost)

# Today's date split MM/DD/YY
c.drawString(*to_points_top_origin(6.57, 9.59), month)
c.drawString(*to_points_top_origin(6.9, 9.59), day)
c.drawString(*to_points_top_origin(7.46, 9.59), year)

# Signature
try:
    sig = ImageReader(SIGNATURE)
    c.drawImage(sig, *to_points_top_origin(0.55, 9.96), width=100, height=50, mask="auto")
except Exception as e:
    print(f" Could not add signature image: {e}")

# Checkboxes
checkbox_size = 8
if boiler_check:
    c.rect(*to_points_top_origin(1.68, 4.74), checkbox_size, checkbox_size, fill=1)
if furnace_check:
    c.rect(*to_points_top_origin(2.41, 5.05), checkbox_size, checkbox_size, fill=1)

c.save()
packet.seek(0)
overlay_pdf = PdfReader(packet)

# --- Merge Overlay ---
for page, overlay in zip(template_pdf.pages, overlay_pdf.pages):
    merger = PageMerge(page)
    merger.add(overlay).render()

# --- Output File ---
customer_last_name = customer_name.split()[-1]
output_filename = f"{customer_last_name} Cheektowaga permit.pdf"
output_path = os.path.join(OUTPUT_DIR, output_filename)

PdfWriter().write(output_path, template_pdf)
print(f" PDF created and saved as '{output_path}'")

# --- Print Automatically if Wanted ---
print_now = input("Do you want to print this PDF? (y/n): ").strip().lower()
if print_now == "y":
    try:
        os.startfile(output_path, "print")
        print(" Sent to printer.")
    except Exception as e:
        print(f" Could not print file: {e}")
else:
    print(" Printing skipped.")

# --- Optionally Delete ---
delete_pdf = input(f"Do you want to delete '{output_filename}' from Desktop? (y/n): ").strip().lower()
if delete_pdf == "y":
    try:
        os.remove(output_path)
        print(f" '{output_filename}' deleted from Desktop.")
    except Exception as e:
        print(f" Could not delete file: {e}")
else:
    print(f" '{output_filename}' kept on Desktop.")
