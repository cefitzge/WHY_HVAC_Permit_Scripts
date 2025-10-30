# -------------------------------
# Hellow 
# -------------------------------
import csv
import re
import requests
import json
import os
import math
from shapely.geometry import Point, shape

# -------------------------------
# Config: paths to your files
# -------------------------------
BASE_DIR = r"C:\Users\cef\WHY_HVAC_Permit_Scripts"
CUSTOMER_FILE = os.path.join(BASE_DIR, "Customer_data.txt")
PERMIT_FILE = os.path.join(BASE_DIR, "Permit_fee_check.txt")

# List of polygon files you asked for (file must exist at these paths)
# The left side is a friendly name (used to override), the right side is filename on Desktop
POLYGONS = {
    "Williamsville": os.path.join(BASE_DIR, "williamsville.geojson"),
    "Sloan":        os.path.join(BASE_DIR, "sloan.geojson"),
    "Pendleton":    os.path.join(BASE_DIR, "pendleton.geojson"),
    "Kenmore":      os.path.join(BASE_DIR, "kenmore.geojson"),
    "Depew":        os.path.join(BASE_DIR, "depew.geojson"),
    "Orchard Park village": os.path.join(BASE_DIR, "orchard_park.geojson"),
    "Akron":        os.path.join(BASE_DIR, "akron.geojson"),    
    "Sanborn":        os.path.join(BASE_DIR, "sanborn.geojson"),
    "Angola":        os.path.join(BASE_DIR, "angola.geojson"),    
    "Derby":        os.path.join(BASE_DIR, "derby.geojson"),   
    "Youngstown":        os.path.join(BASE_DIR, "youngstown.geojson"),         
}

