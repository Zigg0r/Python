bl_info = {
    "name": "Utilities",
    "author": "Ziggor",
    "version": (1, 6),
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > Utilities Tab",
    "description": "Various tools for working with Blender scenes",
    "category": "3D View"
}

import bpy
import bmesh
import ctypes
import sys
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import FloatProperty, PointerProperty
from mathutils import Vector


# ------------------------------------------------------------------------
#   Console utility
# ------------------------------------------------------------------------

def open_console_if_needed():
    if sys.platform == "win32":
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if not hwnd:
            ctypes.windll.kernel32.AllocConsole()


# ------------------------------------------------------------------------
#   Operators
# ------------------------------------------------------------------------

class UTILITIES_OT_open_preferences(Operator):
    bl_idname = "utilities.open_preferences"
    bl_label = "Open Preferences"

    def execute(self, context):
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        return {'FINISHED'}


class UTILITIES_OT_toggle_console(Operator):
    bl_idname = "utilities.toggle_console"
    bl_label = "Toggle Console"

    def execute(self, context):
        if sys.platform == "win32":
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                visible = ctypes.windll.user32.IsWindowVisible(hwnd)
                ctypes.windll.user32.ShowWindow(hwnd, 0 if visible else 1)
                self.report({'INFO'}, "Toggled Console")
            else:
                ctypes.windll.kernel32.AllocConsole()
                self.report({'INFO'}, "Console Allocated")
        else:
            self.report({'WARNING'}, "Only supported on Windows")
        return {'FINISHED'}


class UTILITIES_OT_count_elements(Operator):
    bl_idname = "utilities.count_elements"
    bl_label = "Count Elements"

    mode: bpy.props.EnumProperty(
        items=[
            ('VERT', "Vertex", ""),
            ('EDGE', "Edge", ""),
            ('FACE', "Face", "")
        ]
    )

    def execute(self, context):
        open_console_if_needed()

        data_key = {
            'VERT': 'vertices',
            'EDGE': 'edges',
            'FACE': 'polygons'
        }[self.mode]

        results = []
        for obj in context.scene.objects:
            if obj.type == 'MESH':
                eval_obj = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
                mesh = eval_obj.to_mesh()
                count = len(getattr(mesh, data_key))
                results.append((obj.name, count))
                eval_obj.to_mesh_clear()

        results.sort(key=lambda x: x[1], reverse=True)
        print(f"\n--- {self.mode} Count ---")
        for name, count in results:
            print(f"{name}: {count}")
        return {'FINISHED'}


class UTILITIES_OT_toggle_wireframe(Operator):
    bl_idname = "utilities.toggle_wireframe"
    bl_label = "Wireframe Visibility"

    def execute(self, context):
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.overlay.show_wireframes = not space.overlay.show_wireframes
        return {'FINISHED'}


class UTILITIES_OT_toggle_face_orientation(Operator):
    bl_idname = "utilities.toggle_face_orientation"
    bl_label = "Face Orientation"

    def execute(self, context):
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.overlay.show_face_orientation = not space.overlay.show_face_orientation
        return {'FINISHED'}


class UTILITIES_OT_shade(Operator):
    bl_idname = "utilities.shade"
    bl_label = "Shade Object"

    mode: bpy.props.EnumProperty(
        items=[
            ('FLAT', "Flat", ""),
            ('SMOOTH', "Smooth", ""),
            ('AUTO', "Auto", "")
        ]
    )

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                context.view_layer.objects.active = obj
                if self.mode == 'FLAT':
                    bpy.ops.object.shade_flat()
                elif self.mode == 'SMOOTH':
                    bpy.ops.object.shade_smooth()
                elif self.mode == 'AUTO':
                    bpy.ops.object.shade_auto_smooth()
        return {'FINISHED'}


class UTILITIES_OT_select_non_manifold(Operator):
    bl_idname = "utilities.select_non_manifold"
    bl_label = "Non-Manifold"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_non_manifold()
        return {'FINISHED'}


