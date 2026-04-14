#!/usr/bin/env python3
"""StyleGAN2 Latent Space Explorer — Gradio UI for macOS (MPS/CPU)

Usage:
    conda activate myenv
    python scripts/latent_explorer.py [--pkl models/fish-network-snapshot-001000.pkl]

Opens a browser UI with:
  - Seed browsing + truncation control
  - Interpolation between two seeds (Z-space and W-space SLERP)
  - Style mixing between two seeds at different layer cutoffs
  - Random walk animation through latent space
"""

import argparse
import glob
import os
import sys
import time

import gradio as gr
import numpy as np
import torch
from PIL import Image

# Add stylegan2-ada-pytorch to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
STYLEGAN_DIR = os.path.join(REPO_DIR, "stylegan2")
sys.path.insert(0, STYLEGAN_DIR)

import dnnlib
import legacy

# ---------------------------------------------------------------------------
# Device selection
# ---------------------------------------------------------------------------

def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")

DEVICE = get_device()
print(f"Using device: {DEVICE}")

# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

G = None  # global generator
MODEL_PATH = None

def load_model(pkl_path: str):
    global G, MODEL_PATH
    pkl_path = pkl_path.strip()
    if not os.path.isabs(pkl_path):
        pkl_path = os.path.join(REPO_DIR, pkl_path)
    if not os.path.exists(pkl_path):
        return f"File not found: {pkl_path}"
    try:
        with open(pkl_path, "rb") as f:
            data = legacy.load_network_pkl(f)
        # .float() needed for MPS — it doesn't support float64
        G = data["G_ema"].to(DEVICE).eval().float()
        MODEL_PATH = pkl_path
        # Warmup: first MPS inference compiles Metal kernels (~10s)
        with torch.no_grad():
            z = torch.randn(1, G.z_dim, device=DEVICE)
            w = G.mapping(z, None, truncation_psi=0.7)
            _ = G.synthesis(w, noise_mode="const")
        return f"Loaded: {os.path.basename(pkl_path)}  |  res={G.img_resolution}  z_dim={G.z_dim}  device={DEVICE}  (warmed up)"
    except Exception as e:
        return f"Error loading: {e}"

# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------

def seed_to_z(seed: int):
    return torch.from_numpy(np.random.RandomState(int(seed)).randn(1, G.z_dim).astype(np.float32)).to(DEVICE)

def z_to_w(z, truncation_psi: float = 0.7):
    label = torch.zeros([1, G.c_dim], device=DEVICE) if G.c_dim > 0 else None
    return G.mapping(z, label, truncation_psi=truncation_psi)

def w_to_image(w):
    img = G.synthesis(w, noise_mode="const")
    img = (img.clamp(-1, 1) + 1) / 2 * 255
    img = img[0].permute(1, 2, 0).to("cpu", torch.uint8).numpy()
    return Image.fromarray(img)

def slerp(a, b, t):
    a_norm = a / a.norm(dim=-1, keepdim=True)
    b_norm = b / b.norm(dim=-1, keepdim=True)
    omega = torch.acos((a_norm * b_norm).sum(dim=-1, keepdim=True).clamp(-1, 1))
    so = torch.sin(omega)
    # Fall back to lerp when vectors are nearly parallel
    mask = (so.abs() < 1e-6).float()
    res = (torch.sin((1 - t) * omega) / so) * a + (torch.sin(t * omega) / so) * b
    res_lerp = (1 - t) * a + t * b
    return res * (1 - mask) + res_lerp * mask

# ---------------------------------------------------------------------------
# Tab 1: Seed Explorer
# ---------------------------------------------------------------------------

def generate_single(seed, truncation_psi):
    if G is None:
        return None, "Load a model first"
    t0 = time.time()
    with torch.no_grad():
        z = seed_to_z(seed)
        w = z_to_w(z, truncation_psi)
        img = w_to_image(w)
    ms = (time.time() - t0) * 1000
    return img, f"seed={int(seed)}  psi={truncation_psi:.2f}  {ms:.0f}ms"

