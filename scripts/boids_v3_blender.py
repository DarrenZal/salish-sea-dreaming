#!/usr/bin/env python3
"""
Boids v3 — Tree-Murmuration Cycle (40 seconds, 1200 frames at 30fps)
=====================================================================
Fish school → rise → cross waterline → murmuration in tree canopy 
(trees and birds share space) → murmuration dives back → fish school.
Complete cycle.

Fixes from v2:
  - Trees and murmuration morph into each other at canopy height
  - Murmuration dives back into water becoming fish again
  - Complete cycle that could loop

Usage: blender --background --python boids_v3_blender.py
Output: /home/jovyan/boids_v3/depth/frame_0000.png through frame_1199.png
"""

import bpy
import bmesh
import math
import os
import sys
import time
import logging
import random
from mathutils import Vector, noise

OUT_DIR = "/home/jovyan/boids_v3"
DEPTH_DIR = os.path.join(OUT_DIR, "depth")
os.makedirs(DEPTH_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [BOIDS_V3] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(OUT_DIR, "progress.log")),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

TOTAL_FRAMES = 1200
NUM_AGENTS = 200
RES = 512

WORLD_X = (-8, 8)
WORLD_Z = (-6, 6)
WATER_Y = 0.0

# Canopy zone: y=1 to y=3 — where trees and birds share space
CANOPY_LOW = 1.0
CANOPY_HIGH = 3.5

random.seed(42)


class Agent:
    def __init__(self, idx, pos, vel):
        self.idx = idx
        self.pos = pos.copy()
        self.vel = vel.copy()
        self.morph = 0.0  # 0=fish, 1=bird

    def fish_scale(self):
        return Vector((0.4, 0.1, 0.08))

    def bird_scale(self):
        return Vector((0.15, 0.05, 0.3))

    def current_scale(self):
        fs = self.fish_scale()
        bs = self.bird_scale()
        return fs.lerp(bs, self.morph)


def simulate_all_frames():
    log.info("Simulating %d agents, %d frames", NUM_AGENTS, TOTAL_FRAMES)
    
    agents = []
    for i in range(NUM_AGENTS):
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(5, 8)
        px = math.cos(angle) * radius
        py = random.uniform(-5, -1)
        pz = math.sin(angle) * random.uniform(1, 4)
        vx = -px * 0.02 + random.uniform(-0.01, 0.01)
        vy = random.uniform(-0.005, 0.005)
        vz = -pz * 0.01 + random.uniform(-0.01, 0.01)
        agents.append(Agent(i, Vector((px, py, pz)), Vector((vx, vy, vz))))

    all_frames = []

    for frame in range(TOTAL_FRAMES):
        # Phase determination
        if frame < 200:
            phase = "fish_school"
            t = frame / 200.0
            cohesion, sep, align, speed = 0.8, 1.0, 0.6, 0.06
            target_y_range = (-4, -1)
        elif frame < 350:
            phase = "rising"
            t = (frame - 200) / 150.0
            cohesion, sep, align, speed = 0.7, 0.8, 0.5, 0.05
            target_y_range = (-3 + t * 3, -0.5 + t * 0.5)
        elif frame < 500:
            phase = "crossing"
            t = (frame - 350) / 150.0
            cohesion, sep, align, speed = 0.5, 0.6, 0.4, 0.05
            target_y_range = (-1 + t * 2, 1 + t * 2)
        elif frame < 700:
            phase = "canopy_murmuration"
            t = (frame - 500) / 200.0
            cohesion, sep, align, speed = 0.4, 0.5, 0.3, 0.06
            target_y_range = (CANOPY_LOW, CANOPY_HIGH)
        elif frame < 900:
            phase = "diving"
            t = (frame - 700) / 200.0
            cohesion, sep, align, speed = 0.5, 0.6, 0.4, 0.06
            target_y_range = (CANOPY_HIGH - t * (CANOPY_HIGH + 2), CANOPY_LOW - t * (CANOPY_LOW + 1))
        else:
            phase = "fish_school_return"
            t = (frame - 900) / 300.0
            cohesion, sep, align, speed = 0.8, 1.0, 0.6, 0.06
            target_y_range = (-4, -1)

        sep_dist = 0.6
        nbr_dist = 4.0

        for a in agents:
            # Boids forces
            coh_vec = Vector((0, 0, 0))
            sep_vec = Vector((0, 0, 0))
            ali_vec = Vector((0, 0, 0))
            n_neighbors = 0

            for b in agents:
                if b.idx == a.idx:
                    continue
                diff = b.pos - a.pos
                dist = diff.length
                if dist < nbr_dist and dist > 0.01:
                    n_neighbors += 1
                    coh_vec += b.pos
                    ali_vec += b.vel
                    if dist < sep_dist:
                        sep_vec -= diff.normalized() * (sep_dist - dist)

            if n_neighbors > 0:
                coh_vec = (coh_vec / n_neighbors - a.pos) * cohesion * 0.01
                ali_vec = (ali_vec / n_neighbors - a.vel) * align * 0.1
                sep_vec *= sep * 0.05

            # Y target force — guide agents to correct vertical zone
            target_y = (target_y_range[0] + target_y_range[1]) / 2
            y_force = (target_y - a.pos.y) * 0.005
            
            # Noise for organic feel
            noise_val = noise.noise(a.pos * 0.3 + Vector((frame * 0.01, 0, 0)))
            noise_vec = Vector((noise_val, noise_val * 0.5, noise_val * 0.7)) * 0.003

            # Update velocity
            a.vel += coh_vec + sep_vec + ali_vec + Vector((0, y_force, 0)) + noise_vec
            
            # Speed limit
            if a.vel.length > speed:
                a.vel = a.vel.normalized() * speed

            # Update position
            a.pos += a.vel

            # Boundary wrapping (X and Z)
            if a.pos.x < WORLD_X[0]: a.pos.x = WORLD_X[1]
            if a.pos.x > WORLD_X[1]: a.pos.x = WORLD_X[0]
            if a.pos.z < WORLD_Z[0]: a.pos.z = WORLD_Z[1]
            if a.pos.z > WORLD_Z[1]: a.pos.z = WORLD_Z[0]

            # Morph based on Y position
            if a.pos.y < -0.3:
                a.morph = max(0, a.morph - 0.03)
            elif a.pos.y > 0.3:
                a.morph = min(1, a.morph + 0.03)

            # In canopy phase: agents near bottom move slowly (tree-like)
            if phase == "canopy_murmuration":
                canopy_t = (a.pos.y - CANOPY_LOW) / (CANOPY_HIGH - CANOPY_LOW)
                canopy_t = max(0, min(1, canopy_t))
                # Lower agents = slower = more tree-like
                slowdown = 1.0 - (1.0 - canopy_t) * 0.8
                a.vel *= slowdown

        # Store frame state
        frame_state = [(Vector(a.pos), float(a.morph), Vector(a.current_scale())) for a in agents]
        all_frames.append(frame_state)

        if frame % 100 == 0:
            avg_y = sum(a.pos.y for a in agents) / NUM_AGENTS
            log.info("Frame %d/%d phase=%s avg_y=%.2f", frame, TOTAL_FRAMES, phase, avg_y)

    log.info("Simulation complete")
    return all_frames


