from utils.FloorplanToBlenderLib import *
import os
import config
import json
import ifcopenshell
import ifcopenshell.geom
from ifcopenshell.util.placement import get_local_placement
import numpy as np


def createIFC(data_path, target_path):
    """
    Create IFC file from generated geometry data
    @Param data_path: Path to data directory (e.g., "Data/0/")
    @Param target_path: Output IFC file path (without extension)
    """
    # Read geometry data
    def read_from_file(file_path):
        with open(file_path + '.txt', 'r') as f:
            return json.loads(f.read())
    
    # Read transform
    transform = read_from_file(data_path + "transform")
    position = transform.get("position", [0, 0, 0])
    rotation = transform.get("rotation", [0, 0, 0])
    shape = transform.get("shape", [0, 0, 0])
    
    # Create IFC file
    ifc_file = ifcopenshell.file()
    
    # Create owner history (simplified)
    person = ifc_file.createIfcPerson()
    organization = ifc_file.createIfcOrganization()
    person_org = ifc_file.createIfcPersonAndOrganization(person, organization)
    application = ifc_file.createIfcApplication(organization, "1.0", "FloorplanToIFC", "FloorplanToIFC")
    
    owner_history = ifc_file.createIfcOwnerHistory(
        person_org,
        application,
        None,  # ChangeAction - None means no change tracking
        None, None, None, None
    )
    
    # Create geometric representation contexts
    # Main Model context
    model_context = ifc_file.createIfcGeometricRepresentationContext(
        None, "Model", 3, 1.0E-5,
        ifc_file.createIfcAxis2Placement3D(
            ifc_file.createIfcCartesianPoint([0.0, 0.0, 0.0]),
            ifc_file.createIfcDirection([0.0, 0.0, 1.0]),
            ifc_file.createIfcDirection([1.0, 0.0, 0.0])
        ),
        None
    )
    
    # Body subcontext (required by web viewers)
    body_context = ifc_file.createIfcGeometricRepresentationSubContext(
        "Body", "Model", None, None, None, None,
        model_context,
        None,
        "MODEL_VIEW",
        None
    )
    
    # Axis subcontext (required by web viewers)
    axis_context = ifc_file.createIfcGeometricRepresentationSubContext(
        "Axis", "Model", None, None, None, None,
        model_context,
        None,
        "GRAPH_VIEW",
        None
    )
    
    # Create project with all contexts
    project = ifc_file.createIfcProject(
        ifcopenshell.guid.new(),
        owner_history,
        "Floorplan Project",
        None, None, None, None,
        [model_context, body_context, axis_context],
        None
    )
    
    # CRITICAL: Assign units (meters) - required by web viewers
    # Create length unit (meters)
    length_unit = ifc_file.createIfcSIUnit(None, "LENGTHUNIT", None, "METRE")
    
    # Create area unit (square meters)
    area_unit = ifc_file.createIfcSIUnit(None, "AREAUNIT", None, "SQUARE_METRE")
    
    # Create volume unit (cubic meters)
    volume_unit = ifc_file.createIfcSIUnit(None, "VOLUMEUNIT", None, "CUBIC_METRE")
    
    # Create unit assignment
    unit_assignment = ifc_file.createIfcUnitAssignment([
        length_unit,
        area_unit,
        volume_unit
    ])
    
    # Assign units to project
    project.UnitsInContext = unit_assignment
    
    # Create site
    site_placement = ifc_file.createIfcLocalPlacement(
        None,  # Parent placement (None = global)
            ifc_file.createIfcAxis2Placement3D(
                ifc_file.createIfcCartesianPoint([0.0, 0.0, 0.0]),
                ifc_file.createIfcDirection([0.0, 0.0, 1.0]),
                ifc_file.createIfcDirection([1.0, 0.0, 0.0])
            )
    )
    
    # Create site - try correct parameter order
    # Standard IfcProduct parameters first, then IfcSite specific
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
    
    # CRITICAL: Add spatial hierarchy relationships (IFCRELAGGREGATES)
    # These link Project → Site → Building → BuildingStorey
    # Without these, IFC viewers can't traverse the hierarchy and see nothing!
    
    # Project aggregates Site
    ifc_file.createIfcRelAggregates(
        ifcopenshell.guid.new(),
        owner_history,
        None, None,
        project,
        [site]
    )
    
    # Site aggregates Building
    ifc_file.createIfcRelAggregates(
        ifcopenshell.guid.new(),
        owner_history,
        None, None,
        site,
        [building]
    )
    
    # Building aggregates BuildingStorey
    ifc_file.createIfcRelAggregates(
        ifcopenshell.guid.new(),
        owner_history,
        None, None,
        building,
        [storey]
    )
    
    # Collect all elements to link to storey
    all_elements = []
    
    # Read wall data
    try:
        wall_verts = read_from_file(data_path + "wall_verts")
        wall_faces = read_from_file(data_path + "wall_faces")
        
        # Create walls
        for wall_idx, wall_segments in enumerate(wall_verts):
            for segment_idx, segment in enumerate(wall_segments):
                if len(segment) >= 4:
                    # Extract points from segment (4 vertices per wall face)
                    points = []
                    for vert in segment:
                        if isinstance(vert, list) and len(vert) >= 3:
                            # Apply position offset
                            points.append([
                                vert[0] + position[0],
                                vert[1] + position[1],
                                vert[2] + position[2]
                            ])
                    
                    if len(points) >= 4:
                        # Calculate wall direction for proper orientation
                        p_bottom_start = points[0]
                        p_bottom_end = points[2]
                        wall_dir_x = p_bottom_end[0] - p_bottom_start[0]
                        wall_dir_y = p_bottom_end[1] - p_bottom_start[1]
                        dir_length_xy = np.sqrt(wall_dir_x**2 + wall_dir_y**2)
                        
                        if dir_length_xy > 0.001:
                            wall_dir_x /= dir_length_xy
                            wall_dir_y /= dir_length_xy
                        else:
                            wall_dir_x, wall_dir_y = 1.0, 0.0
                        
                        # Create wall placement with rotation to match wall direction
                        # The RefDirection should point along the wall length direction
                        wall_placement = ifc_file.createIfcLocalPlacement(
                            storey.ObjectPlacement,
                            ifc_file.createIfcAxis2Placement3D(
                                ifc_file.createIfcCartesianPoint([float(points[0][0]), float(points[0][1]), float(points[0][2])]),
                                ifc_file.createIfcDirection([0.0, 0.0, 1.0]),  # Z up
                                ifc_file.createIfcDirection([float(wall_dir_x), float(wall_dir_y), 0.0])  # Wall direction
                            )
                        )
                        
                        # Create wall using IfcWallStandardCase
                        wall = ifc_file.createIfcWallStandardCase(
                            ifcopenshell.guid.new(),
                            owner_history,
                            f"Wall_{wall_idx}_{segment_idx}",
                            None, None,
                            wall_placement,
                            None,
                            None
                        )
                        
                        # Create shape representation for wall (use Body context for web viewers)
                        wall_shape = create_wall_shape(ifc_file, points, body_context)
                        if wall_shape:
                            wall.Representation = ifc_file.createIfcProductDefinitionShape(
                                None, None, [wall_shape]
                            )
                        else:
                            print(f"Warning: Failed to create shape for Wall_{wall_idx}_{segment_idx}")
                            continue  # Skip this wall if shape creation failed
                        
                        all_elements.append(wall)
    except Exception as e:
        print(f"Warning: Could not create walls: {e}")
    
    # Get Body context for web viewers (defined once, used for all shapes)
    body_context = [ctx for ctx in project.RepresentationContexts if hasattr(ctx, 'ContextIdentifier') and ctx.ContextIdentifier == "Body"][0]
    
    # Read floor data
    try:
        floor_verts = read_from_file(data_path + "floor_verts")
        floor_faces = read_from_file(data_path + "floor_faces")
        
        # Create floor slab
        if floor_verts:
            # Flatten floor vertices
            floor_points = []
            for vert in floor_verts:
                if isinstance(vert, list) and len(vert) >= 3:
                    floor_points.append([
                        vert[0] + position[0],
                        vert[1] + position[1],
                        vert[2] + position[2]
                    ])
            
            if floor_points:
                slab_placement = ifc_file.createIfcLocalPlacement(
                    storey.ObjectPlacement,
            ifc_file.createIfcAxis2Placement3D(
                ifc_file.createIfcCartesianPoint([0.0, 0.0, 0.0]),
                ifc_file.createIfcDirection([0.0, 0.0, 1.0]),
                ifc_file.createIfcDirection([1.0, 0.0, 0.0])
            )
                )
                
                slab = ifc_file.createIfcSlab(
                    ifcopenshell.guid.new(),
                    owner_history,
                    "Floor",
                    None, None,
                    slab_placement,
                    None,
                    "FLOOR"
                )
                
                # Create floor shape (use Body context for web viewers)
                floor_shape = create_floor_shape(ifc_file, floor_points, body_context)
                if floor_shape:
                    slab.Representation = ifc_file.createIfcProductDefinitionShape(
                        None, None, [floor_shape]
                    )
                
                all_elements.append(slab)
    except Exception as e:
        print(f"Warning: Could not create floor: {e}")
    
    # Read room data
    try:
        rooms_verts = read_from_file(data_path + "rooms_verts")
        rooms_faces = read_from_file(data_path + "rooms_faces")
        
        # Create spaces (rooms)
        for room_idx, room_verts in enumerate(rooms_verts):
            if room_verts:
                # Extract room boundary points
                room_points = []
                for vert in room_verts:
                    if isinstance(vert, list) and len(vert) >= 3:
                        room_points.append([
                            vert[0] + position[0],
                            vert[1] + position[1],
                            vert[2] + position[2]
                        ])
                
                if room_points:
                    space_placement = ifc_file.createIfcLocalPlacement(
                        storey.ObjectPlacement,
                        ifc_file.createIfcAxis2Placement3D(
                            ifc_file.createIfcCartesianPoint([float(room_points[0][0]), float(room_points[0][1]), float(room_points[0][2])]),
                            ifc_file.createIfcDirection([0.0, 0.0, 1.0]),
                            ifc_file.createIfcDirection([1.0, 0.0, 0.0])
                        )
                    )
                    
                    # IfcSpace has 11 attributes - PredefinedType enum: INTERNAL, EXTERNAL, or None
                    space = ifc_file.createIfcSpace(
                        ifcopenshell.guid.new(),  # 1 GlobalId
                        owner_history,            # 2 OwnerHistory
                        f"Room_{room_idx}",       # 3 Name
                        None,                     # 4 Description
                        None,                     # 5 ObjectType
                        space_placement,          # 6 ObjectPlacement
                        None,                     # 7 Representation
                        None,                     # 8 LongName
                        None,                     # 9 PredefinedType (None instead of "INTERNAL")
                        None,                     # 10 ElevationOfRefHeight
                        None                      # 11 ElevationOfTerrain
                    )
                    
                    # Create space shape
                    space_shape = create_space_shape(ifc_file, room_points, body_context)
                    if space_shape:
                        space.Representation = ifc_file.createIfcProductDefinitionShape(
                            None, None, [space_shape]
                        )
                    
                    all_elements.append(space)
    except Exception as e:
        print(f"Warning: Could not create rooms: {e}")
    
    # Link all elements to storey
    if all_elements:
        ifc_file.createIfcRelContainedInSpatialStructure(
            ifcopenshell.guid.new(),
            owner_history,
            None, None,
            all_elements,
            storey
        )
    
    # Write IFC file - always use project directory
    # Remove leading slash if present and create in current directory
    clean_path = target_path.lstrip('/')
    if not clean_path:
        clean_path = "floorplan"
    output_path = os.path.join(os.getcwd(), clean_path + ".ifc")
    
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    ifc_file.write(output_path)
    print(f"Created IFC file at {output_path}")


