bl_info = {
    "name": "Halo Reach Light Importer",
    "author": "Brooen",
    "version": (1, 0),
    "blender": (4, 1, 1),  # Update to your Blender version
    "location": "View3D > Sidebar > Halo Reach Light Importer",
    "description": "Imports Halo Reach light data into Blender",
    "category": "Import-Export",
}

import bpy
import os
import struct
import math
from bpy.props import StringProperty
from bpy.types import Operator, Panel, AddonPreferences
from mathutils import Matrix, Vector

# Define enums for lighttype, shape, and bungie_light_type
LIGHTTYPE = {0: 'omni', 1: 'spot', 2: 'directional'}
SHAPE = {0: 'rectangle', 1: 'circle'}
BUNGIE_LIGHT_TYPE = {
    0: 'default_lightmap_light',
    1: 'uber_light',
    2: 'inlined_light',
    3: 'screen_space_light',
    4: 'rerender_lights'
}

# Addon Preferences for global settings
class HaloReachLightImporterPreferences(AddonPreferences):
    bl_idname = __name__

    tags_base_directory: StringProperty(
        name="Tags Base Directory",
        subtype='DIR_PATH',
        default=""
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "tags_base_directory")

# Operator to import lights
class IMPORT_OT_halo_reach_lights(Operator):
    bl_idname = "import_scene.halo_reach_lights"
    bl_label = "Import Halo Reach Lights"
    bl_description = "Import Halo Reach lighting data files"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        name="File Path",
        description="Filepath used for importing the lights",
        maxlen=1024,
        subtype='FILE_PATH',
    )
    directory: StringProperty(
        name="Directory",
        description="Directory of the files",
        maxlen=1024,
        subtype='DIR_PATH',
    )
    files: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        for file_elem in self.files:
            filepath = os.path.join(self.directory, file_elem.name)
            read_binary_file(filepath, context)
        return {'FINISHED'}

    def invoke(self, context, event):
        prefs = context.preferences.addons[__name__].preferences
        tags_dir = prefs.tags_base_directory if prefs.tags_base_directory else "//"

        context.window_manager.fileselect_add(self)
        self.directory = bpy.path.abspath(tags_dir)
        self.filter_glob = "*.scenario_structure_lighting_info"
        return {'RUNNING_MODAL'}

# Panel in the 3D Viewport Sidebar
class VIEW3D_PT_halo_reach_light_importer(Panel):
    bl_label = "Halo Reach Light Importer"
    bl_idname = "VIEW3D_PT_halo_reach_light_importer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "HR Lights"

    def draw(self, context):
        layout = self.layout
        layout.operator(IMPORT_OT_halo_reach_lights.bl_idname, text="Import Lights")

