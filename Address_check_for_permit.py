import csv
import requests
import json
import os
from shapely.geometry import Point, shape

# -------------------------------
# Config
# -------------------------------
BASE_DIR = r"C:\Users\cef\WHY_HVAC_Permit_Scripts"
PERMIT_FILE = os.path.join(BASE_DIR, "Permit_fee_check.txt")

POLYGONS = {
    "Williamsville": os.path.join(BASE_DIR, "williamsville.geojson"),
    "Sloan":        os.path.join(BASE_DIR, "sloan.geojson"),
    "Pendleton":    os.path.join(BASE_DIR, "pendleton.geojson"),
    "Kenmore":      os.path.join(BASE_DIR, "kenmore.geojson"),
    "Depew":        os.path.join(BASE_DIR, "depew.geojson"),
    "Orchard Park village": os.path.join(BASE_DIR, "orchard_park.geojson"),
    "Akron":        os.path.join(BASE_DIR, "akron.geojson"),    
    "Sanborn":      os.path.join(BASE_DIR, "sanborn.geojson"),
    "Angola":       os.path.join(BASE_DIR, "angola.geojson"),    
    "Derby":        os.path.join(BASE_DIR, "derby.geojson"),   
    "Youngstown":   os.path.join(BASE_DIR, "youngstown.geojson"),         
}

# -------------------------------
# Utilities
# -------------------------------
def load_permit_data(txt_file):
    permit_dict = {}
    with open(txt_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["Township"].strip().lower()
            permit_dict[key] = row
    return permit_dict

def load_polygons(polygon_map):
    loaded = {}
    for name, path in polygon_map.items():
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                gj = json.load(f)
            geom = shape(gj["features"][0]["geometry"])
            loaded[name] = geom
        except Exception:
            continue
    return loaded

def get_census_coordinates(address):
    url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
    params = {"address": address, "benchmark": "Public_AR_Current", "format": "json"}
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        coords = data['result']['addressMatches'][0]['coordinates']
        return coords['x'], coords['y']
    except Exception:
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
        geographies = geo_data['result']['geographies']
        if 'Places' in geographies and geographies['Places']:
            return geographies['Places'][0]['NAME']
        elif 'County Subdivisions' in geographies and geographies['County Subdivisions']:
            return geographies['County Subdivisions'][0]['NAME']
        return None
    except Exception:
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
def check_permit(township, work_type, permit_data):
    key = township.strip().lower()
    data = permit_data.get(key)
    if not data:
        print(f"❌ Township '{township}' not found in permit list.")
        return

    permit_required = False
    ask_ac_type = False

    special = data.get("Special_Calc", "").strip().upper() == "YES"

    if work_type == "F":
        permit_required = bool(data["Furnace_Cost"]) or special
    elif work_type == "AC":
        ac_new = data["AC_New_Cost"]
        ac_replace = data["AC_Replace_Cost"]
        permit_required = bool(ac_new or ac_replace) or special
        try:
            ac_new_val = float(ac_new) if ac_new else None
            ac_replace_val = float(ac_replace) if ac_replace else None
            if ac_new_val is not None and ac_replace_val is not None and ac_new_val != ac_replace_val:
                ask_ac_type = True
        except ValueError:
            pass
    elif work_type == "FAC":
        permit_required = bool(data["Furnace_Cost"] or data["AC_New_Cost"] or data["AC_Replace_Cost"]) or special
        try:
            ac_new_val = float(data["AC_New_Cost"]) if data["AC_New_Cost"] else None
            ac_replace_val = float(data["AC_Replace_Cost"]) if data["AC_Replace_Cost"] else None
            if ac_new_val is not None and ac_replace_val is not None and ac_new_val != ac_replace_val:
                ask_ac_type = True
        except ValueError:
            pass
    elif work_type == "B":
        permit_required = bool(data["Boiler_Cost"]) or special

    print(f"Township detected: {township}")
    print(f"Permit required? {'Yes' if permit_required else 'No'}")

# -------------------------------
# Main Loop
# -------------------------------
if __name__ == "__main__":
    permit_data = load_permit_data(PERMIT_FILE)
    polygons = load_polygons(POLYGONS)

    while True:
        address = input("\nAddress (or D to done): ").strip()
        if address.upper() == "D":
            break

        lon, lat = get_census_coordinates(address)
        township = None

        if lon is not None and lat is not None:
            point = Point(lon, lat)
            matched_polygon_name = None
            for name, geom in polygons.items():
                try:
                    if geom.intersects(point):
                        matched_polygon_name = name
                        break
                except Exception:
                    continue
            if matched_polygon_name:
                township = matched_polygon_name
            else:
                township = get_census_municipality(address)

        if not township:
            township = input("⚠️ Could not determine township. Enter manually: ").strip()

        work_type = get_work_type()
        check_permit(township, work_type, permit_data)