def create_wall_shape(ifc_file, points, context):
    """Create shape representation for a wall segment"""
    if len(points) < 4:
        return None
    
    try:
        # Points format: [bottom_left, top_left, bottom_right, top_right]
        p_bottom_start = points[0]  # Bottom left
        p_bottom_end = points[2]    # Bottom right
        p_top_start = points[1]     # Top left
        
        # Calculate wall length (distance between bottom corners)
        length = np.sqrt((p_bottom_end[0] - p_bottom_start[0])**2 + 
                        (p_bottom_end[1] - p_bottom_start[1])**2 + 
                        (p_bottom_end[2] - p_bottom_start[2])**2)
        
        # Calculate wall height (difference in Z between bottom and top)
        height = abs(p_top_start[2] - p_bottom_start[2]) if abs(p_top_start[2] - p_bottom_start[2]) > 0.01 else 1.0
        
        width = 0.3  # Default wall thickness (increased for better visibility)
        
        # Calculate wall direction in XY plane (for orientation)
        wall_dir_x = p_bottom_end[0] - p_bottom_start[0]
        wall_dir_y = p_bottom_end[1] - p_bottom_start[1]
        dir_length_xy = np.sqrt(wall_dir_x**2 + wall_dir_y**2)
        
        if dir_length_xy > 0.001:
            # Normalize XY direction
            wall_dir_x /= dir_length_xy
            wall_dir_y /= dir_length_xy
        else:
            wall_dir_x, wall_dir_y = 1.0, 0.0
        
        # Create wall using standard orientation: profile in X-Y plane, extrude along Z
        # Profile: length × thickness in X-Y plane
        # Then we'll rotate it to match wall direction using placement
        
        profile = ifc_file.createIfcRectangleProfileDef(
            "AREA", None,
            ifc_file.createIfcAxis2Placement2D(
                ifc_file.createIfcCartesianPoint([0.0, 0.0]),
                None
            ),
            length,  # XDim: wall length
            width    # YDim: wall thickness
        )
        
        # Position: profile in X-Y plane
        # Standard orientation: Axis = Z (up), RefDirection = X (forward)
        # Profile XDim → X, Profile YDim → Y, then extrude along Z
        # The wall placement will handle the rotation/positioning
        position = ifc_file.createIfcAxis2Placement3D(
            ifc_file.createIfcCartesianPoint([0.0, 0.0, 0.0]),
            ifc_file.createIfcDirection([0.0, 0.0, 1.0]),  # Z up
            ifc_file.createIfcDirection([1.0, 0.0, 0.0])   # X forward (standard)
        )
        
        # Extrude along Z for wall height
        swept_solid = ifc_file.createIfcExtrudedAreaSolid(
            profile,
            position,
            ifc_file.createIfcDirection([0.0, 0.0, 1.0]),  # Extrude along Z
            height  # Extrusion depth = wall height
        )
        
        return ifc_file.createIfcShapeRepresentation(
            context,
            "Body",
            "SweptSolid",
            [swept_solid]
        )
    except Exception as e:
        print(f"Warning: Could not create wall shape: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_floor_shape(ifc_file, points, context):
    """Create shape representation for floor"""
    if len(points) < 3:
        return None
    
    try:
        # Get bounding box
        bbox = get_bounding_box(points)
        width = bbox[1][0] - bbox[0][0]
        depth = bbox[1][1] - bbox[0][1]
        min_z = bbox[0][2]
        height = 0.1  # Thin floor slab
        
        # Create extruded area solid (rectangle profile)
        swept_solid = ifc_file.createIfcExtrudedAreaSolid(
            ifc_file.createIfcRectangleProfileDef(
                "AREA", None,
                ifc_file.createIfcAxis2Placement2D(
                    ifc_file.createIfcCartesianPoint([0.0, 0.0]),
                    None  # RefDirection (optional)
                ),
                width,
                depth
            ),
            ifc_file.createIfcAxis2Placement3D(
                ifc_file.createIfcCartesianPoint([float(bbox[0][0]), float(bbox[0][1]), float(min_z)]),
                ifc_file.createIfcDirection([0.0, 0.0, 1.0]),
                ifc_file.createIfcDirection([1.0, 0.0, 0.0])
            ),
            ifc_file.createIfcDirection([0.0, 0.0, 1.0]),
            height
        )
        
        return ifc_file.createIfcShapeRepresentation(
            context,
            "Body",
            "SweptSolid",
            [swept_solid]
        )
    except Exception as e:
        print(f"Warning: Could not create floor shape: {e}")
        return None


def create_space_shape(ifc_file, points, context):
    """Create shape representation for a space (room)"""
    if len(points) < 3:
        return None
    
    try:
        # Create a simple box representation for the space
        bbox = get_bounding_box(points)
        width = bbox[1][0] - bbox[0][0]
        depth = bbox[1][1] - bbox[0][1]
        min_z = bbox[0][2]
        height = 2.5  # Default ceiling height
        
        swept_solid = ifc_file.createIfcExtrudedAreaSolid(
            ifc_file.createIfcRectangleProfileDef(
                "AREA", None,
                ifc_file.createIfcAxis2Placement2D(
                    ifc_file.createIfcCartesianPoint([0.0, 0.0]),
                    None  # RefDirection (optional)
                ),
                width,
                depth
            ),
            ifc_file.createIfcAxis2Placement3D(
                ifc_file.createIfcCartesianPoint([float(bbox[0][0]), float(bbox[0][1]), float(min_z)]),
                ifc_file.createIfcDirection([0.0, 0.0, 1.0]),
                ifc_file.createIfcDirection([1.0, 0.0, 0.0])
            ),
            ifc_file.createIfcDirection([0.0, 0.0, 1.0]),
            height
        )
        
        return ifc_file.createIfcShapeRepresentation(
            context,
            "Body",
            "SweptSolid",
            [swept_solid]
        )
    except Exception as e:
        print(f"Warning: Could not create space shape: {e}")
        return None


def get_bounding_box(points):
    """Calculate bounding box of points"""
    if not points:
        return [[0, 0, 0], [1, 1, 1]]
    
    min_coords = [float('inf'), float('inf'), float('inf')]
    max_coords = [float('-inf'), float('-inf'), float('-inf')]
    
    for p in points:
        if len(p) >= 3:
            min_coords[0] = min(min_coords[0], p[0])
            min_coords[1] = min(min_coords[1], p[1])
            min_coords[2] = min(min_coords[2], p[2])
            max_coords[0] = max(max_coords[0], p[0])
            max_coords[1] = max(max_coords[1], p[1])
            max_coords[2] = max(max_coords[2], p[2])
    
    return [min_coords, max_coords]


def createFloorPlanIFC(image_path=config.image_path, target_path=config.target_path, SR_Check=True):
    """
    Main function to create IFC file from floorplan image
    @Param image_path: Path to input floorplan image
    @Param target_path: Output IFC file path (without extension)
    @Param SR_Check: Whether to use super-resolution
    """
    SR = [config.SR_scale, config.SR_method]
    CubiCasa = config.CubiCasa
    
    # Generate geometry data files
    data_path = execution.simple_single(image_path, CubiCasa, SR)
    
    # Create IFC file from data
    createIFC(data_path, target_path)
    
    print(f"Created IFC file at {target_path}.ifc")

