"""Hammer and feather on the Moon: a small Blender scene, built and rendered headless.

Run (Blender 4.2):
  blender --background --factory-startup --python hammer_feather_moon.py -- MODE OUTDIR [SAMPLES] [cpu]

MODE is one of:
  still      one turntable frame (frame 1) as OUTDIR/still.png, for a quick check
  turntable  36 frames, camera circling the scene, 960x540, OUTDIR/turn_01.png ... turn_36.png
  drop       90 frames at 30 fps, 1280x720, hammer and feather falling together, OUTDIR/drop_0001.png ...
  dropcheck  four single frames of the drop (held, mid-fall, landing, end) for a quick check
Add cpu as a fourth word to render without the graphics card.

The physics in the drop:
  release height h = 1.6 m (NASA Science, "The Apollo 15 Hammer-Feather Drop")
  Moon surface gravity g = 1.624 m/s2 (NASA Science, "Compare Earth and the Moon")
  height of the bottom of each object at time t after release: z = h - g * t * t / 2
  time to land: sqrt(2 * 1.6 / 1.624) = 1.404 s
Both objects use the same formula, because on the Moon there is almost no air.
After landing, each object tips over onto its side. That tip-over is drawn by eye, not computed.
"""

import math
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

# ---------------------------------------------------------------- settings
H = 1.6            # release height in metres
G_MOON = 1.624     # Moon surface gravity in m/s2
FPS = 30
HOLD = 0.5         # seconds the objects hang still before the release
DROP_FRAMES = 90   # 3 seconds at 30 fps
GHOST_EVERY = 0.2  # a faint copy is left every 0.2 s while falling, as in the talk's 2D page
T_LAND = math.sqrt(2 * H / G_MOON)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODE = argv[0] if argv else "still"
OUT = argv[1] if len(argv) > 1 else "//render"
SAMPLES = int(argv[2]) if len(argv) > 2 else 96
FORCE_CPU = len(argv) > 3 and argv[3] == "cpu"  # skip the graphics card even if there is one

random.seed(15)  # Apollo 15: the same "random" craters and rocks on every run

# ---------------------------------------------------------------- empty scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
col = scene.collection


def material(name, color, rough=0.9, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def link(obj):
    col.objects.link(obj)
    return obj


def mesh_object(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return link(bpy.data.objects.new(name, me))


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def empty(name):
    return link(bpy.data.objects.new(name, None))


# ---------------------------------------------------------------- ground with craters
craters = []
for _ in range(70):
    r = random.choice([0.4, 0.6, 0.9, 1.3, 2.0, 3.0, 5.0, 8.0])
    while True:
        x, y = random.uniform(-45, 45), random.uniform(-45, 45)
        if math.hypot(x, y) > r + 2.2:  # keep the spot where the objects land flat
            break
    craters.append((x, y, r))
# three craters placed by hand so some always show near the objects
craters += [(2.6, 1.9, 0.9), (-2.4, -2.2, 0.7), (-3.4, 2.8, 1.4)]


def ground_height(x, y):
    z = 0.0
    for cx, cy, r in craters:
        d = math.hypot(x - cx, y - cy) / r
        if d < 1.0:
            z -= 0.22 * r * (1.0 - d * d)                        # bowl
        if 0.75 < d < 1.6:
            z += 0.07 * r * math.exp(-((d - 1.0) / 0.22) ** 2)  # raised rim
    v = Vector((x * 0.35, y * 0.35, 0.0))
    z += 0.08 * noise.fractal(v, 0.6, 2.0, 4)       # gentle rolling ground
    z += 0.012 * noise.fractal(v * 8, 0.5, 2.0, 3)  # fine lumps
    dist = math.hypot(x, y)
    if dist < 1.8:                                   # flat landing patch, blended in
        z *= (dist / 1.8) ** 2
    return z


bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=360, y_segments=360, size=50.0)
for v in bm.verts:
    v.co.z = ground_height(v.co.x, v.co.y)
ground = mesh_object("Ground", bm)
smooth(ground)
# far plain beyond the detailed ground, so the horizon looks continuous
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=40, y_segments=40, size=400.0)
for v in bm.verts:
    v.co.z = -0.45 - 0.002 * (v.co.x ** 2 + v.co.y ** 2) ** 0.5 + 1.5 * noise.noise(v.co * 0.01)
far = mesh_object("FarGround", bm)
smooth(far)

