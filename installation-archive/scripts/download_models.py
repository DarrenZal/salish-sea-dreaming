import json, base64, urllib.request
from pathlib import Path

NODE_URL = "https://model-deployment-0b50s.paas.ai.telus.com"
TOKEN = "8f6ceea09691892cf2d19dc7466669ea"
LOCAL_DIR = Path("C:/models")

def download_dir(remote_path, local_path):
    Path(local_path).mkdir(parents=True, exist_ok=True)
    url = f"{NODE_URL}/api/contents/{remote_path}"
    req = urllib.request.Request(url, headers={"Authorization": f"token {TOKEN}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        items = json.loads(r.read())["content"]
    for item in items:
        if item["type"] == "directory":
            download_dir(item["path"], Path(local_path) / item["name"])
        else:
            download_file(item["path"], Path(local_path) / item["name"])

def download_file(remote_path, local_path):
    if local_path.exists():
        print(f"  skip (exists): {local_path.name}")
        return
    print(f"  {local_path.name}...", end=" ", flush=True)
    url = f"{NODE_URL}/api/contents/{remote_path}?content=1&type=file"
    req = urllib.request.Request(url, headers={"Authorization": f"token {TOKEN}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read())
    content = data["content"]
    fmt = data.get("format", "text")
    with open(local_path, "wb") as f:
        f.write(base64.b64decode(content) if fmt == "base64" else content.encode())
    size = local_path.stat().st_size
    print(f"{size/1e6:.1f}MB")

print("=== Downloading sd15-briony-baked (2.1GB) ===")
download_dir("sd15-briony-baked", LOCAL_DIR / "sd15-briony-baked")

print("\n=== Downloading sd-turbo-briony-baked-v2 (2.6GB) ===")
download_dir("sd-turbo-briony-baked-v2", LOCAL_DIR / "sd-turbo-briony-baked-v2")

print("\nDone! Models at C:\\models\\")
