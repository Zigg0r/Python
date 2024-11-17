import bpy
import os

bl_info = {
    "name": "BatchFBX",
    "author": "Ziggor",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > BatchFBX",
    "description": "Batch export selected meshes as separate FBX files",
    "category": "Import-Export",
}

class BatchFBXPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    path_location: bpy.props.StringProperty(
        name="Path",
        description="Folder location for FBX exports",
        subtype='DIR_PATH',
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Select Export Path:")
        layout.prop(self, "path_location")

class BatchFBXPanel(bpy.types.Panel):
    bl_label = "BatchFBX"
    bl_idname = "VIEW3D_PT_batch_fbx"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BatchFBX"

    def draw(self, context):
        layout = self.layout
        preferences = bpy.context.preferences.addons[__name__].preferences
        layout.label(text="Export Path: " + preferences.path_location)
        row = layout.row()
        row.operator("batch_fbx.path", text="Path")
        row = layout.row()
        row.operator("batch_fbx.export", text="Export")
        row = layout.row()
        row.operator("batch_fbx.toggle_face_orientation", text="Toggle Face Orientation")

class BatchFBXPathOperator(bpy.types.Operator):
    bl_idname = "batch_fbx.path"
    bl_label = "Set Export Path"

    filepath: bpy.props.StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        preferences = bpy.context.preferences.addons[__name__].preferences
        preferences.path_location = self.filepath
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class BatchFBXExportOperator(bpy.types.Operator):
    bl_idname = "batch_fbx.export"
    bl_label = "Export FBX"

    def execute(self, context):
        preferences = bpy.context.preferences.addons[__name__].preferences
        export_path = bpy.path.abspath(preferences.path_location)
        selected_objects = bpy.context.selected_objects
        for obj in selected_objects:
            if obj.type == 'MESH':
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                filepath = os.path.join(export_path, obj.name + ".fbx")
                bpy.ops.export_scene.fbx(filepath=filepath, use_selection=True)
        self.report({'INFO'}, "FBX export complete!")
        return {'FINISHED'}

class BatchFBXToggleFaceOrientationOperator(bpy.types.Operator):
    bl_idname = "batch_fbx.toggle_face_orientation"
    bl_label = "Toggle Face Orientation"

    def execute(self, context):
        bpy.context.space_data.overlay.show_face_orientation = not bpy.context.space_data.overlay.show_face_orientation
        return {'FINISHED'}

classes = (
    BatchFBXPreferences,
    BatchFBXPanel,
    BatchFBXPathOperator,
    BatchFBXExportOperator,
    BatchFBXToggleFaceOrientationOperator,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
