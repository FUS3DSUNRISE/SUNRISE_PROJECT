import bpy
import math

def make_box(name, w, d, h, x, y, z):
    verts = [(-w/2,-d/2,0),(w/2,-d/2,0),(w/2,d/2,0),(-w/2,d/2,0),
             (-w/2,-d/2,h),(w/2,-d/2,h),(w/2,d/2,h),(-w/2,d/2,h)]
    faces = [(0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (x, y, z)
    return obj

def make_cylinder(name, r, h, x, y, z, segs=32):
    verts, faces = [], []
    for i in range(segs):
        a = 2*math.pi*i/segs
        verts += [(r*math.cos(a),r*math.sin(a),0),(r*math.cos(a),r*math.sin(a),h)]
    for i in range(segs):
        a,b = 2*i, 2*((i+1)%segs)
        faces.append((a,b,b+1,a+1))
    faces.append([2*i for i in range(segs-1,-1,-1)])
    faces.append([2*i+1 for i in range(segs)])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (x, y, z)
    return obj

def set_material(obj, name, r, g, b, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (r,g,b,1)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    if obj.data.materials: obj.data.materials[0] = mat
    else: obj.data.materials.append(mat)

def parent_objects(children, root_name):
    root = bpy.data.objects.new(root_name, None)
    bpy.context.collection.objects.link(root)
    for obj in children: obj.parent = root
    return root

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in bpy.data.meshes: bpy.data.meshes.remove(block)
for block in bpy.data.materials: bpy.data.materials.remove(block)

seat = make_box('seat', 0.45, 0.45, 0.04, 0, 0, 0.45)
leg1 = make_box('leg1', 0.04, 0.04, 0.45, -0.205, -0.205, 0)
leg2 = make_box('leg2', 0.04, 0.04, 0.45, 0.205, -0.205, 0)
leg3 = make_box('leg3', 0.04, 0.04, 0.45, -0.205, 0.205, 0)
leg4 = make_box('leg4', 0.04, 0.04, 0.45, 0.205, 0.205, 0)
back = make_box('back', 0.45, 0.05, 0.50, 0, -0.225, 0.49)

set_material(seat, 'Blue', 0.0, 0.0, 1.0)
set_material(leg1, 'Blue', 0.0, 0.0, 1.0)
set_material(leg2, 'Blue', 0.0, 0.0, 1.0)
set_material(leg3, 'Blue', 0.0, 0.0, 1.0)
set_material(leg4, 'Blue', 0.0, 0.0, 1.0)
set_material(back, 'Blue', 0.0, 0.0, 1.0)

children = [seat, leg1, leg2, leg3, leg4, back]
parent_objects(children, 'Blue Chair')

bpy.ops.export_scene.gltf(filepath='static/models/prompt_8.glb', export_format='GLB')