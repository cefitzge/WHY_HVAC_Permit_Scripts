import os
import io
import re
import datetime
import subprocess
from pdfrw import PdfReader, PdfWriter, PageMerge, PdfDict
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

TEMPLATE = "City of Lockport water heater boiler furnace.pdf"
INPUT = "Customer_data.txt"
SIGNATURE = "Dollendorf_sig.png"
OUTPUT_DIR = r"\\RPIDCROOT\RedirectedFolders\cef\Desktop"

# --- Read Customer Data ---
with open(INPUT, "r") as f:
    lines = [line.strip() for line in f if line.strip()]

customer_name = lines[0]
phone_number = lines[2]
second_address = lines[6] if len(lines) > 6 and lines[6].strip() else ""

# --- Extract street only (up to Rd, St, Ave, etc.) ---
full_address = lines[1]
street_match = re.match(
    r"^(.*?\b(?:St|Street|Rd|Road|Ave|Avenue|Dr|Drive|Blvd|Lane|Ln|Way|Ct)\b)",
    full_address,
    re.IGNORECASE,
)
street_address = street_match.group(1).strip() if street_match else full_address.strip()

# --- Extract town + zip only if second address exists ---
town, zip_code = "", ""
if second_address:
    parts = [p.strip() for p in second_address.split(",")]
    if len(parts) >= 2:
        town = parts[1]
    if len(parts) >= 3:
        zip_section = parts[-1]
        zip_parts = zip_section.split()
        zip_code = zip_parts[-1] if zip_parts else ""

# --- Prompts ---
estimated_cost = input("Enter estimated cost: ")
forced_air_input = input("Forced air? (y/n): ").strip().lower()
forced_air_check = forced_air_input in ["y", "yes"]

boiler_input = input("Boiler? (y/n): ").strip().lower()
boiler_check = boiler_input in ["y", "yes"]

# --- Today's date ---
today_str = datetime.date.today().strftime("%m/%d/%Y")

# --- Load template for page size ---
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
c.setFont("Helvetica", 12)  # Slightly larger text

# Text fields
c.drawString(*to_points_top_origin(2.27, 2.82), street_address)
c.drawString(*to_points_top_origin(5.59, 2.79), today_str)
c.drawString(*to_points_top_origin(6.19, 9.73), today_str)
c.drawString(*to_points_top_origin(1.83, 3.19), customer_name)

if second_address:
    c.drawString(*to_points_top_origin(5.58, 3.17), street_address)
    c.drawString(*to_points_top_origin(3.71, 3.59), town)
    c.drawString(*to_points_top_origin(5.96, 3.59), zip_code)

c.drawString(*to_points_top_origin(2.62, 3.97), f"${estimated_cost}")
c.drawString(*to_points_top_origin(1.83, 3.57), phone_number)

# --- Checkboxes as visible ✓
c.setFont("Helvetica-Bold", 14)
if forced_air_check:
    c.drawString(*to_points_top_origin(1.38, 6.48), "✓")
if boiler_check:
    c.drawString(*to_points_top_origin(2.95, 6.48), "✓")

# --- Signature ---
try:
    sig = ImageReader(SIGNATURE)
    c.drawImage(sig, *to_points_top_origin(3.04, 10.25), width=120, height=60, mask='auto')
except Exception as e:
    print(f"⚠️ Could not add signature image: {e}")

c.save()
packet.seek(0)
overlay_pdf = PdfReader(packet)

# --- Merge overlay onto template ---
for page, overlay in zip(template_pdf.pages, overlay_pdf.pages):
    merger = PageMerge(page)
    merger.add(overlay).render()

# --- Flatten PDF ---
for page in template_pdf.pages:
    if hasattr(page, 'Annots') and page.Annots:
        for annot in page.Annots:
            if annot.get('/V'):
                page_contents = page.Contents.stream if page.Contents else ''
                value = annot.V.to_unicode() if hasattr(annot.V, 'to_unicode') else str(annot.V)
                page.Contents = PdfDict(stream=f"{value}\n{page_contents}")
        page.Annots = []

# --- Output ---
customer_last_name = customer_name.split()[-1]
output_filename = f"{customer_last_name} Lockport permit.pdf"
output_path = os.path.join(OUTPUT_DIR, output_filename)
PdfWriter().write(output_path, template_pdf)

print(f"✅ PDF created and saved as '{output_path}'")

# --- Ask to print ---
print_now = input("Do you want to print this PDF? (y/n): ").strip().lower()
if print_now == "y":
    try:
        os.startfile(output_path, "print")  # Prints silently using default PDF app
        print("📄 Sent to printer.")
    except Exception as e:
        print(f"⚠️ Could not print file: {e}")
else:
    print("❌ Printing skipped.")

# --- Ask to delete ---
delete_pdf = input(f"Do you want to delete '{output_filename}' from Desktop? (y/n): ").strip().lower()
if delete_pdf == "y":
    try:
        os.remove(output_path)
        print(f"🗑️ '{output_filename}' deleted from Desktop.")
    except Exception as e:
        print(f"⚠️ Could not delete file: {e}")
else:
    print(f"✅ '{output_filename}' kept on Desktop.")
