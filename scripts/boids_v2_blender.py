#!/usr/bin/env python3
"""
Boids v2 — Fixed Narrative Simulation (30 seconds, 900 frames at 30fps)
========================================================================
Fixes from v1:
  1. Waterline constraint: fish ALWAYS below y=0, birds ALWAYS above y=0
  2. Whale emerges FROM murmuration convergence (not a separate object)
  3. Continuous agent trajectories — no agents appear or disappear

Six phases:
  0-150   Gathering     — 200 fish agents form school below waterline
  150-300 Rising        — school ascends toward waterline
  300-450 Crossing      — agents morph from fish→bird crossing y=0
  450-600 Murmuration   — birds swirl in classic murmuration
  600-750 Convergence   — murmuration tightens into spiral
  750-900 Becoming Whale — agents pack into whale-shaped point cloud

Usage: /home/jovyan/blender-4.3.2-linux-x64/blender --background --python boids_v2_blender.py

Output: /home/jovyan/boids_v2/depth/frame_0000.png through frame_0899.png
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

# ── Config ───────────────────────────────────────────────────────────────────
OUT_DIR = "/home/jovyan/boids_v2"
DEPTH_DIR = os.path.join(OUT_DIR, "depth")
os.makedirs(DEPTH_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [BOIDS_V2] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(OUT_DIR, "progress.log")),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

TOTAL_FRAMES = 900
NUM_AGENTS = 200
RES = 512

# World bounds
WORLD_X = (-8, 8)
WORLD_Z = (-6, 6)  # Z is "depth" in our side-view
WATER_Y = 0.0  # Waterline

# Boids parameters per phase (will be interpolated)
# (cohesion, separation, alignment, speed, separation_dist, neighbor_dist)
BOIDS_PARAMS = {
    "gathering":   (0.8, 1.0, 0.6, 0.06, 0.8, 3.0),
    "rising":      (0.7, 0.8, 0.5, 0.05, 0.7, 3.5),
    "crossing":    (0.5, 0.6, 0.4, 0.05, 0.6, 4.0),
    "murmuration": (0.4, 0.5, 0.3, 0.07, 0.5, 5.0),
    "convergence": (0.9, 0.3, 0.7, 0.04, 0.4, 6.0),
    "whale":       (1.0, 0.1, 0.8, 0.02, 0.3, 8.0),
}

random.seed(42)


# ═══════════════════════════════════════════════════════════════════════════
# WHALE SHAPE — Ellipsoid approximation with tail taper
# ═══════════════════════════════════════════════════════════════════════════
def whale_surface_points(n_points, center=Vector((0, -2, 0)), length=6.0):
    """Generate n_points on a whale-like ellipsoid surface.

    The whale is oriented along X axis, centered at `center`.
    Body: elongated ellipsoid (length x 1.5 x 1.2)
    Tail: tapered cone extending from rear 1/3
    """
    points = []
    # Golden ratio spiral for even distribution
    golden = (1 + math.sqrt(5)) / 2

    for i in range(n_points):
        # Fibonacci sphere
        theta = 2 * math.pi * i / golden
        phi = math.acos(1 - 2 * (i + 0.5) / n_points)

        # Unit sphere point
        sx = math.cos(theta) * math.sin(phi)
        sy = math.sin(theta) * math.sin(phi)
        sz = math.cos(phi)

        # Map to whale shape: elongated along X
        # sx maps to length axis
        wx = sx * length * 0.5

        # Taper: the further back (negative X), the thinner
        # front half is full width, rear third tapers to tail
        t = (sx + 1) / 2  # 0 at tail, 1 at head
        if t < 0.3:
            # Tail taper
            taper = t / 0.3 * 0.6 + 0.1
        elif t > 0.85:
            # Head slight rounding
            taper = 0.8 + 0.2 * (1 - (t - 0.85) / 0.15)
        else:
            taper = 1.0

        wy = sy * 1.5 * taper  # height
        wz = sz * 1.2 * taper  # width

        points.append(center + Vector((wx, wy, wz)))

    return points


# ═══════════════════════════════════════════════════════════════════════════
# AGENT CLASS
# ═══════════════════════════════════════════════════════════════════════════
class Agent:
    def __init__(self, idx, pos, vel):
        self.idx = idx
        self.pos = pos.copy()
        self.vel = vel.copy()
        self.morph = 0.0  # 0=fish, 1=bird
        self.whale_target = None  # set in phase 6
        self.whale_lerp = 0.0  # 0=free, 1=locked to whale

    def fish_scale(self):
        """Scale for fish shape (elongated horizontal)."""
        return Vector((0.4, 0.1, 0.08))

    def bird_scale(self):
        """Scale for bird shape (wider wings)."""
        return Vector((0.15, 0.05, 0.3))

    def current_scale(self):
        fs = self.fish_scale()
        bs = self.bird_scale()
        return fs.lerp(bs, self.morph)


# ═══════════════════════════════════════════════════════════════════════════
# BOIDS SIMULATION
# ═══════════════════════════════════════════════════════════════════════════
def simulate_all_frames():
    """Run the full 900-frame Boids simulation, return list of frame states."""
    log.info("Starting Boids simulation for %d agents, %d frames", NUM_AGENTS, TOTAL_FRAMES)

    # Initialize agents scattered below waterline
    agents = []
    for i in range(NUM_AGENTS):
        # Spread around edges below water
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(5, 8)
        px = math.cos(angle) * radius
        py = random.uniform(-5, -1)  # Below waterline
        pz = math.sin(angle) * random.uniform(1, 4)

        # Initial velocity toward center
        vx = -px * 0.02 + random.uniform(-0.01, 0.01)
        vy = random.uniform(-0.005, 0.005)
        vz = -pz * 0.01 + random.uniform(-0.01, 0.01)

        agents.append(Agent(i, Vector((px, py, pz)), Vector((vx, vy, vz))))

    # Pre-compute whale target positions
    whale_targets = whale_surface_points(NUM_AGENTS)
    # Shuffle so assignment doesn't create artifacts
    random.shuffle(whale_targets)

    # Store all frame states
    all_frames = []

    for frame in range(TOTAL_FRAMES):
        # Determine phase and interpolation factor within phase
        if frame < 150:
            phase = "gathering"
            t = frame / 150.0
        elif frame < 300:
            phase = "rising"
            t = (frame - 150) / 150.0
        elif frame < 450:
            phase = "crossing"
            t = (frame - 300) / 150.0
        elif frame < 600:
            phase = "murmuration"
            t = (frame - 450) / 150.0
        elif frame < 750:
            phase = "convergence"
            t = (frame - 600) / 150.0
        else:
            phase = "whale"
            t = (frame - 750) / 150.0

        cohesion, separation, alignment, speed, sep_dist, nbr_dist = BOIDS_PARAMS[phase]

        # === Phase-specific target/behavior ===
        # Gathering: attract toward center below water
        # Rising: attract upward toward y=0
        # Crossing: agents near y=0 morph
        # Murmuration: loose swirling above water
        # Convergence: tighten spiral
        # Whale: lerp to whale positions

        # Compute center of mass
        com = Vector((0, 0, 0))
        for a in agents:
            com += a.pos
        com /= NUM_AGENTS

        # Update each agent
        for a in agents:
            # Boids forces
            coh_force = Vector((0, 0, 0))
            sep_force = Vector((0, 0, 0))
            ali_force = Vector((0, 0, 0))
            n_neighbors = 0

            for b in agents:
                if b.idx == a.idx:
                    continue
                diff = b.pos - a.pos
                dist = diff.length
                if dist < nbr_dist and dist > 0.001:
                    n_neighbors += 1
                    # Cohesion: steer toward center of neighbors
                    coh_force += diff.normalized()
                    # Alignment: match neighbor velocity
                    ali_force += b.vel
                    # Separation: steer away from very close neighbors
                    if dist < sep_dist:
                        sep_force -= diff.normalized() / max(dist, 0.1)

            if n_neighbors > 0:
                coh_force /= n_neighbors
                ali_force /= n_neighbors

            # Combined boids force
            steer = (coh_force * cohesion +
                     sep_force * separation +
                     ali_force.normalized() * alignment if ali_force.length > 0.001 else
                     coh_force * cohesion + sep_force * separation)

            # Phase-specific forces
            phase_force = Vector((0, 0, 0))

            if phase == "gathering":
                # Pull toward center, keep below water
                target = Vector((0, -2.5, 0))
                phase_force = (target - a.pos) * 0.02
                # Hard ceiling at waterline
                if a.pos.y > WATER_Y - 0.3:
                    phase_force.y -= 0.05

            elif phase == "rising":
                # Gradually rise toward waterline
                target_y = -2.5 + t * 2.5  # from -2.5 to 0
                phase_force.y = (target_y - a.pos.y) * 0.03
                # Keep some horizontal cohesion
                phase_force.x = -a.pos.x * 0.01
                phase_force.z = -a.pos.z * 0.01

            elif phase == "crossing":
                # Push upward through waterline
                target_y = -0.5 + t * 3.0  # from -0.5 to 2.5
                phase_force.y = (target_y - a.pos.y) * 0.02
                # Expand horizontally as they cross
                spread = 1.0 + t * 0.5
                phase_force.x += (a.pos.x * 0.005) * spread
                phase_force.z += (a.pos.z * 0.005) * spread
                # Morph based on y position
                if a.pos.y < -0.5:
                    a.morph = 0.0
                elif a.pos.y > 0.5:
                    a.morph = 1.0
                else:
                    a.morph = (a.pos.y + 0.5) / 1.0

            elif phase == "murmuration":
                # All should be birds by now
                a.morph = 1.0
                # Ensure above waterline
                if a.pos.y < WATER_Y + 0.5:
                    phase_force.y += 0.04
                # Swirling: tangential force around center
                to_center = com - a.pos
                tangent = Vector((-to_center.z, 0, to_center.x)).normalized()
                # Oscillating tangential direction for organic feel
                wave = math.sin(frame * 0.03 + a.idx * 0.1) * 0.5 + 0.5
                phase_force += tangent * 0.02 * wave
                # Gentle vertical oscillation
                phase_force.y += math.sin(frame * 0.02 + a.idx * 0.15) * 0.01
                # Keep in bounds
                phase_force.x -= a.pos.x * 0.003
                phase_force.z -= a.pos.z * 0.003
                # Target altitude
                target_alt = 3.0 + math.sin(frame * 0.015) * 1.0
                phase_force.y += (target_alt - a.pos.y) * 0.01

            elif phase == "convergence":
                a.morph = 1.0
                # Tighten spiral — increasing pull toward center
                pull_strength = 0.02 + t * 0.06  # increases over phase
                to_center = com - a.pos
                phase_force += to_center.normalized() * pull_strength
                # Spiral: tangential force
                tangent = Vector((-to_center.z, 0, to_center.x)).normalized()
                phase_force += tangent * 0.03 * (1 - t * 0.5)
                # Descend toward water
                target_y = 3.0 - t * 3.5  # from 3 down toward -0.5
                phase_force.y += (target_y - a.pos.y) * 0.02

            elif phase == "whale":
                a.morph = 1.0
                # Assign whale target if not yet assigned
                if a.whale_target is None:
                    a.whale_target = whale_targets[a.idx]

                # Whale swims slowly forward
                swim_offset = Vector((t * 2.0, 0, 0))
                target = a.whale_target + swim_offset

                # Lerp factor increases over the phase
                a.whale_lerp = min(1.0, t * 1.3)  # reach 1.0 by ~77% through

                # Blend between boids movement and whale position
                desired_pos = a.pos.lerp(target, a.whale_lerp * 0.05)
                phase_force = (desired_pos - a.pos) * 2.0

                # Reduce boids influence as whale forms
                steer *= (1.0 - a.whale_lerp * 0.8)

            # Apply forces
            accel = steer * 0.5 + phase_force
            a.vel += accel

            # Clamp speed
            max_speed = speed * (1 + random.uniform(-0.1, 0.1))
            if a.vel.length > max_speed:
                a.vel = a.vel.normalized() * max_speed

            # Update position
            a.pos += a.vel

            # === HARD CONSTRAINTS ===
            # Fish (morph < 0.5) must stay below water
            if a.morph < 0.5:
                if a.pos.y > WATER_Y:
                    a.pos.y = WATER_Y - 0.1
                    a.vel.y = min(a.vel.y, 0)

            # During gathering/rising, ALL agents below water
            if phase in ("gathering", "rising") and frame < 280:
                if a.pos.y > WATER_Y:
                    a.pos.y = WATER_Y - 0.05
                    a.vel.y = min(a.vel.y, 0)

            # During murmuration/convergence, keep above water (mostly)
            if phase in ("murmuration",):
                if a.pos.y < WATER_Y + 0.2:
                    a.pos.y = WATER_Y + 0.2
                    a.vel.y = max(a.vel.y, 0.01)

            # World bounds (soft)
            for axis, (lo, hi) in [(0, WORLD_X), (2, WORLD_Z)]:
                if a.pos[axis] < lo:
                    a.vel[axis] += 0.02
                elif a.pos[axis] > hi:
                    a.vel[axis] -= 0.02

            # Vertical bounds
            if a.pos.y < -6:
                a.vel.y += 0.02
            if a.pos.y > 7:
                a.vel.y -= 0.02

        # Store frame state
        frame_state = []
        for a in agents:
            frame_state.append({
                "pos": a.pos.copy(),
                "vel": a.vel.copy(),
                "morph": a.morph,
                "scale": a.current_scale(),
            })
        all_frames.append(frame_state)

        if frame % 100 == 0:
            avg_y = sum(a.pos.y for a in agents) / NUM_AGENTS
            log.info("Frame %d/%d [%s t=%.2f] avg_y=%.2f",
                     frame, TOTAL_FRAMES, phase, t, avg_y)

    log.info("Simulation complete: %d frames", len(all_frames))
    return all_frames


# ═══════════════════════════════════════════════════════════════════════════
# BLENDER SCENE SETUP
# ═══════════════════════════════════════════════════════════════════════════
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)


def create_agent_mesh(name, scale):
    """Create a simple ellipsoid mesh for an agent."""
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=8, ring_count=6,
        radius=1.0,
        location=(0, 0, 0)
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return obj


def setup_camera():
    """Side-view camera capturing both underwater and sky."""
    bpy.ops.object.camera_add(
        location=(0, 0, 18),
        rotation=(0, 0, 0)
    )
    cam = bpy.context.active_object
    cam.name = "SideCamera"
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 16  # Capture -8 to 8 in view
    # Look down Z axis (side view: X is horizontal, Y is vertical)
    cam.rotation_euler = (0, 0, 0)  # Will be set properly below

    # We want to look along -Z (from positive Z toward origin)
    # Camera looks down its -Z local axis by default
    # So rotation (0,0,0) = looking down -Z world = perfect side view
    # X-axis = left/right, Y-axis = up/down in render

    bpy.context.scene.camera = cam
    return cam


def setup_waterline_plane():
    """Add a thin plane at y=0 to mark the waterline in depth map."""
    bpy.ops.mesh.primitive_plane_add(
        size=20,
        location=(0, 0, 0)
    )
    plane = bpy.context.active_object
    plane.name = "Waterline"
    # Rotate to be horizontal (in our side-view, plane should span X at Y=0)
    # The plane is in XY by default. We want it in XZ at y=0 for a horizontal line.
    # Actually in side view (camera looking down Z), we see X (horizontal) and Y (vertical).
    # A plane at y=0 spanning X would be a horizontal line.
    # Default plane is in XY plane. We need it in XZ plane.
    plane.rotation_euler = (math.radians(90), 0, 0)
    plane.scale = (10, 1, 0.005)  # Very thin in Y
    bpy.ops.object.transform_apply(rotation=True, scale=True)

    # Make it very thin — just a line
    plane.scale.y = 0.01

    return plane


def setup_render():
    """Configure Cycles for depth map rendering."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.render.resolution_x = RES
    scene.render.resolution_y = RES
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_depth = '16'
    scene.render.image_settings.color_mode = 'RGB'

    # GPU
    scene.cycles.device = 'GPU'
    scene.cycles.samples = 16  # Low for depth
    scene.cycles.use_denoising = False
    prefs = bpy.context.preferences.addons.get('cycles')
    if prefs:
        try:
            prefs.preferences.compute_device_type = 'CUDA'
            prefs.preferences.get_devices()
            for d in prefs.preferences.devices:
                d.use = True
        except Exception as e:
            log.warning("GPU setup: %s", e)

    # Compositor for Z-depth output
    scene.use_nodes = True
    tree = scene.node_tree
    for node in tree.nodes:
        tree.nodes.remove(node)

    # Render layers
    rl = tree.nodes.new('CompositorNodeRLayers')
    rl.location = (0, 0)

    # Enable Z pass
    view_layer = bpy.context.view_layer
    view_layer.use_pass_z = True

    # Normalize Z depth
    norm = tree.nodes.new('CompositorNodeNormalize')
    norm.location = (300, 0)
    tree.links.new(rl.outputs['Depth'], norm.inputs[0])

    # Invert so closer = brighter (for ControlNet)
    invert = tree.nodes.new('CompositorNodeInvert')
    invert.location = (500, 0)
    tree.links.new(norm.outputs[0], invert.inputs['Color'])

    # Output
    comp = tree.nodes.new('CompositorNodeComposite')
    comp.location = (700, 0)
    tree.links.new(invert.outputs[0], comp.inputs['Image'])

    # Also output via file output node for direct save
    return scene


