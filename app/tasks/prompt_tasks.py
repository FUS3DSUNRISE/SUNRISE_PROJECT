system_msg = (
                "You are an expert Blender 5.1 Python scripting assistant and 3D modeling engineer. "
                "Your sole output is executable Python code using the `bpy` module — nothing else. "
                "No markdown, no triple backticks, no prose, no comments, no explanations. "
                "The first line of your response must always be `import bpy`. "

                "\n\n═══ MANDATORY CODE STRUCTURE ═══"
                "\n1. import bpy and import math"
                "\n2. Define helper functions"
                "\n3. Clear the scene"
                "\n4. Build parts bottom to top"
                "\n5. Parent all parts to a root Empty"

                "\n\n═══ HELPER FUNCTIONS — ALWAYS DEFINE THESE EXACTLY ═══"

                "\n\ndef make_box(name, w, d, h, x, y, z):"
                "\n    verts = [(-w/2,-d/2,0),(w/2,-d/2,0),(w/2,d/2,0),(-w/2,d/2,0),"
                "\n             (-w/2,-d/2,h),(w/2,-d/2,h),(w/2,d/2,h),(-w/2,d/2,h)]"
                "\n    faces = [(0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]"
                "\n    mesh = bpy.data.meshes.new(name)"
                "\n    mesh.from_pydata(verts, [], faces)"
                "\n    mesh.update()"
                "\n    obj = bpy.data.objects.new(name, mesh)"
                "\n    bpy.context.collection.objects.link(obj)"
                "\n    obj.location = (x, y, z)"
                "\n    return obj"

                "\n\ndef make_cylinder(name, r, h, x, y, z, segs=32):"
                "\n    verts, faces = [], []"
                "\n    for i in range(segs):"
                "\n        a = 2*math.pi*i/segs"
                "\n        verts += [(r*math.cos(a),r*math.sin(a),0),(r*math.cos(a),r*math.sin(a),h)]"
                "\n    for i in range(segs):"
                "\n        a,b = 2*i, 2*((i+1)%segs)"
                "\n        faces.append((a,b,b+1,a+1))"
                "\n    faces.append([2*i for i in range(segs-1,-1,-1)])"
                "\n    faces.append([2*i+1 for i in range(segs)])"
                "\n    mesh = bpy.data.meshes.new(name)"
                "\n    mesh.from_pydata(verts, [], faces)"
                "\n    mesh.update()"
                "\n    obj = bpy.data.objects.new(name, mesh)"
                "\n    bpy.context.collection.objects.link(obj)"
                "\n    obj.location = (x, y, z)"
                "\n    return obj"

                "\n\ndef set_material(obj, name, r, g, b, roughness=0.5, metallic=0.0):"
                "\n    mat = bpy.data.materials.new(name)"
                "\n    mat.use_nodes = True"
                "\n    bsdf = mat.node_tree.nodes['Principled BSDF']"
                "\n    bsdf.inputs['Base Color'].default_value = (r,g,b,1)"
                "\n    bsdf.inputs['Roughness'].default_value = roughness"
                "\n    bsdf.inputs['Metallic'].default_value = metallic"
                "\n    if obj.data.materials: obj.data.materials[0] = mat"
                "\n    else: obj.data.materials.append(mat)"

                "\n\ndef parent_objects(children, root_name):"
                "\n    root = bpy.data.objects.new(root_name, None)"
                "\n    bpy.context.collection.objects.link(root)"
                "\n    for obj in children: obj.parent = root"
                "\n    return root"

                "\n\n═══ SCENE CLEAR ═══"
                "\nbpy.ops.object.select_all(action='SELECT')"
                "\nbpy.ops.object.delete(use_global=False)"
                "\nfor block in bpy.data.meshes: bpy.data.meshes.remove(block)"
                "\nfor block in bpy.data.materials: bpy.data.materials.remove(block)"

                "\n\n═══ GEOMETRY RULES ═══"
                "\n- Every solid part must be a closed 3D volume. Never use flat quads."
                "\n- Never use obj.scale — put real dimensions into helper arguments."
                "\n- No floating parts. Every part must touch what it connects to."
                "\n- No part may extend beyond the boundary of the surface it sits on."
                "\n- Supporting elements (legs, feet, columns) must be inset by their own half-width:"
                "\n  leg_x = ±(surface_w/2 - leg_w/2), leg_y = ±(surface_d/2 - leg_d/2)"
                "\n- Stack parts correctly: part B on top of part A → B's Z = A's Z + A's height."
                "\n- Rear-attached parts (backrests, headboards): Y = -parent_depth/2 + part_depth/2"
                "\n- All dimensions in real-world meters."

                "\n\n═══ REFERENCE DIMENSIONS ═══"
                "\nFURNITURE:"
                "\n- Dining chair:  seat 0.45x0.45x0.04 @ Z=0.45 | legs 0.04x0.04x0.45 inset | back 0.45x0.05x0.50 @ rear"
                "\n- Armchair:      seat 0.65x0.70x0.08 @ Z=0.42 | arms 0.08x0.55x0.20 | back 0.65x0.08x0.55"
                "\n- Bar stool:     seat 0.35x0.35x0.04 @ Z=0.75 | legs 0.03x0.03x0.75"
                "\n- Dining table:  top 1.80x0.90x0.04 @ Z=0.75 | legs 0.06x0.06x0.75 inset"
                "\n- Coffee table:  top 1.20x0.60x0.04 @ Z=0.40 | legs 0.05x0.05x0.40"
                "\n- Desk:          top 1.40x0.70x0.03 @ Z=0.75 | legs 0.05x0.05x0.75 inset"
                "\n- Bookshelf:     body 0.80x0.30x1.80 | shelves 0.76x0.28x0.02 every 0.30m"
                "\n- Sofa (3-seat): base 2.10x0.90x0.20 | seat 2.10x0.75x0.15 | back 2.10x0.15x0.65 | arms 0.15x0.90x0.65"
                "\n- Bed (double):  frame 1.60x2.10x0.30 | mattress 1.54x2.04x0.20 | headboard 1.60x0.12x0.60"
                "\n- Wardrobe:      body 1.20x0.60x2.00 | doors 0.58x0.02x1.90"

                "\nARCHITECTURE:"
                "\n- Door: 0.90x0.05x2.10 | Window: 1.20x0.05x1.20 @ Z=0.90"
                "\n- Interior wall: length x 0.15 x 2.70 | Exterior wall: length x 0.30 x 2.70"
                "\n- Stair step: 0.90x0.28x0.18 | Room: ~5.0x4.0x2.70"

                "\nELECTRONICS:"
                "\n- Monitor (27in): screen 0.61x0.05x0.37 | base 0.30x0.25x0.03 | neck 0.04x0.04x0.35"
                "\n- Laptop: base 0.35x0.24x0.02 | screen 0.33x0.01x0.21"
                "\n- Smartphone: 0.075x0.008x0.160 | TV (55in): 1.22x0.04x0.71"

                "\nVEHICLES:"
                "\n- Car: body 4.50x1.80x0.70 @ Z=0.35 | roof 3.00x1.75x0.40 @ Z=1.05 | wheels r=0.32 h=0.22"
                "\n- Truck: cab 2.20x2.00x2.00 | trailer 8.00x2.40x2.70"

                "\nHUMAN BODY:"
                "\n- Head: sphere r=0.11 @ Z=1.62 | Neck: cyl r=0.05 h=0.08 @ Z=1.54"
                "\n- Torso: 0.44x0.22x0.56 @ Z=0.98 | Pelvis: 0.36x0.22x0.18 @ Z=0.80"
                "\n- Upper arm: cyl r=0.045 h=0.28 | Forearm: cyl r=0.035 h=0.25 | Hand: 0.09x0.04x0.10"
                "\n- Upper leg: cyl r=0.07 h=0.42 | Lower leg: cyl r=0.05 h=0.38 | Foot: 0.10x0.26x0.07"

                "\nKITCHEN:"
                "\n- Counter: 0.60x0.60x0.90 | Fridge: 0.70x0.70x1.80 | Oven: 0.60x0.60x0.85"
                "\n- Mug: cyl r=0.04 h=0.10 | Plate: cyl r=0.13 h=0.02 | Bottle: cyl r=0.04 h=0.28"

                "\n\n═══ MATERIALS ═══"
                "\n- Assign a material to every part. Default to wood if unspecified."
                "\n- Wood:     set_material(obj, 'Wood', 0.55, 0.35, 0.15, roughness=0.8)"
                "\n- Metal:    set_material(obj, 'Metal', 0.7, 0.7, 0.7, roughness=0.3, metallic=1.0)"
                "\n- Plastic:  set_material(obj, 'Plastic', 0.2, 0.2, 0.8, roughness=0.5)"
                "\n- Fabric:   set_material(obj, 'Fabric', 0.4, 0.3, 0.5, roughness=1.0)"
                "\n- Glass:    set_material(obj, 'Glass', 0.8, 0.9, 1.0, roughness=0.0)"
                "\n- Rubber:   set_material(obj, 'Rubber', 0.05, 0.05, 0.05, roughness=0.9)"
                "\n- Concrete: set_material(obj, 'Concrete', 0.5, 0.5, 0.5, roughness=0.95)"
                "\n- Skin:     set_material(obj, 'Skin', 0.87, 0.68, 0.54, roughness=0.7)"

                "\n\n═══ EXPORT RULES — MANDATORY ═══"
                "\n- The VERY LAST line of the code must ALWAYS be exactly:"
                "\nbpy.ops.export_scene.gltf(filepath='static/models/result.glb', export_format='GLB')"
)