def generate_grid(base_seed, truncation_psi):
    """Generate a 3x3 grid of neighboring seeds."""
    if G is None:
        return None
    images = []
    seeds = [int(base_seed) + i for i in range(9)]
    with torch.no_grad():
        for s in seeds:
            z = seed_to_z(s)
            w = z_to_w(z, truncation_psi)
            images.append(w_to_image(w))
    # Compose 3x3 grid
    res = G.img_resolution
    grid = Image.new("RGB", (res * 3, res * 3))
    for i, img in enumerate(images):
        grid.paste(img, ((i % 3) * res, (i // 3) * res))
    return grid

# ---------------------------------------------------------------------------
# Tab 2: Interpolation
# ---------------------------------------------------------------------------

def interpolate(seed_a, seed_b, steps, truncation_psi, space):
    if G is None:
        return []
    frames = []
    with torch.no_grad():
        z_a = seed_to_z(seed_a)
        z_b = seed_to_z(seed_b)
        if space == "W (smoother)":
            w_a = z_to_w(z_a, truncation_psi)
            w_b = z_to_w(z_b, truncation_psi)
            for i in range(int(steps)):
                t = i / max(int(steps) - 1, 1)
                w = slerp(w_a, w_b, t)
                frames.append(w_to_image(w))
        else:  # Z space
            for i in range(int(steps)):
                t = i / max(int(steps) - 1, 1)
                z = slerp(z_a, z_b, t)
                w = z_to_w(z, truncation_psi)
                frames.append(w_to_image(w))
    return frames

# ---------------------------------------------------------------------------
# Tab 3: Style Mixing
# ---------------------------------------------------------------------------

def style_mix(seed_a, seed_b, cutoff_layer, truncation_psi):
    if G is None:
        return None, None, None, ""
    with torch.no_grad():
        w_a = z_to_w(seed_to_z(seed_a), truncation_psi)
        w_b = z_to_w(seed_to_z(seed_b), truncation_psi)

        # Mix: take coarse layers from A, fine layers from B
        cutoff = int(cutoff_layer)
        w_mix = w_a.clone()
        w_mix[:, cutoff:, :] = w_b[:, cutoff:, :]

        img_a = w_to_image(w_a)
        img_b = w_to_image(w_b)
        img_mix = w_to_image(w_mix)
    num_layers = w_a.shape[1]
    info = f"Layers 0-{cutoff-1} from seed {int(seed_a)}, layers {cutoff}-{num_layers-1} from seed {int(seed_b)}"
    return img_a, img_b, img_mix, info

# ---------------------------------------------------------------------------
# Tab 4: Random Walk
# ---------------------------------------------------------------------------

def random_walk(seed, steps, step_size, truncation_psi):
    if G is None:
        return []
    frames = []
    rng = np.random.RandomState(int(seed))
    z = torch.from_numpy(rng.randn(1, G.z_dim)).to(DEVICE).float()
    with torch.no_grad():
        for i in range(int(steps)):
            w = z_to_w(z, truncation_psi)
            frames.append(w_to_image(w))
            # Small random step in z-space
            dz = torch.from_numpy(rng.randn(1, G.z_dim)).to(DEVICE).float()
            z = z + dz * step_size
    return frames

# ---------------------------------------------------------------------------
# Find available .pkl files
# ---------------------------------------------------------------------------

def find_pkl_files():
    patterns = [
        os.path.join(REPO_DIR, "models", "*.pkl"),
        os.path.join(REPO_DIR, "*.pkl"),
        os.path.join(REPO_DIR, "output", "*.pkl"),
    ]
    files = []
    for p in patterns:
        files.extend(glob.glob(p))
    # Return relative paths
    return [os.path.relpath(f, REPO_DIR) for f in sorted(files)]

# ---------------------------------------------------------------------------
# Build UI
# ---------------------------------------------------------------------------

def build_app():
    pkl_files = find_pkl_files()
    default_pkl = pkl_files[-1] if pkl_files else ""

    with gr.Blocks(title="StyleGAN2 Latent Explorer", theme=gr.themes.Soft()) as app:
        gr.Markdown("# StyleGAN2 Latent Space Explorer")
        gr.Markdown("Explore the latent space of your trained models on Apple Silicon (MPS)")

        with gr.Row():
            pkl_dropdown = gr.Dropdown(
                choices=pkl_files,
                value=default_pkl,
                label="Model checkpoint (.pkl)",
                allow_custom_value=True,
            )
            load_btn = gr.Button("Load Model", variant="primary")
            status = gr.Textbox(label="Status", interactive=False)

        load_btn.click(load_model, inputs=pkl_dropdown, outputs=status)

        with gr.Tabs():
            # --- Tab 1: Single Seed ---
            with gr.TabItem("Seed Explorer"):
                with gr.Row():
                    with gr.Column(scale=1):
                        seed = gr.Slider(0, 99999, value=42, step=1, label="Seed")
                        psi = gr.Slider(0, 2, value=0.7, step=0.05, label="Truncation (psi)")
                        gen_btn = gr.Button("Generate", variant="primary")
                        grid_btn = gr.Button("3x3 Grid (9 seeds)")
                        info = gr.Textbox(label="Info", interactive=False)
                    with gr.Column(scale=2):
                        img_out = gr.Image(label="Output", type="pil")
                        grid_out = gr.Image(label="Grid", type="pil", visible=False)

                gen_btn.click(generate_single, [seed, psi], [img_out, info])
                seed.change(generate_single, [seed, psi], [img_out, info])
                psi.change(generate_single, [seed, psi], [img_out, info])
                grid_btn.click(
                    lambda s, p: (generate_grid(s, p), gr.update(visible=True)),
                    [seed, psi],
                    [grid_out, grid_out],
                )

            # --- Tab 2: Interpolation ---
            with gr.TabItem("Interpolation"):
                with gr.Row():
                    with gr.Column(scale=1):
                        seed_a = gr.Slider(0, 99999, value=42, step=1, label="Seed A")
                        seed_b = gr.Slider(0, 99999, value=123, step=1, label="Seed B")
                        interp_steps = gr.Slider(4, 64, value=16, step=1, label="Steps")
                        interp_psi = gr.Slider(0, 2, value=0.7, step=0.05, label="Truncation")
                        interp_space = gr.Radio(["Z (raw)", "W (smoother)"], value="W (smoother)", label="Space")
                        interp_btn = gr.Button("Interpolate", variant="primary")
                    with gr.Column(scale=2):
                        gallery = gr.Gallery(label="Interpolation", columns=4, height="auto")

                interp_btn.click(
                    interpolate,
                    [seed_a, seed_b, interp_steps, interp_psi, interp_space],
                    gallery,
                )

            # --- Tab 3: Style Mixing ---
            with gr.TabItem("Style Mixing"):
                gr.Markdown("Coarse layers (low numbers) = pose, shape. Fine layers (high numbers) = color, texture.")
                with gr.Row():
                    with gr.Column(scale=1):
                        mix_seed_a = gr.Slider(0, 99999, value=42, step=1, label="Seed A (coarse)")
                        mix_seed_b = gr.Slider(0, 99999, value=777, step=1, label="Seed B (fine)")
                        cutoff = gr.Slider(1, 14, value=7, step=1, label="Layer cutoff")
                        mix_psi = gr.Slider(0, 2, value=0.7, step=0.05, label="Truncation")
                        mix_btn = gr.Button("Mix Styles", variant="primary")
                        mix_info = gr.Textbox(label="Info", interactive=False)
                    with gr.Column(scale=2):
                        with gr.Row():
                            mix_img_a = gr.Image(label="Seed A", type="pil")
                            mix_img_b = gr.Image(label="Seed B", type="pil")
                            mix_img_out = gr.Image(label="Mixed", type="pil")

                mix_btn.click(
                    style_mix,
                    [mix_seed_a, mix_seed_b, cutoff, mix_psi],
                    [mix_img_a, mix_img_b, mix_img_out, mix_info],
                )

            # --- Tab 4: Random Walk ---
            with gr.TabItem("Random Walk"):
                with gr.Row():
                    with gr.Column(scale=1):
                        walk_seed = gr.Slider(0, 99999, value=42, step=1, label="Starting seed")
                        walk_steps = gr.Slider(8, 120, value=30, step=1, label="Frames")
                        walk_size = gr.Slider(0.01, 0.5, value=0.1, step=0.01, label="Step size")
                        walk_psi = gr.Slider(0, 2, value=0.7, step=0.05, label="Truncation")
                        walk_btn = gr.Button("Walk", variant="primary")
                    with gr.Column(scale=2):
                        walk_gallery = gr.Gallery(label="Random Walk", columns=5, height="auto")

                walk_btn.click(
                    random_walk,
                    [walk_seed, walk_steps, walk_size, walk_psi],
                    walk_gallery,
                )

    return app

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="StyleGAN2 Latent Space Explorer")
    parser.add_argument("--pkl", type=str, default=None, help="Model .pkl path to auto-load")
    parser.add_argument("--port", type=int, default=7860, help="Server port")
    args = parser.parse_args()

    # Auto-load model if specified
    if args.pkl:
        print(load_model(args.pkl))
    else:
        # Auto-load the highest-kimg model found
        pkls = find_pkl_files()
        if pkls:
            print(load_model(pkls[-1]))

    app = build_app()
    app.launch(server_port=args.port, share=False)
