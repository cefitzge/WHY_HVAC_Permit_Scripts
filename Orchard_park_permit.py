import os
import io
import re
import datetime
from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# --- Config ---
TEMPLATE = "Orchard Park HVAC permit.pdf"
INPUT = "Customer_data.txt"
OUTPUT_DIR = r"\\RPIDCROOT\RedirectedFolders\cef\Desktop"

# --- Read customer data ---
with open(INPUT, "r") as f:
    lines = [line.strip() for line in f if line.strip()]

customer_name = lines[0]
full_address = lines[1]
phone_number = lines[2] if len(lines) > 2 else ""
secondary_address = lines[6] if len(lines) > 6 and lines[6].strip() else ""

# --- Parse address components ---
address_pattern = re.match(r"(.+?),\s*([A-Za-z\s]+),\s*NY\s*(\d{5})", full_address)
if address_pattern:
    street_only = address_pattern.group(1).strip()
    city = address_pattern.group(2).strip()
    zip_code = address_pattern.group(3).strip()
else:
    street_only = full_address
    city = ""
    zip_code = ""

# Use second address for job location if available, otherwise main street address
job_address = secondary_address if secondary_address else street_only

# --- Prompts ---
estimated_cost = input("Enter estimated cost: ")
heating = input("Repairing/replacing heating equipment? (y/n): ").strip().lower()
doing_ac = input("Doing AC? (y/n): ").strip().lower()

ac_new = False
ac_replace = False
if doing_ac in ["y", "yes"]:
    ac_type = input("Is the AC new or replacement? (n/r): ").strip().lower()
    ac_new = ac_type.startswith("n")
    ac_replace = ac_type.startswith("r")

# --- Today's date ---
today_str = datetime.date.today().strftime("%m/%d/%Y")

# --- Load template and get size ---
template_pdf = PdfReader(TEMPLATE)
page0 = template_pdf.pages[0]
try:
    llx, lly, urx, ury = map(float, page0.MediaBox)
    page_width_pts = urx - llx
    page_height_pts = ury - lly
except Exception:
    page_width_pts, page_height_pts = letter

def to_points_top_origin(x_in_inches, y_in_inches):
    x_pts = x_in_inches * 72
    y_pts = page_height_pts - (y_in_inches * 72)
    return x_pts, y_pts

# --- Create overlay ---
packet = io.BytesIO()
c = canvas.Canvas(packet, pagesize=(page_width_pts, page_height_pts))
c.setFont("Helvetica", 12)

# --- Draw fields ---
c.drawString(*to_points_top_origin(0.98, 1.87), full_address)        # Full address
c.drawString(*to_points_top_origin(1.92, 5.5), job_address)          # Job/secondary address (street only)
c.drawString(*to_points_top_origin(1.92, 5.87), city)
c.drawString(*to_points_top_origin(5.6, 5.87), "NY")
c.drawString(*to_points_top_origin(7.26, 5.87), zip_code)
c.drawString(*to_points_top_origin(1.45, 2.15), f"${estimated_cost}")
c.drawString(*to_points_top_origin(2.0, 4.86), customer_name)
c.drawString(*to_points_top_origin(7.33, 0.56), today_str)           # Today's date
c.drawString(*to_points_top_origin(6.46, 5.55), phone_number)        # Phone number

# --- Draw checkboxes (visible above fillable layer) ---
checkbox_size = 10
checkbox_fill_color = 0.2  # gray tone for visibility

# Always fill main box
x, y = to_points_top_origin(2.5, 2.5)
c.setFillGray(checkbox_fill_color)
c.rect(x, y, checkbox_size, checkbox_size, fill=1)

# Heating
if heating in ["y", "yes"]:
    x, y = to_points_top_origin(5.12, 2.83)
    c.setFillGray(checkbox_fill_color)
    c.rect(x, y, checkbox_size, checkbox_size, fill=1)

# AC options
if ac_new:
    x, y = to_points_top_origin(2.49, 3.08)
    c.setFillGray(checkbox_fill_color)
    c.rect(x, y, checkbox_size, checkbox_size, fill=1)
elif ac_replace:
    x, y = to_points_top_origin(5.12, 3.08)
    c.setFillGray(checkbox_fill_color)
    c.rect(x, y, checkbox_size, checkbox_size, fill=1)

c.save()
packet.seek(0)
overlay_pdf = PdfReader(packet)

# --- Merge ---
for page, overlay in zip(template_pdf.pages, overlay_pdf.pages):
    merger = PageMerge(page)
    merger.add(overlay).render()

# --- Output ---
customer_last_name = customer_name.split()[-1]
output_filename = f"{customer_last_name} Orchard Park permit.pdf"
output_path = os.path.join(OUTPUT_DIR, output_filename)
PdfWriter().write(output_path, template_pdf)

print(f" PDF created and saved as '{output_path}'")

# --- Ask to print ---
print_now = input("Do you want to print this PDF? (y/n): ").strip().lower()
if print_now == "y":
    try:
        os.startfile(output_path, "print")
        print(" Sent to printer via default PDF handler.")
    except Exception as e:
        print(f" Could not print: {e}")
else:
    print(" Printing skipped.")

# --- Ask to delete ---
delete_pdf = input(f"Do you want to delete '{output_filename}' from Desktop? (y/n): ").strip().lower()
if delete_pdf == "y":
    try:
        os.remove(output_path)
        print(f" '{output_filename}' deleted from Desktop.")
    except Exception as e:
        print(f" Could not delete file: {e}")
else:
    print(f" '{output_filename}' kept on Desktop.")