class UTILITIES_OT_select_near_vertices(Operator):
    bl_idname = "utilities.select_near_vertices"
    bl_label = "Select"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH' and bpy.context.tool_settings.mesh_select_mode[0]

    def execute(self, context):
        dist = context.scene.utilities_settings.selection_distance
        obj = context.active_object

        if obj and obj.type == 'MESH':
            bm = bmesh.from_edit_mesh(obj.data)
            bm.verts.ensure_lookup_table()

            selected_positions = [v.co.copy() for v in bm.verts if v.select]
            for v in bm.verts:
                if any((v.co - pos).length <= dist for pos in selected_positions):
                    v.select_set(True)

            bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}


# ------------------------------------------------------------------------
#   Property Group
# ------------------------------------------------------------------------

class UtilitiesSettings(PropertyGroup):
    selection_distance: FloatProperty(
        name="Distance",
        description="Distance in meters for vertex selection",
        default=0.01,
        min=0.0,
        unit='LENGTH'
    )


# ------------------------------------------------------------------------
#   UI Panel
# ------------------------------------------------------------------------

class UTILITIES_PT_main_panel(Panel):
    bl_label = "Utilities"
    bl_idname = "UTILITIES_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "DefaultCube"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.utilities_settings
        mode = context.mode
        is_vert_mode = bpy.context.tool_settings.mesh_select_mode[0]

        layout.operator("utilities.open_preferences", icon='PREFERENCES')
        layout.operator("utilities.toggle_console", icon='CONSOLE')

        row = layout.row()
        row.alignment = 'CENTER'
        row.label(text="Count Amount Scene")
        row = layout.row(align=True)
        row.operator("utilities.count_elements", text="Vertex", icon='VERTEXSEL').mode = 'VERT'
        row.operator("utilities.count_elements", text="Edge", icon='EDGESEL').mode = 'EDGE'
        row.operator("utilities.count_elements", text="Face", icon='FACESEL').mode = 'FACE'

        layout.operator("utilities.toggle_wireframe", icon='SHADING_WIRE')
        layout.operator("utilities.toggle_face_orientation", icon='ORIENTATION_NORMAL')

        row = layout.row()
        row.alignment = 'CENTER'
        row.label(text="Change Object Shading")
        row = layout.row(align=True)
        row.operator("utilities.shade", text="Flat", icon='MATERIAL').mode = 'FLAT'
        row.operator("utilities.shade", text="Smooth", icon='NODE_MATERIAL').mode = 'SMOOTH'
        row.operator("utilities.shade", text="Auto", icon='MATSPHERE').mode = 'AUTO'

        row = layout.row()
        row.enabled = (mode == 'EDIT_MESH')
        row.operator("utilities.select_non_manifold", icon='MOD_EDGESPLIT')

        row = layout.row()
        row.alignment = 'CENTER'
        row.label(text="Select Nearby Vertices")
        row = layout.row(align=True)
        row.prop(settings, "selection_distance", text="Range")
        row.enabled = (mode == 'EDIT_MESH' and is_vert_mode)
        row.operator("utilities.select_near_vertices", icon='POINTCLOUD_DATA')


# ------------------------------------------------------------------------
#   Registration
# ------------------------------------------------------------------------

classes = (
    UTILITIES_OT_open_preferences,
    UTILITIES_OT_toggle_console,
    UTILITIES_OT_count_elements,
    UTILITIES_OT_toggle_wireframe,
    UTILITIES_OT_toggle_face_orientation,
    UTILITIES_OT_shade,
    UTILITIES_OT_select_non_manifold,
    UTILITIES_OT_select_near_vertices,
    UtilitiesSettings,
    UTILITIES_PT_main_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.utilities_settings = PointerProperty(type=UtilitiesSettings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.utilities_settings

if __name__ == "__main__":
    register()
