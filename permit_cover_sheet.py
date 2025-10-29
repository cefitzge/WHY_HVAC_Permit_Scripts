import os
import io
from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

TEMPLATE = "Permit cover sheet.pdf"
INPUT = "Customer_data.txt"
OUTPUT_DIR = r"\\RPIDCROOT\RedirectedFolders\cef\Desktop"

# --- Read Customer Data ---
with open(INPUT, "r") as f:
    lines = [line.strip() for line in f if line.strip()]

# --- Split address cleanly ---
full_address = lines[1]
address_parts = [part.strip() for part in full_address.split(",")]

if len(address_parts) >= 3:
    street_address = address_parts[0]
    city_state_zip = f"{address_parts[1]}, {address_parts[2]}"
elif len(address_parts) == 2:
    street_address = address_parts[0]
    city_state_zip = address_parts[1]
else:
    street_address = full_address
    city_state_zip = ""

# --- Prompt for variable fields ---
municipality = input("Enter municipality: ")
inspection_time = input("Enter inspection time: ")
job_description = input("Enter Job/Project Description: ")
permit_fee = input("Enter Permit Fee: ")

# --- Hardcoded filled-by name ---
filled_by = "Courtney"

# --- Data Map ---
data = {
    "Customer Name": lines[0],
    "Address 1": street_address,
    "Address 2": city_state_zip,
    "Phone Number": lines[2],
    "Job Number": lines[3],
    "Date of JobProject": lines[4],
    "JobProject Info 1": job_description,
    "JobProject Info 2": lines[5],  # Technician
    "JobProject Info 3": f"{filled_by}",
    "Primary Municipality": municipality,
    "Inspection Time": inspection_time,
    "Permit Fee": permit_fee,
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

# --- Create Overlay ---
packet = io.BytesIO()
c = canvas.Canvas(packet, pagesize=(page_width_pts, page_height_pts))
c.setFont("Helvetica", 10)

# Draw fields
c.drawString(*to_points_top_origin(2.24, 1.71), data["Customer Name"])
c.drawString(*to_points_top_origin(1.69, 2.14), data["Address 1"])
c.drawString(*to_points_top_origin(1.69, 2.45), data["Address 2"])
c.drawString(*to_points_top_origin(5.56, 1.71), data["Job Number"])
c.drawString(*to_points_top_origin(5.79, 2.09), data["Phone Number"])
c.drawString(*to_points_top_origin(1.06, 3.45), data["JobProject Info 1"])
c.drawString(*to_points_top_origin(2.73, 5.12), data["Date of JobProject"])
c.drawString(*to_points_top_origin(2.73, 5.39), data["Inspection Time"])
c.drawString(*to_points_top_origin(2.73, 6.10), data["Primary Municipality"])
c.drawString(*to_points_top_origin(5.97, 6.10), f"${data['Permit Fee']}")
c.drawString(*to_points_top_origin(2.73, 7.08), data["JobProject Info 2"])
c.drawString(*to_points_top_origin(2.73, 7.40), data["JobProject Info 3"])
c.save()

packet.seek(0)
overlay_pdf = PdfReader(packet)

# --- Merge overlay ---
for page, overlay in zip(template_pdf.pages, overlay_pdf.pages):
    merger = PageMerge(page)
    merger.add(overlay).render()

# --- Output File ---
customer_last_name = lines[0].split()[-1]
output_filename = f"{customer_last_name} cover sheet.pdf"
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
