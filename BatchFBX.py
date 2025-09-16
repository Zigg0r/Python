bl_info = {
    "name": "BatchFBX",
    "author": "Ziggor",
    "version": (1, 0),
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > BatchFBX",
    "description": "Export selected meshes as separate FBX files",
    "category": "Import-Export",
}

import bpy
import os
from bpy.props import (
    StringProperty, BoolProperty, EnumProperty,
    FloatProperty, CollectionProperty
)
from bpy.types import Operator, Panel, PropertyGroup


# ----------------------------
# Property Storage
# ----------------------------
class BatchFBXProperties(PropertyGroup):
    export_path: StringProperty(
        name="Export Path",
        description="Choose export directory",
        subtype='DIR_PATH'
    )

    export_mode: EnumProperty(
        name="Export Mode",
        description="Choose FBX export preset",
        items=[
            ('VRCHAT', "VRChat", "Export using VRChat preset"),
            ('DEFAULT', "Default", "Export using Blender's default FBX settings")
        ],
        default='VRCHAT'
    )

    progress: FloatProperty(
        name="Progress",
        description="Current export progress",
        default=0.0,
        min=0.0,
        max=1.0
    )

    show_recent: BoolProperty(
        name="Show Recent",
        description="Show recently exported object names",
        default=False
    )

    recent_names: CollectionProperty(type=bpy.types.PropertyGroup)


# ----------------------------
# Operators
# ----------------------------
class BATCHFBX_OT_SetPath(Operator):
    bl_idname = "batchfbx.set_path"
    bl_label = "Set Export Path"
    bl_description = "Choose export directory"

    directory: StringProperty(subtype='DIR_PATH')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        context.scene.batchfbx_props.export_path = self.directory
        return {'FINISHED'}


class BATCHFBX_OT_ToggleMode(Operator):
    bl_idname = "batchfbx.toggle_mode"
    bl_label = "Toggle Export Mode"

    mode: StringProperty()

    def execute(self, context):
        context.scene.batchfbx_props.export_mode = self.mode
        return {'FINISHED'}


class BATCHFBX_OT_Export(Operator):
    bl_idname = "batchfbx.export"
    bl_label = "Export FBX"
    bl_description = "Export selected meshes to individual FBX files"

    def execute(self, context):
        props = context.scene.batchfbx_props
        path = props.export_path
        selected = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not path or not selected:
            self.report({'ERROR'}, "Set a path and select at least one mesh")
            return {'CANCELLED'}

        props.recent_names.clear()
        props.show_recent = False

        context.window.cursor_set("WAIT")
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        total = len(selected)
        for i, obj in enumerate(selected):
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj

            export_file = os.path.join(path, f"{obj.name}.fbx")

            if props.export_mode == 'VRCHAT':
                bpy.ops.export_scene.fbx(
                    filepath=export_file,
                    use_selection=True,
                    object_types={'MESH'},
                    apply_scale_options='FBX_SCALE_UNITS',
                    add_leaf_bones=False,
                    bake_anim_use_all_bones=False,
                    bake_anim_use_nla_strips=False,
                    bake_anim_use_all_actions=False,
                    use_custom_props=False,
                    mesh_smooth_type='OFF'
                )
            else:
                bpy.ops.export_scene.fbx(
                    filepath=export_file,
                    use_selection=True
                )

            item = props.recent_names.add()
            item.name = obj.name

            props.progress = (i + 1) / total
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        context.window.cursor_set("DEFAULT")
        self.report({'INFO'}, f"Exported {total} object(s)")
        return {'FINISHED'}


# ----------------------------
# UI Panel
# ----------------------------
class BATCHFBX_PT_MainPanel(Panel):
    bl_label = "BatchFBX"
    bl_idname = "BATCHFBX_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "DefaultCube"

    def draw(self, context):
        layout = self.layout
        props = context.scene.batchfbx_props
        selected = [obj for obj in context.selected_objects if obj.type == 'MESH']

        # Path Button (left, no stretch) + Path Text (right, fills rest)
        row = layout.row(align=True)
        row.operator("batchfbx.set_path", text="Path", icon='FILE_FOLDER')
        row.label(text=props.export_path if props.export_path else "")

        # Export Mode Header
        row = layout.row()
        row.alignment = 'CENTER'
        row.label(text="Export Mode", icon='SETTINGS')

        # Toggle buttons
        row = layout.row(align=True)
        row.operator("batchfbx.toggle_mode", text="VRChat", icon='MESH_UVSPHERE', depress=props.export_mode == 'VRCHAT').mode = 'VRCHAT'
        row.operator("batchfbx.toggle_mode", text="Default", icon='MESH_MONKEY', depress=props.export_mode == 'DEFAULT').mode = 'DEFAULT'

        # Export Settings (read-only)
        box = layout.box()
        box.enabled = False
        if props.export_mode == 'VRCHAT':
            box.label(text="✓ Selected Objects")
            box.label(text="✗ Camera, Lamp")
            box.label(text="✓ Apply Scalings: FBX Units Scale")
            box.label(text="✗ Add Leaf Bones")
            box.label(text="✗ Bake Animation")
            box.label(text="✗ Custom Properties")
        else:
            box.label(text="✓ Default Blender Settings")

        # Export Row: Count + Export Button
        row = layout.row(align=True)
        row.label(text=f"Selected: {len(selected)}", icon='MESH_CUBE')
        row.operator("batchfbx.export", text="Export", icon='EXPORT')

        # Progress
        layout.prop(props, "progress", text="Progress", slider=True)

        # Recent Exports Dropdown
        box = layout.box()
        row = box.row()
        row.prop(props, "show_recent", icon="TRIA_DOWN" if props.show_recent else "TRIA_RIGHT", text="", emboss=False)
        row.label(text="Recent Exports")

        if props.show_recent:
            for item in props.recent_names:
                box.label(text=item.name, icon='OBJECT_DATAMODE')

# ----------------------------
# Register / Unregister
# ----------------------------
classes = (
    BatchFBXProperties,
    BATCHFBX_OT_SetPath,
    BATCHFBX_OT_ToggleMode,
    BATCHFBX_OT_Export,
    BATCHFBX_PT_MainPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.batchfbx_props = bpy.props.PointerProperty(type=BatchFBXProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.batchfbx_props

if __name__ == "__main__":
    register()