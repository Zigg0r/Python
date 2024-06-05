import bpy

materials_merged_colours = {}
for mat in bpy.data.materials:
    if mat.name == 'Dots Stroke':
        continue
    if mat.use_nodes:
        try:
            colour = mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value[:]
        except AttributeError:
            continue
        except KeyError:
            try:
                colour = mat.node_tree.nodes[0].inputs[0].default_value[:]
            except:
                continue
    else:
        colour = mat.diffuse_color[:]
    merged_mat = False
    for original_mat_key in materials_merged_colours.keys():
        if colour == materials_merged_colours[original_mat_key][:]: #de [:] is nodig omdat je anders addressen vergelijkt ipv values
            mat.user_remap(bpy.data.materials[original_mat_key].id_data)
            merged_mat = True
    if not merged_mat:
        materials_merged_colours[mat.name] = colour