regolith = bpy.data.materials.new("Regolith")
regolith.use_nodes = True
nt = regolith.node_tree
bsdf = nt.nodes["Principled BSDF"]
bsdf.inputs["Roughness"].default_value = 1.0
tex = nt.nodes.new("ShaderNodeTexNoise")
tex.inputs["Scale"].default_value = 0.6
tex.inputs["Detail"].default_value = 8.0
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.35
ramp.color_ramp.elements[0].color = (0.085, 0.085, 0.082, 1)
ramp.color_ramp.elements[1].position = 0.65
ramp.color_ramp.elements[1].color = (0.24, 0.235, 0.225, 1)
nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
grain = nt.nodes.new("ShaderNodeTexNoise")
grain.inputs["Scale"].default_value = 140.0
grain.inputs["Detail"].default_value = 4.0
bump = nt.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.3
nt.links.new(grain.outputs["Fac"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
ground.data.materials.append(regolith)
far.data.materials.append(regolith)

# a few rocks
rock_mat = material("Rock", (0.13, 0.128, 0.122), rough=0.95)
for i in range(45):
    while True:
        x, y = random.uniform(-14, 14), random.uniform(-14, 14)
        if math.hypot(x, y) > 1.6:
            break
    s = random.choice([0.04, 0.06, 0.08, 0.12, 0.18, 0.28])
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    off = Vector((random.random() * 50, random.random() * 50, random.random() * 50))
    for v in bm.verts:
        v.co *= 1.0 + 0.35 * noise.noise(v.co * 1.3 + off)
        v.co.z *= 0.6
    rock = mesh_object(f"Rock{i}", bm)
    rock.scale = (s * random.uniform(0.8, 1.4), s, s)
    rock.rotation_euler.z = random.uniform(0, 6.28)
    rock.location = (x, y, ground_height(x, y) + 0.15 * s)
    rock.data.materials.append(rock_mat)

# ---------------------------------------------------------------- the hammer
# Built in the x-z plane, facing the front camera: handle along x, head upright at the +x end.
aluminium = material("Aluminium", (0.78, 0.78, 0.80), rough=0.4, metal=0.55)
grip = material("Grip", (0.05, 0.05, 0.055), rough=0.7)
ALONG_X = Matrix.Rotation(math.pi / 2, 4, "Y")


def build_hammer():
    parts = []
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.014, radius2=0.014, depth=0.33,
                          matrix=ALONG_X)
    handle = mesh_object("HammerHandle", bm)
    handle.data.materials.append(aluminium)
    parts.append(handle)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.0175, radius2=0.0175, depth=0.16,
                          matrix=Matrix.Translation((-0.075, 0, 0)) @ ALONG_X)
    sleeve = mesh_object("HammerGrip", bm)
    sleeve.data.materials.append(grip)
    parts.append(sleeve)
    # head: a square striking face at the bottom, a chisel-like pick at the top
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.044
        v.co.y *= 0.034
        v.co.z *= 0.17
        if v.co.z > 0:
            v.co.x *= 0.45
            v.co.z += 0.02
    head = mesh_object("HammerHead", bm)
    head.location.x = 0.17
    head.data.materials.append(aluminium)
    bev = head.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.004
    bev.segments = 3
    parts.append(head)
    smooth(handle)
    smooth(sleeve)
    return parts


# ---------------------------------------------------------------- the feather
# Built in the x-z plane too: quill along x, vane spread up and down.
feather_mat = bpy.data.materials.new("Feather")
feather_mat.use_nodes = True
nt = feather_mat.node_tree
bsdf = nt.nodes["Principled BSDF"]
bsdf.inputs["Roughness"].default_value = 0.8
coord = nt.nodes.new("ShaderNodeTexCoord")
wave = nt.nodes.new("ShaderNodeTexWave")  # dark and light bars across the vane
wave.inputs["Scale"].default_value = 9.0
wave.inputs["Distortion"].default_value = 2.0
wave.bands_direction = "X"
nt.links.new(coord.outputs["Object"], wave.inputs["Vector"])
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (0.17, 0.10, 0.055, 1)
ramp.color_ramp.elements[1].color = (0.82, 0.72, 0.56, 1)
nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
quill_mat = material("Quill", (0.85, 0.80, 0.70), rough=0.5)


