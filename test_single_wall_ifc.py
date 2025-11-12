"""
Simple test to create IFC file with a single wall
"""
import ifcopenshell
import ifcopenshell.guid
import os


def create_single_wall_ifc(output_path="test_single_wall.ifc"):
    """Create a minimal IFC file with one wall for testing"""
    
    # Create IFC file
    ifc_file = ifcopenshell.file()
    
    # Create owner history
    person = ifc_file.createIfcPerson()
    organization = ifc_file.createIfcOrganization()
    person_org = ifc_file.createIfcPersonAndOrganization(person, organization)
    application = ifc_file.createIfcApplication(organization, "1.0", "TestIFC", "TestIFC")
    
    owner_history = ifc_file.createIfcOwnerHistory(
        person_org,
        application,
        None,
        None, None, None, None
    )
    
    # Create project
    project = ifc_file.createIfcProject(
        ifcopenshell.guid.new(),
        owner_history,
        "Test Project",
        None, None, None, None,
        [ifc_file.createIfcGeometricRepresentationContext(
            None, "Model",
            3, 1.0E-5,
            ifc_file.createIfcAxis2Placement3D(
                ifc_file.createIfcCartesianPoint([0.0, 0.0, 0.0]),
                ifc_file.createIfcDirection([0.0, 0.0, 1.0]),
                ifc_file.createIfcDirection([1.0, 0.0, 0.0])
            ),
            None
        )],
        None
    )
    
    # Create site
    site_placement = ifc_file.createIfcLocalPlacement(
        None,
        ifc_file.createIfcAxis2Placement3D(
            ifc_file.createIfcCartesianPoint([0.0, 0.0, 0.0]),
            ifc_file.createIfcDirection([0.0, 0.0, 1.0]),
            ifc_file.createIfcDirection([1.0, 0.0, 0.0])
        )
    )
    
    # IfcSite - exact same pattern as FloorplanToIFC.py
    site = ifc_file.createIfcSite(
        ifcopenshell.guid.new(),  # GlobalId
        owner_history,            # OwnerHistory
        "Site",                    # Name
        None,                     # Description
        None,                     # ObjectType
        None,                     # LongName
        site_placement,           # ObjectPlacement
        None,                     # Representation
        "ELEMENT",                 # CompositionType (after placement)
        None,                     # RefElevation
        None,                     # RefLatitude
        None,                     # RefLongitude
        None                      # LandTitleNumber
    )
    
    # Create building
    building_placement = ifc_file.createIfcLocalPlacement(
        site.ObjectPlacement,
        ifc_file.createIfcAxis2Placement3D(
            ifc_file.createIfcCartesianPoint([0.0, 0.0, 0.0]),
            ifc_file.createIfcDirection([0.0, 0.0, 1.0]),
            ifc_file.createIfcDirection([1.0, 0.0, 0.0])
        )
    )
    
    building = ifc_file.createIfcBuilding(
        ifcopenshell.guid.new(),
        owner_history,
        "Building",
        None, None, None,
        building_placement,
        None, None, None
    )
    
    # Create building storey
    storey_placement = ifc_file.createIfcLocalPlacement(
        building.ObjectPlacement,
        ifc_file.createIfcAxis2Placement3D(
            ifc_file.createIfcCartesianPoint([0.0, 0.0, 0.0]),
            ifc_file.createIfcDirection([0.0, 0.0, 1.0]),
            ifc_file.createIfcDirection([1.0, 0.0, 0.0])
        )
    )
    
    # IfcBuildingStorey has 10 attributes
    storey = ifc_file.createIfcBuildingStorey(
        ifcopenshell.guid.new(),  # 1 GlobalId
        owner_history,            # 2 OwnerHistory
        "Ground Floor",           # 3 Name
        None,                     # 4 Description
        None,                     # 5 ObjectType
        storey_placement,         # 6 ObjectPlacement
        None,                     # 7 Representation
        None,                     # 8 LongName
        None,                     # 9 CompositionType
        0.0                       # 10 Elevation
    )
    
    # Create a simple wall at origin
    # Wall dimensions: 10m long, 3m high, 0.3m thick (larger for visibility)
    wall_length = 10.0  # Length along X axis
    wall_height = 3.0   # Height along Z axis
    wall_thickness = 0.3  # Thickness along Y axis
    
    # Wall placement at origin
    wall_placement = ifc_file.createIfcLocalPlacement(
        storey.ObjectPlacement,
        ifc_file.createIfcAxis2Placement3D(
            ifc_file.createIfcCartesianPoint([0.0, 0.0, 0.0]),
            ifc_file.createIfcDirection([0.0, 0.0, 1.0]),
            ifc_file.createIfcDirection([1.0, 0.0, 0.0])
        )
    )
    
    # Create wall shape - rectangle profile extruded along X axis
    # The profile is in the Y-Z plane (thickness in Y, height in Z)
    # Then extruded along X axis for the length
    
    # Profile: rectangle in Y-Z plane
    profile = ifc_file.createIfcRectangleProfileDef(
        "AREA", None,
        ifc_file.createIfcAxis2Placement2D(
            ifc_file.createIfcCartesianPoint([0.0, 0.0]),
            None  # RefDirection optional
        ),
        wall_thickness,  # X dimension in profile plane (wall thickness)
        wall_height      # Y dimension in profile plane (wall height)
    )
    
    # Position: at origin, Z up, X forward
    position = ifc_file.createIfcAxis2Placement3D(
        ifc_file.createIfcCartesianPoint([0.0, 0.0, 0.0]),
        ifc_file.createIfcDirection([0.0, 0.0, 1.0]),  # Z axis (up)
        ifc_file.createIfcDirection([1.0, 0.0, 0.0])   # X axis (forward)
    )
    
    # Extrusion direction: along X axis (wall length direction)
    extrusion_dir = ifc_file.createIfcDirection([1.0, 0.0, 0.0])
    
    # Create extruded solid
    extruded_solid = ifc_file.createIfcExtrudedAreaSolid(
        profile,
        position,
        extrusion_dir,
        wall_length  # Extrude this distance along X
    )
    
    wall_shape = ifc_file.createIfcShapeRepresentation(
        project.RepresentationContexts[0],
        "Body",
        "SweptSolid",
        [extruded_solid]
    )
    
    # Create wall
    wall = ifc_file.createIfcWallStandardCase(
        ifcopenshell.guid.new(),
        owner_history,
        "Test_Wall",
        None, None,
        wall_placement,
        ifc_file.createIfcProductDefinitionShape(None, None, [wall_shape]),
        None,
        None
    )
    
    # Link wall to storey
    ifc_file.createIfcRelContainedInSpatialStructure(
        ifcopenshell.guid.new(),
        owner_history,
        None, None,
        [wall],
        storey
    )
    
    # Write IFC file
    output_path = os.path.join(os.getcwd(), output_path)
    ifc_file.write(output_path)
    print(f"Created test IFC file with single wall at: {output_path}")
    print(f"Wall dimensions: {wall_length}m long × {wall_height}m high × {wall_thickness}m thick")
    print(f"Wall position: Origin (0, 0, 0)")
    
    return output_path


if __name__ == "__main__":
    create_single_wall_ifc()