def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'CUDA'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = True
    scene.render.resolution_x = RES
    scene.render.resolution_y = RES
    scene.cycles.samples = 16
    
    # Camera — side view
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 16
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = (0, 0, 20)
    cam.rotation_euler = (0, 0, 0)
    scene.camera = cam
    
    # Adjust camera for side view (looking from Z toward -Z, X is horizontal, Y is vertical)
    cam.location = (0, 0, 20)
    cam.rotation_euler = (0, 0, 0)
    
    # Depth pass setup
    scene.use_nodes = True
    tree = scene.node_tree
    for n in tree.nodes:
        tree.nodes.remove(n)
    
    rl = tree.nodes.new('CompositorNodeRLayers')
    scene.view_layers[0].use_pass_z = True
    
    normalize = tree.nodes.new('CompositorNodeNormalize')
    invert = tree.nodes.new('CompositorNodeInvert')
    output = tree.nodes.new('CompositorNodeOutputFile')
    output.base_path = DEPTH_DIR
    output.format.file_format = 'PNG'
    output.format.color_depth = '8'
    output.format.color_mode = 'BW'
    
    tree.links.new(rl.outputs['Depth'], normalize.inputs[0])
    tree.links.new(normalize.outputs[0], invert.inputs['Color'])
    tree.links.new(invert.outputs[0], output.inputs[0])
    
    # Also add a waterline plane for visual reference in depth
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    plane = bpy.context.object
    plane.name = "Waterline"
    plane.scale = (10, 0.02, 1)
    
    return scene, cam, output


def render_frames(all_frames, scene, cam, output_node):
    log.info("Rendering %d frames at %dx%d", len(all_frames), RES, RES)
    
    # Create agent mesh template
    mesh = bpy.data.meshes.new("AgentMesh")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=4, v_segments=3, radius=0.5)
    bm.to_mesh(mesh)
    bm.free()
    
    # Create agent objects
    agent_objs = []
    for i in range(NUM_AGENTS):
        obj = bpy.data.objects.new(f"Agent_{i}", mesh.copy())
        bpy.context.collection.objects.link(obj)
        agent_objs.append(obj)
    
    t0 = time.time()
    for frame_idx, frame_state in enumerate(all_frames):
        # Update agent positions and scales
        for i, (pos, morph, scale) in enumerate(frame_state):
            obj = agent_objs[i]
            # In Blender: X=horizontal, Y=depth(into screen), Z=up
            # Our sim: X=horizontal, Y=vertical(up/down), Z=depth
            obj.location = (pos.x, pos.z, pos.y)
            obj.scale = (scale.x, scale.z, scale.y)
            
            # Rotate to face velocity direction (approximate)
            if i < len(frame_state) - 1:
                obj.rotation_euler = (0, 0, math.atan2(pos.y, pos.x + 0.001))
        
        # Set output path for this frame
        output_node.file_slots[0].path = f"frame_{frame_idx:04d}"
        scene.frame_set(frame_idx)
        
        bpy.ops.render.render(write_still=False)
        
        if frame_idx % 100 == 0:
            elapsed = time.time() - t0
            rate = (frame_idx + 1) / elapsed if elapsed > 0 else 0
            log.info("Rendered %d/%d (%.1f fps, %.0fs elapsed)", frame_idx, len(all_frames), rate, elapsed)
    
    elapsed = time.time() - t0
    log.info("Rendering complete: %d frames in %.1fs (%.2f fps)", len(all_frames), elapsed, len(all_frames)/elapsed)


# Main
log.info("=" * 60)
log.info("BOIDS V3 — Tree-Murmuration Cycle")
log.info("=" * 60)

all_frames = simulate_all_frames()
scene, cam, output_node = setup_scene()
render_frames(all_frames, scene, cam, output_node)

log.info("DONE — depth maps at %s", DEPTH_DIR)
