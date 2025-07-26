bl_info = {
    "name": "UVwrap",
    "author": "Ziggor",
    "version": (2, 3),
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > UVwrap",
    "description": "Unwraps and scales UVs so 1m = 1 UV unit, with upright wall logic and per-object memory",
    "category": "UV",
}

import bpy
import bmesh
import sys
import io
from mathutils import Vector

last_object_id_global = None

# --------------------------
# Helpers
# --------------------------

def get_best_uv_axes(normal):
    normal = normal.normalized()
    up = Vector((0, 0, 1))
    forward = Vector((0, 1, 0))
    if abs(normal.dot(up)) > 0.9:
        return 0, 1
    elif abs(normal.dot(forward)) > 0.9:
        return 0, 2
    else:
        return 1, 2

def object_change_handler(scene, depsgraph):
    global last_object_id_global
    props = scene.uvwrap_props
    obj = bpy.context.active_object

    obj_id = str(id(obj)) if obj else ""
    if obj_id != last_object_id_global:
        last_object_id_global = obj_id
        props.status_message = ""
        if obj and obj.type == 'MESH':
            stored = obj.get("uvwrap_scale", None)
            props.scale = stored if stored is not None else 1.0

# --------------------------
# Operator
# --------------------------

class UVWRAP_OT_UnwrapBase(bpy.types.Operator):
    bl_idname = "uvwrap.unwrap_base"
    bl_label = "UVwrap Base"
    bl_options = {'UNDO', 'INTERNAL'}

    unwrap_method: bpy.props.EnumProperty(
        name="Unwrap Method",
        items=[
            ('ANGLE_BASED', 'Angle Based', 'Organic meshes'),
            ('CONFORMAL', 'Conformal', 'Hard-surface meshes'),
            ('SMART_PROJECT', 'Smart UV Project', 'Blender’s Smart UV Project')
        ],
        default='ANGLE_BASED'
    )

    scale: bpy.props.FloatProperty(
        name="Scale",
        description="1 UV unit equals this many meters",
        default=1.0,
        min=0.001
    )

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        props = context.scene.uvwrap_props
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "Please select a mesh object.")
            props.status_message = "⚠ No mesh object selected."
            return {'CANCELLED'}

        obj["uvwrap_scale"] = self.scale

        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        for f in bm.faces:
            f.select_set(True)

        try:
            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()

            if self.unwrap_method == 'SMART_PROJECT':
                bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.01)
                props.status_message = "✅ Smart UV Project completed"
            else:
                result = bpy.ops.uv.unwrap(method=self.unwrap_method, margin=0.001)
                output = buffer.getvalue()
                if "Unwrap failed to solve" in output:
                    props.status_message = "❌ Unwrap completed, but some islands failed.\nCheck seams or try Smart UV."
                elif 'CANCELLED' in result:
                    props.status_message = "❌ Unwrap failed completely.\nTry adding seams or Smart UV Project."
                    bpy.ops.object.mode_set(mode='OBJECT')
                    sys.stdout = old_stdout
                    return {'CANCELLED'}
                else:
                    props.status_message = "✅ Unwrap completed"

            sys.stdout = old_stdout

        except Exception as e:
            sys.stdout = old_stdout
            props.status_message = f"❌ Unwrap failed: {str(e)}"
            bpy.ops.object.mode_set(mode='OBJECT')
            return {'CANCELLED'}

        for face in bm.faces:
            u_axis, v_axis = get_best_uv_axes(face.normal)
            for loop in face.loops:
                co = obj.matrix_world @ loop.vert.co
                uv = loop[uv_layer].uv
                uv.x = co[u_axis] / self.scale
                uv.y = co[v_axis] / self.scale

        bmesh.update_edit_mesh(obj.data)
        bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}

# --------------------------
# Panel
# --------------------------

class UVWRAP_PT_Panel(bpy.types.Panel):
    bl_label = "UVwrap"
    bl_idname = "UVWRAP_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'UVwrap'

    def draw(self, context):
        layout = self.layout
        props = context.scene.uvwrap_props
        obj = context.active_object

        if obj and obj.type == 'MESH':
            stored = obj.get("uvwrap_scale", None)
            if stored is not None:
                info = layout.box()
                info.label(text=f"Stored Scale: {stored:.3f}", icon='INFO')

        layout.prop(props, "scale", text="World to UV Scale", icon='SORTSIZE')

        row = layout.row(align=True)
        col1 = row.column(align=True)
        col2 = row.column(align=True)
        col3 = row.column(align=True)

        col1.alignment = 'CENTER'
        col2.alignment = 'CENTER'
        col3.alignment = 'CENTER'

        col1.label(text="Organic")
        col2.label(text="Hard Surface")
        col3.label(text="UV Project")

        op = col1.operator("uvwrap.unwrap_base", text="Angle", icon='UV')
        op.unwrap_method = 'ANGLE_BASED'
        op.scale = props.scale

        op = col2.operator("uvwrap.unwrap_base", text="Conformal", icon='UV_DATA')
        op.unwrap_method = 'CONFORMAL'
        op.scale = props.scale

        op = col3.operator("uvwrap.unwrap_base", text="Smart", icon='MOD_UVPROJECT')
        op.unwrap_method = 'SMART_PROJECT'
        op.scale = props.scale

        if props.status_message:
            box = layout.box()
            lines = props.status_message.split('\n')
            for line in lines:
                box.label(text=line, icon='INFO' if "✅" in props.status_message else 'ERROR')

# --------------------------
# Properties
# --------------------------

class UVWRAP_Props(bpy.types.PropertyGroup):
    scale: bpy.props.FloatProperty(
        name="World to UV Scale",
        description="Meters per 1 UV unit",
        default=1.0,
        min=0.001
    )
    status_message: bpy.props.StringProperty(
        name="Status Message",
        default=""
    )

# --------------------------
# Register
# --------------------------

classes = (
    UVWRAP_OT_UnwrapBase,
    UVWRAP_PT_Panel,
    UVWRAP_Props,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.uvwrap_props = bpy.props.PointerProperty(type=UVWRAP_Props)
    bpy.app.handlers.depsgraph_update_post.append(object_change_handler)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.uvwrap_props
    if object_change_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(object_change_handler)

if __name__ == "__main__":
    register()
