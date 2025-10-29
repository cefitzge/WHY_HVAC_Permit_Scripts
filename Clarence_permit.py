import os
import io
import datetime
from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

TEMPLATE = "Clarence HVAC permit.pdf"
INPUT = "Customer_data.txt"
OUTPUT_DIR = r"\\RPIDCROOT\RedirectedFolders\cef\Desktop"

# --- Read Customer Data ---
with open(INPUT, "r") as f:
    lines = [line.strip() for line in f if line.strip()]

# --- Split address ---
address_parts = [part.strip() for part in lines[1].split(",")]
if len(address_parts) >= 3:
    job_address = address_parts[0]
    city_state_zip = f"{address_parts[1]}, {address_parts[2]}"
else:
    job_address = lines[1]
    city_state_zip = ""

# --- Second address logic ---
second_address = lines[6] if len(lines) > 6 else job_address

# --- Prompt for variable fields ---
job_description = input("Enter Job Description: ")
job_cost = input("Enter Job Cost Estimate: ")

# --- Today's date ---
today = datetime.date.today().strftime("%m/%d/%Y")

# --- Data Map ---
data = {
    "today": today,
    "job_description": job_description,
    "job_cost": job_cost,
    "date_of_job": lines[4],
    "job_address": job_address,
    "name": lines[0],
    "second_address": second_address,
    "phone": lines[2],
}

# --- Load template ---
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

# --- Create overlay ---
packet = io.BytesIO()
c = canvas.Canvas(packet, pagesize=(page_width_pts, page_height_pts))
c.setFont("Helvetica", 10)

c.drawString(*to_points_top_origin(1.88, 1.41), data["today"])
c.drawString(*to_points_top_origin(6.69, 8.19), data["today"])
c.drawString(*to_points_top_origin(2.65, 2.02), data["job_description"])
c.drawString(*to_points_top_origin(2.4, 2.55), f"${data['job_cost']}")
c.drawString(*to_points_top_origin(5.57, 2.53), data["date_of_job"])
c.drawString(*to_points_top_origin(2.28, 2.93), data["job_address"])
c.drawString(*to_points_top_origin(2.28, 3.24), data["name"])
c.drawString(*to_points_top_origin(2.28, 3.51), data["second_address"])
c.drawString(*to_points_top_origin(2.28, 3.8), data["phone"])

c.save()
packet.seek(0)
overlay_pdf = PdfReader(packet)

# --- Merge overlay onto template ---
for page, overlay in zip(template_pdf.pages, overlay_pdf.pages):
    merger = PageMerge(page)
    merger.add(overlay).render()

# --- Output file path ---
customer_last_name = lines[0].split()[-1]
output_filename = os.path.join(OUTPUT_DIR, f"{customer_last_name} Clarence permit.pdf")
PdfWriter().write(output_filename, template_pdf)

print(f" PDF created and saved as '{output_filename}'")

# --- Ask to print ---
print_now = input("Do you want to print this PDF? (y/n): ").strip().lower()
if print_now == "y":
    try:
        os.startfile(output_filename, "print")
        print(" Sent to printer.")
    except Exception as e:
        print(f" Printing failed: {e}")
else:
    print(" Printing skipped.")

# --- Ask to delete ---
delete_pdf = input(f"Do you want to delete '{output_filename}'? (y/n): ").strip().lower()
if delete_pdf == "y":
    try:
        os.remove(output_filename)
        print(f"🗑️ '{output_filename}' deleted.")
    except Exception as e:
        print(f" Could not delete file: {e}")
else:
    print(f" '{output_filename}' kept.")
