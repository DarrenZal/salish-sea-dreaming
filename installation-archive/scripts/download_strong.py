import urllib.request, os, base64, json

TOKEN = "8f6ceea09691892cf2d19dc7466669ea"
BASE_URL = "https://model-deployment-0b50s.paas.ai.telus.com"
FILES = [
    "sd15-briony-strong/model_index.json",
    "sd15-briony-strong/vae/config.json",
    "sd15-briony-strong/vae/diffusion_pytorch_model.safetensors",
    "sd15-briony-strong/unet/config.json",
    "sd15-briony-strong/unet/diffusion_pytorch_model.safetensors",
    "sd15-briony-strong/scheduler/scheduler_config.json",
    "sd15-briony-strong/tokenizer/tokenizer_config.json",
    "sd15-briony-strong/tokenizer/merges.txt",
    "sd15-briony-strong/tokenizer/special_tokens_map.json",
    "sd15-briony-strong/tokenizer/vocab.json",
    "sd15-briony-strong/text_encoder/config.json",
    "sd15-briony-strong/text_encoder/model.safetensors",
    "sd15-briony-strong/feature_extractor/preprocessor_config.json",
]

out_base = r"C:\models"

for rel_path in FILES:
    out_path = os.path.join(out_base, rel_path.replace("/", "\\"))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    url = f"{BASE_URL}/api/contents/{rel_path}"
    req = urllib.request.Request(url, headers={"Authorization": f"token {TOKEN}"})
    
    print(f"Downloading {rel_path}...", flush=True)
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read())
    
    if data["format"] == "base64":
        content = base64.b64decode(data["content"])
    else:
        content = data["content"].encode("utf-8")
    
    with open(out_path, "wb") as f:
        f.write(content)
    print(f"  -> {len(content):,} bytes", flush=True)

print("All done! Model at C:\\models\\sd15-briony-strong")