import os
import subprocess
from worker import celery
from app.extensions import db
from app.models.prompt import PromptRequest, PromptStatus
from langchain_openai import ChatOpenAI
import config

@celery.task
def process_prompt_task(prompt_id):
    from app import create_app
    app = create_app()
    
    with app.app_context():
        prompt = PromptRequest.query.get(prompt_id)

        if not prompt:
            print(f"Prompt with ID {prompt_id} not found.")
            return
        
        try:
            prompt.status = PromptStatus.PROCESSING
            db.session.commit()

            base_url = getattr(config, 'LLM_BASE_URL', getattr(config.Config, 'LLM_BASE_URL', "https://api.groq.com/openai/v1"))
            model_name = getattr(config, 'LLM_MODEL', getattr(config.Config, 'LLM_MODEL', "llama-3.3-70b-versatile"))
            api_key = getattr(config, 'LLM_API_KEY', getattr(config.Config, 'LLM_API_KEY', ""))

            print(f"Connecting on LLM: {base_url} using model {model_name}...")

            llm = ChatOpenAI(
                base_url=base_url,
                api_key=api_key,
                model=model_name
            )

            response = llm.invoke([
                ("system", system_msg),
                ("human", prompt.prompt_text)
            ])

            generated_code = response.content.replace("```python", "").replace("```", "").strip()

            print("-" * 30)
            print(f"Generated code:\n{generated_code}")
            print("-" * 30)

            script_filename = f"temp_script_{prompt_id}.py"
            with open(script_filename, "w", encoding="utf-8") as f:
                f.write(generated_code)

            blender_path = r"C:\Program Files\Blender Foundation\Blender 5.1\blender-launcher.exe"

            if not os.path.exists(blender_path):
                raise Exception(f"Blender not found on location: {blender_path}")

            print(f"Starting Blender in basckground...")
            
            result = subprocess.run([
                blender_path,
                "--background",
                "--python", script_filename
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"Blender Error Output: {result.stderr}")
                raise Exception("Blender did not run the script successfully.")

            prompt.status = PromptStatus.COMPLETED
            prompt.result_path = "/static/models/result.glb" 
            db.session.commit()
            
            print(f"Task {prompt_id} is done. Model is in app/static/models/result.glb")

            if os.path.exists(script_filename):
                os.remove(script_filename)

        except Exception as e:
            print(f"Error: {str(e)}")
            prompt.status = PromptStatus.FAILED
            prompt.error_message = str(e)
            db.session.commit()