def build_feather():
    L = 0.30
    bm = bmesh.new()
    nu, nv = 40, 7
    rows = []
    for i in range(nu + 1):
        u = i / nu
        x = -L / 2 + L * u
        curl = 0.035 * u * u  # the feather curls a little toward its tip
        if u < 0.18:
            wl = wr = 0.0     # bare quill near the base
        else:
            k = (u - 0.18) / 0.82
            shape = math.sin(math.pi * min(1.0, k ** 0.65)) ** 0.8
            wl, wr = 0.030 * shape, 0.017 * shape  # one side wider, like a flight feather
        row = []
        for j in range(-nv, nv + 1):
            s = j / nv
            w = wl if s < 0 else wr
            row.append(bm.verts.new((x, -0.012 * s * s * (w / 0.03), w * s + curl)))
        rows.append(row)
    for i in range(nu):
        for j in range(2 * nv):
            quad = (rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j])
            if len({v.co.to_tuple(5) for v in quad}) >= 3:
                bm.faces.new(quad)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    vane = mesh_object("FeatherVane", bm)
    smooth(vane)
    vane.modifiers.new("Solidify", "SOLIDIFY").thickness = 0.0012
    vane.data.materials.append(feather_mat)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.0022, radius2=0.0008, depth=L,
                          matrix=ALONG_X)
    for v in bm.verts:
        u = (v.co.x + L / 2) / L
        v.co.z += 0.035 * u * u
    quill = mesh_object("FeatherQuill", bm)
    quill.data.materials.append(quill_mat)
    smooth(quill)
    return [vane, quill]