# -------------------------------
# Utility: load permit CSV
# -------------------------------
def load_permit_data(txt_file):
    permit_dict = {}
    with open(txt_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["Township"].strip().lower()
            permit_dict[key] = row
    return permit_dict

# -------------------------------
# Geocode (Census) functions
# -------------------------------
def get_census_coordinates(address):
    url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
    params = {"address": address, "benchmark": "Public_AR_Current", "format": "json"}
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
    except Exception as e:
        print(" Census geocode request failed:", e)
        return None, None

    try:
        coords = data['result']['addressMatches'][0]['coordinates']
        return coords['x'], coords['y']
    except (KeyError, IndexError):
        return None, None

def get_census_municipality(address):
    lon, lat = get_census_coordinates(address)
    if lon is None:
        return None
    geo_url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
    geo_params = {"x": lon, "y": lat, "benchmark": "Public_AR_Current", "vintage": "Current_Current", "format": "json"}
    try:
        geo_response = requests.get(geo_url, params=geo_params, timeout=10)
        geo_data = geo_response.json()
    except Exception as e:
        print(" Census geography request failed:", e)
        return None

    try:
        geographies = geo_data['result']['geographies']
        if 'Places' in geographies and geographies['Places']:
            return geographies['Places'][0]['NAME']
        elif 'County Subdivisions' in geographies and geographies['County Subdivisions']:
            return geographies['County Subdivisions'][0]['NAME']
        return None
    except (KeyError, IndexError):
        return None

# -------------------------------
# Load polygon files into memory
# -------------------------------
def load_polygons(polygon_map):
    loaded = {}
    for name, path in polygon_map.items():
        if not os.path.isfile(path):
            print(f" Polygon file not found for {name}: {path}  (skipping)")
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                gj = json.load(f)
            geom = shape(gj["features"][0]["geometry"])
            loaded[name] = geom
        except Exception as e:
            print(f" Failed to load polygon for {name} ({path}): {e}")
    return loaded

# -------------------------------
# Helpers for address extraction & input
# -------------------------------
def extract_address_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    # permissive: line starting with number and containing a 5-digit ZIP somewhere
    addr_pattern = re.compile(r"^\d+.*\d{5}")
    for line in lines:
        if addr_pattern.search(line):
            return line
    return None

def get_work_type():
    while True:
        work = input("Enter work type (F = Furnace, AC = AC, FAC = Furnace+AC, B = Boiler): ").strip().upper()
        if work in ["F", "AC", "FAC", "B"]:
            return work
        print("Invalid input. Try again.")

def get_ac_type():
    while True:
        ac_type = input("Is the AC New or Replacement? (N/R): ").strip().upper()
        if ac_type in ["N", "R"]:
            return ac_type
        print("Invalid input. Try again.")

# -------------------------------
# Permit logic 
# -------------------------------
def normalize_township(name: str) -> str:
    """Ensure consistent naming for lookups."""
    return name.strip().lower()

def check_permit(township, work_type, permit_data):
    key = normalize_township(township)

    # First, handle special calculation towns
    if township.lower() in ["amherst town", "niagara falls city", "north tonawanda city"]:
        price = special_calc_price(township, work_type, permit_data)
        if price is not None:
            print(f"Township detected: {township} (special calc)")
            print(f"Permit required? Yes")
            print(f"Permit price: ${price:.2f}")
            return

    # Fallback to regular CSV logic
    data = permit_data.get(key)
    if not data:
        print(f" Township '{township}' not found in permit list.")
        return

    permit_required = False
    ac_permit_required = False
    ask_ac_type = False
    price = 0.0

    def safe_float(val):
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    furnace_val = safe_float(data.get("Furnace_Cost"))
    ac_new_val = safe_float(data.get("AC_New_Cost"))
    ac_replace_val = safe_float(data.get("AC_Replace_Cost"))
    boiler_val = safe_float(data.get("Boiler_Cost"))
    fac_val = safe_float(data.get("FAC_Cost"))
    separate = data.get("Separate", "").strip().lower() == "yes"
    special = data.get("Special_Calc", "").strip().lower() == "yes"

    # Base permit logic
    if work_type == "F":
        permit_required = furnace_val > 0 or special
        price = furnace_val

    elif work_type == "AC":
        ac_permit_required = ac_new_val > 0 or ac_replace_val > 0 or special
        permit_required = ac_permit_required
        if ac_new_val != ac_replace_val:
            ask_ac_type = True
            price = max(ac_new_val, ac_replace_val)
        else:
            price = ac_new_val

    elif work_type == "FAC":
        permit_required = furnace_val > 0 or ac_new_val > 0 or ac_replace_val > 0 or special
        price = furnace_val + (max(ac_new_val, ac_replace_val) if separate else 0.0)
        if ac_new_val != ac_replace_val:
            ask_ac_type = True

    elif work_type == "B":
        permit_required = boiler_val > 0 or special
        price = boiler_val

    # AC type selection (applies before any special fee)
    if ask_ac_type:
        ac_type = get_ac_type()
        print(f"AC type selected: {'New' if ac_type == 'N' else 'Replacement'}")
        if work_type == "AC":
            price = ac_new_val if ac_type == "N" else ac_replace_val
        elif work_type == "FAC" and separate:
            price = furnace_val + (ac_new_val if ac_type == "N" else ac_replace_val)

    print(f"Township detected: {township}")
    print(f"Permit required? {'Yes' if permit_required else 'No'}")
    print(f"Permit price: ${price:.2f}")
# -------------------------------
# Special Permit Cost Calculation
# -------------------------------
def special_calc_price(township, work_type, permit_data):
    key = normalize_township(township)

    if township.lower() == "amherst":
        # Amherst: use CSV as before
        data = permit_data[key]
        try:
            furnace_cost = float(data.get("Furnace_Cost") or 0)
            ac_new_cost = float(data.get("AC_New_Cost") or 0)
            ac_replace_cost = float(data.get("AC_Replace_Cost") or 0)
            boiler_cost = float(data.get("Boiler_Cost") or 0)
            fac_cost = float(data.get("FAC_Cost") or 0)
            extra_fee = 1.75
        except ValueError:
            print("⚠️ Invalid numbers in CSV for Amherst")
            return None

        if work_type == "F":
            return furnace_cost + extra_fee
        elif work_type == "AC":
            if ac_new_cost != ac_replace_cost:
                ac_type = get_ac_type()
                return (ac_new_cost if ac_type == "N" else ac_replace_cost) + extra_fee
            else:
                return ac_new_cost + extra_fee
        elif work_type == "FAC":
            return fac_cost + extra_fee
        elif work_type == "B":
            return boiler_cost + extra_fee

    elif township.lower() == "niagara falls city":
        # Ask for cost
        total_cost = None
        while total_cost is None:
            try:
                total_cost = float(input("Enter installation cost for Niagara Falls City: "))
            except ValueError:
                print("Invalid number, try again.")
        # Round up to next 1000
        rounded = math.ceil(total_cost / 1000) * 1000
        price = 25 + max(0, (rounded - 1000) // 1000 * 10)
        print("calculation = 25 for first $1000 and $10 for remaining fractions of 1000")
        print(f"                 25.0 plus {price - 25.0} = {price}")
        return price

    elif township.lower() == "north tonawanda city":
        total_cost = None
        while total_cost is None:
            try:
                total_cost = float(input("Enter installation cost for North Tonawanda: "))
            except ValueError:
                print("Invalid number, try again.")
        # Round up to next 1000
        rounded = math.ceil(total_cost / 1000) * 1000
        additional_units = max(0, (rounded) // 1000)  # only above first 1000
        price = 35 + additional_units * 8
        print("calculation = 35 base price and $8 * total cost/1000")
        print(f"                 35.0 plus {price - 35.0} = {price}")
        print("Check with North Tonawanada town if smoke detectors and COs are needed: if yes, add 75")
        return price

    # Default: not a special calc
    return None
# -------------------------------
# Main flow
# -------------------------------
if __name__ == "__main__":
    # Load data
    permit_data = load_permit_data(PERMIT_FILE)
    polygons = load_polygons(POLYGONS)

    # Extract address from customer file
    address = extract_address_from_file(CUSTOMER_FILE)
    if not address:
        print("Could not find an address in the customer file.")
        raise SystemExit(1)

    # Geocode to lon/lat
    lon, lat = get_census_coordinates(address)
    township = None

    if lon is None or lat is None:
        print(" Census geocode failed for address:", address)
        township = input("Enter the township manually: ").strip()
        print(f"Township entered manually: {township}")
    else:
        # Check polygons first — override Census if inside a polygon
        point = Point(lon, lat)
        matched_polygon_name = None
        for name, geom in polygons.items():
            try:
                if geom.intersects(point):
                    matched_polygon_name = name
                    break
            except Exception as e:
                print(f" Error testing polygon {name}: {e}")

        if matched_polygon_name:
            township = matched_polygon_name
            print(f"Township detected from polygon: {township}")
        else:
            # Fallback to Census municipality (favor County Subdivision if available)
            lon, lat = get_census_coordinates(address)
            geo_url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
            geo_params = {
                "x": lon, "y": lat,
                "benchmark": "Public_AR_Current",
                "vintage": "Current_Current",
                "format": "json"
            }
            try:
                geo_response = requests.get(geo_url, params=geo_params, timeout=10)
                geo_data = geo_response.json()
                geographies = geo_data['result']['geographies']
                if 'County Subdivisions' in geographies and geographies['County Subdivisions']:
                    township = geographies['County Subdivisions'][0]['NAME']
                    print(f"Township detected from Census (County Subdivision): {township}")
                elif 'Places' in geographies and geographies['Places']:
                    township = geographies['Places'][0]['NAME']
                    print(f"Township detected from Census (Place): {township}")
                else:
                    township = input(" Could not determine township from address. Enter the township manually: ").strip()
                    print(f"Township entered manually: {township}")
            except Exception as e:
                print(" Census geography request failed:", e)
                township = input("Enter the township manually: ").strip()
                print(f"Township entered manually: {township}")

    # Prompt user for work type and check permit (including special calcs)
    work_type = get_work_type()

    # First check if this is a special calc case
    special_price = special_calc_price(township, work_type, permit_data)
    if special_price is not None:
        print(f"Township detected: {township} (special calc)")
        print(f"Permit required? Yes")
        print(f"Permit price: ${special_price:.2f}")
    else:
        # Use standard permit logic
        check_permit(township, work_type, permit_data)
    
    if township.strip().lower() in ["clarence", "orchard park town"]:
        print(" print signed estimate invoice ")
    if township.strip().lower() in ["north tonawanda city"]:
        print("inspection: will send info to Jeff L")
    if township.strip().lower() in ["niagara falls city"]:
        print("inspection: will send pics")