#!/usr/bin/env python3.11
"""
Salish Sea Dreaming - Image Generation Script
Generates "dreaming" visuals using OpenAI's image API.

Briony paints the Salish Sea awake. We show it dreaming.
"""

import openai
import base64
import os
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'output', 'experiments')
os.makedirs(OUTPUT_DIR, exist_ok=True)

client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# Style prefix applied to all prompts - establishes the dreaming aesthetic
STYLE = (
    "Abstract, luminous, contemplative digital art. "
    "Deep underwater atmosphere, bioluminescent glow. "
    "NOT illustrative or naturalistic - this is what the ocean sees when it dreams. "
    "Color palette: deep ocean blues (#0A1F33, #1A3A4A), "
    "bioluminescent cyan-green (#33CCAA, #66FFCC), "
    "warm salmon-pink accents (#E87060), kelp gold (#B8A030). "
    "Soft, flowing, organic forms. No text, no humans, no hard edges. "
    "Ethereal, vast, quiet. Think: bioluminescence, deep water, emergence."
)

PROMPTS = [
    {
        "name": "herring-spawn-dream",
        "prompt": (
            f"{STYLE} "
            "A vast underwater dreamscape of herring spawning - thousands of tiny luminous forms "
            "dissolving into clouds of milky light. The water itself glows white and cyan as spawn "
            "fills the sea. Distant dark silhouettes of whales move through the luminous fog. "
            "The feeling is sacred, ancient, abundant - a foundation species dreaming itself into existence. "
            "Pearlescent whites and deep teals. Soft particle clouds. Cosmic and oceanic simultaneously."
        ),
    },
    {
        "name": "tlep-octopus-intelligence",
        "prompt": (
            f"{STYLE} "
            "A giant Pacific octopus reimagined as a distributed neural network - eight arms "
            "extending as flowing rivers of bioluminescent light through dark water. "
            "Each arm branches into finer and finer tendrils, like synapses firing in slow motion. "
            "The central body pulses with warm amber and red light. The tentacles glow cyan and green "
            "as they reach into darkness. Nine brains dreaming as one. "
            "Organic intelligence, decentralized consciousness, deep ocean wisdom."
        ),
    },
    {
        "name": "kelp-forest-cathedral",
        "prompt": (
            f"{STYLE} "
            "An underwater kelp forest rendered as a cathedral of light. Tall golden-green columns "
            "of kelp rise from darkness below into shafts of diffused light above. "
            "Between the kelp, bioluminescent particles drift like underwater fireflies. "
            "The scene has depth - foreground kelp in warm gold, middle ground in teal, "
            "background dissolving into deep blue-black. Small luminous fish dart between fronds. "
            "The feeling is ancient, vertical, sacred - a forest that breathes with the tides."
        ),
    },
]


def generate_image(prompt_data):
    name = prompt_data["name"]
    prompt = prompt_data["prompt"]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}_{name}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)

    print(f"\nGenerating: {name}...")
    print(f"Prompt: {prompt[:100]}...")

    result = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1792x1024",
        quality="hd",
        n=1,
    )

    # DALL-E 3 returns a URL
    import requests
    url = result.data[0].url
    revised_prompt = result.data[0].revised_prompt

    response = requests.get(url)
    with open(filepath, 'wb') as f:
        f.write(response.content)

    print(f"Saved: {filepath}")
    print(f"Revised prompt: {revised_prompt[:150]}...")
    return filepath


if __name__ == "__main__":
    print("=== Salish Sea Dreaming - Visual Generation ===\n")
    generated = []
    for p in PROMPTS:
        try:
            path = generate_image(p)
            generated.append(path)
        except Exception as e:
            print(f"Error generating {p['name']}: {e}")

    print(f"\n=== Done! Generated {len(generated)} images ===")
    for g in generated:
        print(f"  {g}")
