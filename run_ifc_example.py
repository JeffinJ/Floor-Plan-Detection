"""
Example script to create IFC file from floorplan image
This creates a web-viewer-ready IFC file with units and subcontexts
"""
import FloorplanToIFC as ifc
import config

# Create web-viewer-ready IFC file
# The createFloorPlanIFC function now includes:
# - Unit assignment (meters)
# - Body and Axis subcontexts
# - Complete spatial hierarchy
ifc.createFloorPlanIFC(
    image_path=config.image_path,
    target_path=config.target_path,  # Creates: floorplan.ifc
    SR_Check=True
)

print("\n✅ IFC file created with web viewer compatibility!")
print("   - Units assigned (meters)")
print("   - Body and Axis subcontexts")
print("   - Complete spatial hierarchy")

# Option 2: Use custom paths
# ifc.createFloorPlanIFC(
#     image_path='Images/my_floorplan.png',  # Your image path
#     target_path='/my_floorplan',            # Output will be: my_floorplan.ifc
#     SR_Check=True                           # Use super-resolution (recommended)
# )