# Function to read and import binary files
def read_binary_file(file_path, context):
    with open(file_path, 'rb') as file:
        # 1. Skip 184 bytes
        file.seek(184)
        
        # 2. Read a u32, then skip that many bytes
        skip_size, = struct.unpack('I', file.read(4))
        file.seek(skip_size, 1)
        
        # 3. Skip 8 bytes, read a u32, then skip that many bytes (11 times)
        for _ in range(11):
            file.seek(8, 1)
            skip_size, = struct.unpack('I', file.read(4))
            file.seek(skip_size, 1)

        # Skip 132 bytes after completing the first part
        file.seek(132, 1)

        # Read u32 reference count
        reference_count, = struct.unpack('I', file.read(4))
        print(f"Reference count: {reference_count}")

        # Store references in a list
        references = []

        # Read each reference
        for _ in range(reference_count):
            lighttype, = struct.unpack('I', file.read(4))  # Read lighttype (u32)
            flags, = struct.unpack('I', file.read(4))  # Read flags (u32)
            shape, = struct.unpack('I', file.read(4))  # Read shape (u32)
            color = struct.unpack('fff', file.read(12))  # Read color (3 floats: r, g, b)
            intensity, = struct.unpack('f', file.read(4))  # Read intensity (float)
            hotspot_size, = struct.unpack('f', file.read(4))  # Read hotspot size (float)
            hotspot_cutoff_size, = struct.unpack('f', file.read(4))  # Read hotspot cutoff size (float)
            hotspot_falloff_speed, = struct.unpack('f', file.read(4))  # Read hotspot falloff speed (float)
            near_attenuation_bounds = struct.unpack('ff', file.read(8))  # Read near attenuation bounds (2 floats)
            far_attenuation_bounds = struct.unpack('ff', file.read(8))  # Read far attenuation bounds (2 floats)
            aspect, = struct.unpack('f', file.read(4))  # Read aspect (float)
            clipping_planes = struct.unpack('5I', file.read(20))  # Read clipping planes (5 u32s)

            # Store the parsed reference data
            reference = {
                'lighttype': LIGHTTYPE.get(lighttype, 'unknown'),
                'color': color,
                'intensity': intensity,
            }
            references.append(reference)

            # Print the parsed reference data (optional)
            print(f"Lighttype: {LIGHTTYPE.get(lighttype, 'unknown')}")
            print(f"Flags: {flags}")
            print(f"Shape: {SHAPE.get(shape, 'unknown')}")
            print(f"Color: {color}")
            print(f"Intensity: {intensity}")
            print(f"Hotspot Size: {hotspot_size}")
            print(f"Hotspot Cutoff Size: {hotspot_cutoff_size}")
            print(f"Hotspot Falloff Speed: {hotspot_falloff_speed}")
            print(f"Near Attenuation Bounds: {near_attenuation_bounds}")
            print(f"Far Attenuation Bounds: {far_attenuation_bounds}")
            print(f"Aspect: {aspect}")
            print(f"Clipping Planes: {clipping_planes}")
            print('-' * 40)

        # Skip 16 bytes of padding after references
        file.seek(16, 1)

        # Read u32 instance count
        instance_count, = struct.unpack('I', file.read(4))
        print(f"Instance count: {instance_count}")

        # Skip 4 bytes of padding
        file.seek(4, 1)

        # Create a collection named after the file (minus extension)
        collection_name = os.path.splitext(os.path.basename(file_path))[0]
        collection = bpy.data.collections.new(collection_name)
        context.scene.collection.children.link(collection)

        # Create a dictionary to store light data blocks for each reference index
        light_data_blocks = {}

        # Read each instance block
        for instance_index in range(instance_count):
            definition_index, = struct.unpack('I', file.read(4))  # Read definition_index (u32)
            shader_reference_index, = struct.unpack('I', file.read(4))  # Read shader_reference_index (u32)
            
            origin = struct.unpack('fff', file.read(12))  # Read origin (xyz: 3 floats)
            forward = struct.unpack('fff', file.read(12))  # Read forward (xyz: 3 floats)
            up = struct.unpack('fff', file.read(12))  # Read up (xyz: 3 floats)
            
            bungie_light_type, = struct.unpack('H', file.read(2))  # Read bungie_light_type (u16)
            file.seek(2, 1)  # Skip 2 bytes of padding
            
            screen_space_specular, = struct.unpack('I', file.read(4))  # Read screen_space_specular (u32)
            bounce_light_control, = struct.unpack('f', file.read(4))  # Read bounce_light_control (float)
            light_volume_distance, = struct.unpack('f', file.read(4))  # Read light_volume_distance (float)
            fade_out_distance, = struct.unpack('f', file.read(4))  # Read fade_out_distance (float)
            fade_start_distance, = struct.unpack('f', file.read(4))  # Read fade_start_distance (float)
            
            file.seek(64, 1)  # Skip 64 bytes of padding

            # Get the reference data using definition_index
            reference = references[definition_index]

            # Check if light data for this reference already exists
            if definition_index not in light_data_blocks:
                # Map the lighttype to Blender's light types
                blender_light_type = {
                    'omni': 'POINT',
                    'spot': 'SPOT',
                    'directional': 'SUN'
                }.get(reference['lighttype'], 'POINT')  # Default to POINT if unknown

                # Create the light data block
                light_data = bpy.data.lights.new(name=f"LightData_{definition_index}", type=blender_light_type)
                
                # Set light properties
                light_data.color = reference['color']
                light_data.energy = reference['intensity'] * 10  # Multiply intensity by 10

                # Store the light data block in the dictionary
                light_data_blocks[definition_index] = light_data
            else:
                # Reuse the existing light data block
                light_data = light_data_blocks[definition_index]

            # Create the light object using the shared light data
            light_object = bpy.data.objects.new(name=f"Light_{instance_index}", object_data=light_data)
            collection.objects.link(light_object)

            # Multiply location by 3.048
            scaled_origin = Vector(origin) * 3.048
            light_object.location = scaled_origin

            # Convert tuples to mathutils.Vector and normalize
            forward_vector = Vector(forward).normalized()
            up_vector = Vector(up).normalized()

            # Compute the right vector
            right_vector = forward_vector.cross(up_vector).normalized()

            # Recompute the up vector to ensure orthogonality
            up_vector = right_vector.cross(forward_vector).normalized()

            # Create rotation matrix (3x3)
            rotation_matrix = Matrix((
                right_vector,
                up_vector,
                -forward_vector,  # Adjust for Blender's coordinate system
            )).transposed()

            # Invert Y rotation by rotating 180 degrees around Y-axis (3x3)
            invert_y_rotation = Matrix.Rotation(math.pi, 3, 'Y')  # 180 degrees in radians

            # Rotate -90 degrees around local X-axis (3x3)
            rotate_neg_90_x = Matrix.Rotation(-math.pi / 2, 3, 'X')  # -90 degrees in radians

            # Apply the rotations
            rotation_matrix = rotation_matrix @ invert_y_rotation @ rotate_neg_90_x

            # Convert rotation matrix to 4x4
            rotation_matrix_4x4 = rotation_matrix.to_4x4()

            # Apply rotation and location to the light object
            light_object.matrix_world = Matrix.Translation(scaled_origin) @ rotation_matrix_4x4

            # Print the parsed instance data (optional)
            print(f"Definition Index: {definition_index}")
            print(f"Shader Reference Index: {shader_reference_index}")
            print(f"Origin: {origin}")
            print(f"Forward: {forward}")
            print(f"Up: {up}")
            print(f"Bungie Light Type: {BUNGIE_LIGHT_TYPE.get(bungie_light_type, 'unknown')}")
            print(f"Screen Space Specular: {screen_space_specular}")
            print(f"Bounce Light Control: {bounce_light_control}")
            print(f"Light Volume Distance: {light_volume_distance}")
            print(f"Fade Out Distance: {fade_out_distance}")
            print(f"Fade Start Distance: {fade_start_distance}")
            print('-' * 40)

# Registration
classes = (
    HaloReachLightImporterPreferences,
    IMPORT_OT_halo_reach_lights,
    VIEW3D_PT_halo_reach_light_importer,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    print("Halo Reach Light Importer registered")

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("Halo Reach Light Importer unregistered")

if __name__ == "__main__":
    register()
