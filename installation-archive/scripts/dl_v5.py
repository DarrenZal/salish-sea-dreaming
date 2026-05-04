import urllib.request, os, time

BASE  = 'https://model-deployment-0b50s.paas.ai.telus.com/files'
TOKEN = '8f6ceea09691892cf2d19dc7466669ea'
DEST  = r'C:\Users\user\models\sd-turbo-briony-v5'
LOG   = r'C:\Users\user\v5_download.log'

FILES = [
    ('model_index.json',                          1),
    ('unet/config.json',                          2),
    ('unet/diffusion_pytorch_model.safetensors',  1_814_154_256),
    ('vae/config.json',                           907),
    ('vae/diffusion_pytorch_model.safetensors',   167_335_342),
    ('text_encoder/config.json',                  549),
    ('text_encoder/model.safetensors',            680_820_392),
    ('scheduler/scheduler_config.json',           677),
    ('tokenizer/tokenizer_config.json',           885),
    ('tokenizer/merges.txt',                      524_619),
    ('tokenizer/special_tokens_map.json',         574),
    ('tokenizer/vocab.json',                      1_059_962),
]

def log(msg):
    with open(LOG, 'a') as f:
        f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    print(msg)

for relpath, expected_size in FILES:
    out = os.path.join(DEST, relpath.replace('/', os.sep))
    os.makedirs(os.path.dirname(out), exist_ok=True)

    existing = os.path.getsize(out) if os.path.exists(out) else 0
    if existing >= expected_size - 1024:
        log(f"SKIP {relpath} ({existing//1024//1024} MB)")
        continue

    url = f"{BASE}/sd-turbo-briony-v5/{relpath}?token={TOKEN}"
    log(f"START {relpath} ({expected_size//1024//1024} MB)")

    headers = {}
    mode = 'wb'
    if existing > 0:
        headers['Range'] = f'bytes={existing}-'
        mode = 'ab'
        log(f"  resuming from {existing//1024//1024} MB")

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=600) as resp, open(out, mode) as f:
            downloaded = existing
            chunk = 1024 * 1024  # 1 MB chunks
            while True:
                data = resp.read(chunk)
                if not data:
                    break
                f.write(data)
                downloaded += len(data)
                if downloaded % (50*1024*1024) < chunk:
                    log(f"  {relpath}: {downloaded//1024//1024} MB")
    except Exception as e:
        log(f"ERROR {relpath}: {e}")
        continue

    final = os.path.getsize(out)
    log(f"DONE {relpath} ({final//1024//1024} MB)")

log("=== ALL DONE ===")
