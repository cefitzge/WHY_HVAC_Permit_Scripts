# WHY_HVAC_Permit_Scripts
These scripts are used for filing permits for HVAC jobs in the western New York area. Permits depend on municipality. Job addresses are checked using the https://geocoding.geo.census.gov and the coordinates are used to make the determination. However smaller townships/villages are often marked as the larger surrounding town and have to be checked separately. To handle this, these townships have geojson coordinate maps that override the geocoding website determination. The current list of relevent townships in WNY to check are: Angola, Depew, Derby, Kenmore, Orchard Park, Pendleton, Sanborn, Sloan, Williamsville, and Youngstown.
The township polygon can be plotted from the geojson file using draw_coordinates.py. This is useful for verifying new townships. I made these myself and took some liberties along rivers and other borders. 

Permit_fee_check.txt is a csv file listing the permit cost of replacing a furnace, an AC (replace or new), and a boiler in various townships. If the permit cost has different conditions from just the township and job type, then "Special Calc" is marked as yes. If the cost of replacing furnace and AC at the same time is separate (i.e. not just the same price as doing one of them), then "Separate" is marked yes. The townships are named to match the geocoding website. When you need to update permit costs, edit this file. 

Address_check_for_permit.py allows you to paste or type in an address directly into the command line. This is useful for going through a list of new HVAC jobs and seeing from the address and job type if the job require a permit with a simple yes or no. The script reads Permit_fee_check.txt.

Customer_data.txt contains information about the customer's contact information. It is used in making a permit cover sheet and the township HVAC permits. It contains:
Customer name
Job address
Phone number
Service Titan job number
Date of installation
Name of Technician
Secondary address (if the customer lives somewhere other than the job location)

Permit_cost.py reads the address from Customer_data.txt so you must fill and save this file before running the script. It will give you the cost of filing a permit for use in filling out other files such as the HVAC permit and permit cover sheet. It may need additional information and will prompt you as needed. It will provide the township, the permit cost, and sometimes extra notes about filing for a particular township. 

Permit_cover_sheet.py fills out the cover sheet from Customer_data.txt and will prompt for additional information such as the fee (from Permit_cost.py) and job (Replace furnace, etc). Online permits such as Buffalo and Amherst do not use this. This sheet gets printed but not saved so the end prompts involve printing and deleting it from the desktop. Please update the desktop location (OUTPUT_DIR = r"\\RPIDCROOT\RedirectedFolders\cef\Desktop") before using this. 

Each HVAC permit pdf has a corresponding script to fill it. They use Customer_data.txt, a signature.png (where relevent), and will prompt for printing and deleting the file so you must also update (OUTPUT_DIR = r"\\RPIDCROOT\RedirectedFolders\cef\Desktop") for this. Amherst does not prompt for printing because it is done online. 