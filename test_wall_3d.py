"""
Test to create a clearly visible 3D wall
"""
import ifcopenshell
import ifcopenshell.guid
import os


def create_visible_wall_ifc(output_path="test_wall_3d.ifc"):
    """Create IFC with a large, clearly visible wall"""
    
    ifc_file = ifcopenshell.file()
    
    # Owner history
    person = ifc_file.createIfcPerson()
    organization = ifc_file.createIfcOrganization()
    person_org = ifc_file.createIfcPersonAndOrganization(person, organization)
    application = ifc_file.createIfcApplication(organization, "1.0", "TestIFC", "TestIFC")
    owner_history = ifc_file.createIfcOwnerHistory(person_org, application, None, None, None, None, None)
    
    # Project
    project = ifc_file.createIfcProject(
        ifcopenshell.guid.new(),
        owner_history,
        "Test Project",
        None, None, None, None,
        [ifc_file.createIfcGeometricRepresentationContext(
            None, "Model", 3, 1.0E-5,
            ifc_file.createIfcAxis2Placement3D(
                ifc_file.createIfcCartesianPoint([0.0, 0.0, 0.0]),
                ifc_file.createIfcDirection([0.0, 0.0, 1.0]),
                ifc_file.createIfcDirection([1.0, 0.0, 0.0])
            ),
            None
        )],
        None
    )
    
    # Site
    site_placement = ifc_file.createIfcLocalPlacement(
        None,
        ifc_file.createIfcAxis2Placement3D(
            ifc_file.createIfcCartesianPoint([0.0, 0.0, 0.0]),
            ifc_file.createIfcDirection([0.0, 0.0, 1.0]),
            ifc_file.createIfcDirection([1.0, 0.0, 0.0])
        )
    )
    
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
    
    # Building
    building_placement = ifc_file.createIfcLocalPlacement(
        site.ObjectPlacement,
        ifc_file.createIfcAxis2Placement3D(
            ifc_file.createIfcCartesianPoint([0.0, 0.0, 0.0]),
            ifc_file.createIfcDirection([0.0, 0.0, 1.0]),
            ifc_file.createIfcDirection([1.0, 0.0, 0.0])
        )
    )
    
    building = ifc_file.createIfcBuilding(
        ifcopenshell.guid.new(), owner_history, "Building",
        None, None, None, building_placement, None, None, None
    )
    
    # Storey
    storey_placement = ifc_file.createIfcLocalPlacement(
        building.ObjectPlacement,
        ifc_file.createIfcAxis2Placement3D(
            ifc_file.createIfcCartesianPoint([0.0, 0.0, 0.0]),
            ifc_file.createIfcDirection([0.0, 0.0, 1.0]),
            ifc_file.createIfcDirection([1.0, 0.0, 0.0])
        )
    )
    
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
    
    # Create wall: 10m × 3m × 0.3m
    # Profile is in Y-Z plane (thickness × height)
    # Extrude along X axis (length)
    
    wall_placement = ifc_file.createIfcLocalPlacement(
        storey.ObjectPlacement,
        ifc_file.createIfcAxis2Placement3D(
            ifc_file.createIfcCartesianPoint([0.0, 0.0, 0.0]),
            ifc_file.createIfcDirection([0.0, 0.0, 1.0]),
            ifc_file.createIfcDirection([1.0, 0.0, 0.0])
        )
    )
    
    # Use standard orientation: profile in X-Y plane, extrude along Z
    # Profile XDim → X (global), Profile YDim → Y (global)
    # Extrude along Z → Z (global)
    # So: 10m (XDim) × 0.3m (YDim) profile, extrude 3m (Z) = 10m × 0.3m × 3m wall
    
    profile = ifc_file.createIfcRectangleProfileDef(
        "AREA", None,
        ifc_file.createIfcAxis2Placement2D(
            ifc_file.createIfcCartesianPoint([0.0, 0.0]),
            None
        ),
        10.0,  # XDim: wall length (X direction)
        0.3    # YDim: wall thickness (Y direction)
    )
    
    # Standard position: profile in X-Y plane
    # Axis = Z (up), RefDirection = X (forward)
    # Profile X → X, Profile Y → Y
    position = ifc_file.createIfcAxis2Placement3D(
        ifc_file.createIfcCartesianPoint([0.0, 0.0, 0.0]),
        ifc_file.createIfcDirection([0.0, 0.0, 1.0]),  # Axis = Z up
        ifc_file.createIfcDirection([1.0, 0.0, 0.0])    # RefDirection = X forward
    )
    
    # Extrude along Z for 3m (wall height)
    extruded = ifc_file.createIfcExtrudedAreaSolid(
        profile,
        position,
        ifc_file.createIfcDirection([0.0, 0.0, 1.0]),  # Extrude along Z (up)
        3.0  # 3 meters height
    )
    
    shape_repr = ifc_file.createIfcShapeRepresentation(
        project.RepresentationContexts[0],
        "Body",
        "SweptSolid",
        [extruded]
    )
    
    wall = ifc_file.createIfcWallStandardCase(
        ifcopenshell.guid.new(),
        owner_history,
        "Test_Wall_3D",
        None, None,
        wall_placement,
        ifc_file.createIfcProductDefinitionShape(None, None, [shape_repr]),
        None,
        None
    )
    
    # Link to storey
    ifc_file.createIfcRelContainedInSpatialStructure(
        ifcopenshell.guid.new(),
        owner_history,
        None, None,
        [wall],
        storey
    )
    
    output_path = os.path.join(os.getcwd(), output_path)
    ifc_file.write(output_path)
    print(f"Created 3D wall test file: {output_path}")
    print("Wall: 10m (X) × 3m (Z) × 0.3m (Y) at origin")
    return output_path


if __name__ == "__main__":
    create_visible_wall_ifc()

