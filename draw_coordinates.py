import matplotlib.pyplot as plt
from shapely.geometry import Point, shape
import json

# Load polygon
with open("akron.geojson") as f:
    gj = json.load(f)
polygon = shape(gj["features"][0]["geometry"])

# Plot polygon
x, y = polygon.exterior.xy
plt.plot(x, y, 'blue')

plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title("Akron")
plt.show()