def carrier(name, parts, x, y):
    """An empty that holds the parts with its origin on the lowest point, on the +y (far) edge.
    Moving the carrier moves the object; turning it about x tips the object over that edge."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for p in parts:
        ev = p.evaluated_get(dg)
        pts += [p.matrix_world @ v.co for v in ev.to_mesh().vertices]
        ev.to_mesh_clear()
    zmin = min(q.z for q in pts)
    ymax = max(q.y for q in pts)
    c = empty(name)
    for p in parts:
        p.parent = c
        p.location -= Vector((0, ymax, zmin))
    c.location = (x, y, H)
    return c


HX, FX = -0.50, 0.32  # hammer head ends up near x = -0.33, feather spans x = 0.17 to 0.47
hammer_obj = carrier("Hammer", build_hammer(), HX, 0.0)
feather_obj = carrier("Feather", build_feather(), FX, 0.0)

# ---------------------------------------------------------------- a striped height rod, 1.6 m
white = material("RodWhite", (0.85, 0.85, 0.85), rough=0.6)
orange = material("RodOrange", (0.9, 0.35, 0.05), rough=0.6)
ROD = (-0.08, 0.0)  # between the two objects, at the same distance from the camera
for k in range(8):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.025
        v.co.y *= 0.025
        v.co.z = (v.co.z + 0.5) * 0.2 + 0.2 * k
    seg = mesh_object(f"Rod{k}", bm)
    seg.location = (*ROD, 0.0)
    seg.data.materials.append(orange if k % 2 else white)
txt_curve = bpy.data.curves.new("RodLabel", "FONT")
txt_curve.body = "1.6 m"
txt_curve.size = 0.11
txt_curve.align_x = "CENTER"
txt_curve.extrude = 0.004
label = link(bpy.data.objects.new("RodLabel", txt_curve))
label.location = (ROD[0], ROD[1], H + 0.05)
label.rotation_euler.x = math.radians(90)
label.data.materials.append(material("Label", (0.9, 0.9, 0.9), rough=0.5))

# ---------------------------------------------------------------- the Earth in the sky
# Drawn about twice as wide as it looks from the Moon, so it reads on a projector.
EARTH_AZ = Vector((-0.42, 1.0, 0.0)).normalized()
EARTH_ELEV = math.radians(8)
EARTH_D = 300.0
earth_pos = Vector((EARTH_AZ.x * math.cos(EARTH_ELEV), EARTH_AZ.y * math.cos(EARTH_ELEV),
                    math.sin(EARTH_ELEV))) * EARTH_D
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=10.0, location=earth_pos)
earth = bpy.context.active_object
earth.rotation_euler = (math.radians(23), 0.0, math.radians(40))
smooth(earth)
em = bpy.data.materials.new("Earth")
em.use_nodes = True
nt = em.node_tree
bsdf = nt.nodes["Principled BSDF"]
bsdf.inputs["Roughness"].default_value = 0.6
land = nt.nodes.new("ShaderNodeTexNoise")
land.inputs["Scale"].default_value = 1.6
land.inputs["Detail"].default_value = 6.0
land_ramp = nt.nodes.new("ShaderNodeValToRGB")
land_ramp.color_ramp.interpolation = "CONSTANT"
land_ramp.color_ramp.elements[0].color = (0.02, 0.09, 0.35, 1)  # ocean
land_ramp.color_ramp.elements[1].position = 0.56
land_ramp.color_ramp.elements[1].color = (0.22, 0.30, 0.10, 1)  # land
nt.links.new(land.outputs["Fac"], land_ramp.inputs["Fac"])
cloud = nt.nodes.new("ShaderNodeTexNoise")
cloud.inputs["Scale"].default_value = 3.5
cloud.inputs["Detail"].default_value = 8.0
cloud_ramp = nt.nodes.new("ShaderNodeValToRGB")
cloud_ramp.color_ramp.elements[0].position = 0.5
cloud_ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
cloud_ramp.color_ramp.elements[1].position = 0.68
cloud_ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
nt.links.new(cloud.outputs["Fac"], cloud_ramp.inputs["Fac"])
mix = nt.nodes.new("ShaderNodeMix")
mix.data_type = "RGBA"
nt.links.new(cloud_ramp.outputs["Color"], mix.inputs["Factor"])
nt.links.new(land_ramp.outputs["Color"], mix.inputs["A"])
mix.inputs["B"].default_value = (0.95, 0.95, 0.95, 1)
nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
earth.data.materials.append(em)
earth.visible_shadow = False

# ---------------------------------------------------------------- light: a low Sun, hard shadows
sun_data = bpy.data.lights.new("Sun", "SUN")
sun_data.energy = 4.5
sun_data.angle = math.radians(0.6)
sun = link(bpy.data.objects.new("Sun", sun_data))
sun.rotation_euler = (math.radians(68), 0.0, math.radians(-50))  # about 22 degrees above the ground
# weak cool fill from the other side so shadows are not pure black on a projector
fill_data = bpy.data.lights.new("Fill", "SUN")
fill_data.energy = 0.5
fill_data.color = (0.75, 0.82, 1.0)
fill_data.angle = math.radians(30)
fill = link(bpy.data.objects.new("Fill", fill_data))
fill.rotation_euler = (math.radians(50), 0.0, math.radians(160))

# ---------------------------------------------------------------- black sky with stars
world = bpy.data.worlds.new("Space")
scene.world = world
world.use_nodes = True
nt = world.node_tree
bg = nt.nodes["Background"]
tc = nt.nodes.new("ShaderNodeTexCoord")
vor = nt.nodes.new("ShaderNodeTexVoronoi")
vor.inputs["Scale"].default_value = 260.0
nt.links.new(tc.outputs["Generated"], vor.inputs["Vector"])
sr = nt.nodes.new("ShaderNodeMapRange")  # a dot where a point is near a cell centre
sr.inputs["From Min"].default_value = 0.0
sr.inputs["From Max"].default_value = 0.09
sr.inputs["To Min"].default_value = 1.0
sr.inputs["To Max"].default_value = 0.0
sr.clamp = True
nt.links.new(vor.outputs["Distance"], sr.inputs["Value"])
pick = nt.nodes.new("ShaderNodeMath")    # only some cells get a star
pick.operation = "GREATER_THAN"
pick.inputs[1].default_value = 0.72
nt.links.new(vor.outputs["Color"], pick.inputs[0])
mul = nt.nodes.new("ShaderNodeMath")
mul.operation = "MULTIPLY"
nt.links.new(sr.outputs["Result"], mul.inputs[0])
nt.links.new(pick.outputs["Value"], mul.inputs[1])
bright = nt.nodes.new("ShaderNodeMath")
bright.operation = "MULTIPLY"
bright.inputs[1].default_value = 6.0
nt.links.new(mul.outputs["Value"], bright.inputs[0])
lp = nt.nodes.new("ShaderNodeLightPath")  # stars are seen by the camera but light nothing
gate = nt.nodes.new("ShaderNodeMath")
gate.operation = "MULTIPLY"
nt.links.new(bright.outputs["Value"], gate.inputs[0])
nt.links.new(lp.outputs["Is Camera Ray"], gate.inputs[1])
nt.links.new(gate.outputs["Value"], bg.inputs["Strength"])
bg.inputs["Color"].default_value = (1, 1, 1, 1)

# ---------------------------------------------------------------- render settings
scene.render.engine = "CYCLES"
cprefs = bpy.context.preferences.addons["cycles"].preferences
use_gpu = False
for dev_type in () if FORCE_CPU else ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
    try:
        cprefs.compute_device_type = dev_type
        cprefs.get_devices()
        if any(d.type == dev_type for d in cprefs.devices):
            for d in cprefs.devices:
                d.use = d.type == dev_type
            use_gpu = True
            break
    except TypeError:
        pass
scene.cycles.device = "GPU" if use_gpu else "CPU"
print("RENDER DEVICE:", scene.cycles.device, cprefs.compute_device_type if use_gpu else "", "DENOISER:", scene.cycles.denoiser)
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 4
scene.cycles.diffuse_bounces = 2
scene.cycles.glossy_bounces = 2
scene.cycles.transparent_max_bounces = 8
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = 0.0
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.fps = FPS

cam_data = bpy.data.cameras.new("Camera")
cam = link(bpy.data.objects.new("Camera", cam_data))
scene.camera = cam
target = empty("Target")
track = cam.constraints.new("TRACK_TO")
track.target = target
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"


# ---------------------------------------------------------------- the drop
def pose(t):
    """(height, tip angle) of each object t seconds after the clip starts."""
    tf = t - HOLD
    if tf <= 0:
        return H, 0.0
    if tf < T_LAND:
        return H - 0.5 * G_MOON * tf * tf, 0.0
    s = min(1.0, (tf - T_LAND) / 0.45)  # tip over onto the side in 0.45 s (drawn by eye)
    return 0.0, math.radians(90) * s * s


def animate_drop():
    for f in range(1, DROP_FRAMES + 1):
        z, tip = pose((f - 1) / FPS)
        for obj in (hammer_obj, feather_obj):
            obj.location.z = z
            obj.rotation_euler.x = -tip
            obj.keyframe_insert("location", index=2, frame=f)
            obj.keyframe_insert("rotation_euler", index=0, frame=f)
    for obj in (hammer_obj, feather_obj):
        for fc in obj.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def setup_ghosts():
    """Faint copies every 0.2 s from the release, each shown from the moment it is passed."""
    ghost = bpy.data.materials.new("Ghost")
    ghost.use_nodes = True
    nt = ghost.node_tree
    out = nt.nodes["Material Output"]
    bs = nt.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.75, 0.85, 1.0, 1)
    bs.inputs["Emission Color"].default_value = (0.6, 0.75, 1.0, 1)
    bs.inputs["Emission Strength"].default_value = 0.3
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs["Fac"].default_value = 0.3
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(bs.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    k = 0  # k = 0 marks the release point
    while k * GHOST_EVERY < T_LAND - 0.05:
        t = k * GHOST_EVERY
        z = H - 0.5 * G_MOON * t * t
        frame_shown = round((HOLD + t) * FPS) + 1
        for src in (hammer_obj, feather_obj):
            root = empty(f"{src.name}Ghost{k}")
            root.location = (src.location.x, src.location.y, z)
            for child in src.children:
                g = child.copy()
                g.data = child.data.copy()
                g.data.materials.clear()
                g.data.materials.append(ghost)
                g.animation_data_clear()
                link(g)
                g.parent = root
                g.visible_shadow = False
                for f, hide in ((1, True), (frame_shown, False)):
                    g.hide_render = hide
                    g.keyframe_insert("hide_render", frame=f)
        k += 1


def render_still(path):
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


if MODE in ("still", "turntable"):
    scene.render.resolution_x, scene.render.resolution_y = 960, 540
    cam_data.lens = 24
    cx, cy = ROD
    target.location = (cx, cy, 1.05)
    frames = [0] if MODE == "still" else range(36)
    for i in frames:
        a = math.radians(-90 + 10 * i)  # frame 1 looks from the front (-y), then 10 degrees per frame
        cam.location = (cx + 2.5 * math.cos(a), cy + 2.5 * math.sin(a), 1.4)
        label.rotation_euler.z = a + math.radians(90)  # the "1.6 m" label turns to face the camera
        render_still(f"{OUT}/" + ("still" if MODE == "still" else f"turn_{i + 1:02d}") + ".png")

elif MODE in ("drop", "dropcheck"):
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    cam_data.lens = 30
    cam.location = (0.0, -3.1, 0.8)
    target.location = (-0.08, 0.0, 0.95)
    animate_drop()
    setup_ghosts()
    scene.frame_start, scene.frame_end = 1, DROP_FRAMES
    if MODE == "dropcheck":
        for f in (1, 37, 59, 90):
            scene.frame_set(f)
            render_still(f"{OUT}/dropcheck_{f:03d}.png")
    else:
        scene.render.filepath = f"{OUT}/drop_"
        bpy.ops.render.render(animation=True)