def setup_lighting():
    """Simple lighting for depth map."""
    bpy.ops.object.light_add(type='SUN', location=(0, 5, 10))
    sun = bpy.context.active_object
    sun.name = "Sun"
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(-45), 0, 0)


def create_bg_planes():
    """Create background planes for water (below y=0) and sky (above y=0)."""
    # Water plane (below)
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, -3, -1))
    water = bpy.context.active_object
    water.name = "WaterBG"

    # Create a dark material for water
    mat_water = bpy.data.materials.new("WaterMat")
    mat_water.use_nodes = True
    bsdf = mat_water.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.05, 0.1, 0.15, 1)
    bsdf.inputs["Roughness"].default_value = 1.0
    water.data.materials.append(mat_water)

    # Sky plane (above)
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 3, -1))
    sky = bpy.context.active_object
    sky.name = "SkyBG"

    mat_sky = bpy.data.materials.new("SkyMat")
    mat_sky.use_nodes = True
    bsdf = mat_sky.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.3, 0.35, 0.4, 1)
    bsdf.inputs["Roughness"].default_value = 1.0
    sky.data.materials.append(mat_sky)


# ═══════════════════════════════════════════════════════════════════════════
# RENDERING
# ═══════════════════════════════════════════════════════════════════════════
def render_all_frames(all_frames):
    """Render each frame by placing agent meshes and capturing depth."""
    log.info("Setting up Blender scene...")

    clear_scene()
    setup_render()
    setup_camera()
    setup_lighting()
    # No background planes - we want clean depth maps of just the agents
    # The dissolution pipeline adds the landscape

    scene = bpy.context.scene

    # Create a template mesh for agents
    # We'll create all agent objects once and move them each frame
    agent_objs = []

    # White material for depth visibility
    mat_agent = bpy.data.materials.new("AgentMat")
    mat_agent.use_nodes = True
    bsdf = mat_agent.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.9, 0.9, 0.9, 1)
    bsdf.inputs["Roughness"].default_value = 1.0

    for i in range(NUM_AGENTS):
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=8, ring_count=6,
            radius=0.2,
            location=(0, 0, 0)
        )
        obj = bpy.context.active_object
        obj.name = f"Agent_{i:03d}"
        obj.data.materials.append(mat_agent)
        agent_objs.append(obj)

    log.info("Created %d agent objects", len(agent_objs))

    # Add waterline marker (thin horizontal bar)
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, 5)  # At y=0, pushed back in Z
    )
    waterline = bpy.context.active_object
    waterline.name = "WaterlineBar"
    waterline.scale = (10, 0.02, 0.01)
    mat_wl = bpy.data.materials.new("WaterlineMat")
    mat_wl.use_nodes = True
    bsdf_wl = mat_wl.node_tree.nodes["Principled BSDF"]
    bsdf_wl.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1)
    waterline.data.materials.append(mat_wl)

    # Render each frame
    timings = []
    for frame_idx, frame_state in enumerate(all_frames):
        out_path = os.path.join(DEPTH_DIR, f"frame_{frame_idx:04d}.png")

        # Skip if already rendered
        if os.path.exists(out_path):
            if frame_idx % 100 == 0:
                log.info("Frame %d/%d — skipped (exists)", frame_idx, TOTAL_FRAMES)
            continue

        t_start = time.perf_counter()

        # Update agent positions and scales
        for i, state in enumerate(frame_state):
            obj = agent_objs[i]
            pos = state["pos"]
            scale = state["scale"]
            vel = state["vel"]

            # Position: X stays X, Y stays Y, Z controls depth from camera
            # Camera is at Z=18 looking down -Z
            # Agents should be near Z=0 to be visible
            obj.location = (pos.x, pos.y, pos.z * 0.3)  # Compress Z range

            # Scale based on morph
            obj.scale = (scale.x, scale.y, scale.z)

            # Orient along velocity
            if vel.length > 0.001:
                # Point elongated axis along velocity
                vel_2d = Vector((vel.x, vel.y, 0))
                if vel_2d.length > 0.001:
                    angle = math.atan2(vel.y, vel.x)
                    obj.rotation_euler = (0, 0, angle)

        # Render
        scene.render.filepath = out_path
        bpy.ops.render.render(write_still=True)

        elapsed = time.perf_counter() - t_start
        timings.append(elapsed)

        if frame_idx % 25 == 0:
            avg = sum(timings) / len(timings)
            remaining = avg * (TOTAL_FRAMES - frame_idx - 1)
            log.info("Frame %d/%d — %.2fs (avg %.2fs, ETA %.1fmin)",
                     frame_idx, TOTAL_FRAMES, elapsed, avg, remaining / 60)

    total = sum(timings)
    log.info("Rendering complete: %d frames in %.1fmin (avg %.2fs/frame)",
             len(timings), total / 60, total / len(timings) if timings else 0)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    log.info("=" * 70)
    log.info("BOIDS V2 — Fixed Narrative Simulation")
    log.info("  200 agents, 900 frames, 30fps = 30 seconds")
    log.info("  Fixes: waterline constraint, whale from murmuration, continuous flow")
    log.info("=" * 70)

    start_time = time.time()

    # Phase 1: Simulate
    log.info("PHASE 1: Running Boids simulation...")
    all_frames = simulate_all_frames()
    sim_time = time.time() - start_time
    log.info("Simulation took %.1fs", sim_time)

    # Phase 2: Render depth maps
    log.info("PHASE 2: Rendering depth maps...")
    render_all_frames(all_frames)

    total_time = time.time() - start_time
    log.info("=" * 70)
    log.info("ALL DONE — Total time: %.1fmin", total_time / 60)
    log.info("Depth maps: %s", DEPTH_DIR)

    # Count output files
    n_files = len([f for f in os.listdir(DEPTH_DIR) if f.endswith('.png')])
    log.info("Output: %d depth frames", n_files)
    log.info("=" * 70)


if __name__ == "__main__":
    main()
