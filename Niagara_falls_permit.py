import os
import io
import datetime
import re
from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

# --- Config ---
TEMPLATE = "Niagara Falls HVAC permit.pdf"
INPUT = "Customer_data.txt"
SIGNATURE = "signature.png"
OUTPUT_DIR = r"\\RPIDCROOT\RedirectedFolders\cef\Desktop"

# --- Read customer data ---
with open(INPUT, "r") as f:
    lines = [line.strip() for line in f if line.strip()]

customer_name = lines[0]
phone_raw = lines[2]

# --- Full address ---
full_address = lines[1]  # e.g., "123 Main St, Niagara Falls, NY 14301"

# Secondary address (optional)
secondary_address = lines[6] if len(lines) > 6 and lines[6].strip() else full_address

# --- Phone number formatting ---
digits = re.sub(r"\D", "", phone_raw)
area_code = digits[:3]
rest_number = f"{digits[3:6]}-{digits[6:]}"  # XXX-XXXX

# --- Prompts ---
fee = input("Enter permit fee: ")
job_description = input("Enter job description: ")

# Today's date
today_str = datetime.date.today().strftime("%m/%d/%Y")

# --- Load template ---
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

# Draw fields
c.drawString(*to_points_top_origin(4.65, 1.4), f"${fee}")
c.drawString(*to_points_top_origin(6.27, 1.4), today_str)
c.drawString(*to_points_top_origin(2.55, 2.94), full_address)         # Address line 1
c.drawString(*to_points_top_origin(5.26, 3.13), secondary_address)    # Address line 2
c.drawString(*to_points_top_origin(1.88, 3.13), customer_name)
c.drawString(*to_points_top_origin(2.76, 3.34), area_code)
c.drawString(*to_points_top_origin(3.22, 3.34), rest_number)
c.drawString(*to_points_top_origin(1.3, 3.89), job_description)

# Draw signature
try:
    sig = ImageReader(SIGNATURE)
    c.drawImage(sig, *to_points_top_origin(1.28, 5.1), width=120, height=60, mask='auto')
except Exception as e:
    print(f" Could not add signature image: {e}")

c.save()
packet.seek(0)
overlay_pdf = PdfReader(packet)

# --- Merge overlay onto template ---
for page, overlay in zip(template_pdf.pages, overlay_pdf.pages):
    merger = PageMerge(page)
    merger.add(overlay).render()

# --- Output ---
customer_last_name = customer_name.split()[-1]
output_filename = f"{customer_last_name} Niagara Falls permit.pdf"
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
