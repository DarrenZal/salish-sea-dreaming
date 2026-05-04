import io, logging, os, sys, time
import numpy as np
import torch, uvicorn
from diffusers import ControlNetModel, StableDiffusionControlNetPipeline, UniPCMultistepScheduler
from fastapi import FastAPI, Request, Response
from PIL import Image
from transformers import DPTForDepthEstimation, DPTImageProcessor

LOG_PATH  = os.path.join("C:", os.sep, "Users", "user", "style_server.log")
LORA_PATH = os.path.join("C:", os.sep, "Users", "user", "Desktop", "briony_watercolor_v1.safetensors")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("style_server")

IMG_SIZE = 512
STEPS = 25
GUIDANCE = 7.5
CONTROLNET_SCALE = 0.6
PROMPT = (
    "brionypenn watercolor painting, Pacific Northwest coastal ecosystem, "
    "natural history illustration, pen-and-ink outlines, soft organic watercolor tones, "
    "dreaming in the Salish Sea"
)
NEG_PROMPT = (
    "photo, photograph, realistic, 3d render, blurry, low quality, "
    "text, watermark, harsh lighting, overexposed"
)

log.info("Loading DPT depth estimator...")
t0 = time.time()
depth_processor = DPTImageProcessor.from_pretrained("Intel/dpt-large")
depth_model = DPTForDepthEstimation.from_pretrained("Intel/dpt-large")
depth_model = depth_model.to("cuda").eval()
log.info(f"DPT loaded in {time.time()-t0:.1f}s")

log.info("Loading ControlNet depth...")
t0 = time.time()
controlnet = ControlNetModel.from_pretrained("lllyasviel/sd-controlnet-depth", torch_dtype=torch.float16)
log.info(f"ControlNet loaded in {time.time()-t0:.1f}s")

log.info("Loading SD 1.5 pipeline...")
t0 = time.time()
pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    controlnet=controlnet,
    torch_dtype=torch.float16,
    safety_checker=None,
)
pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
pipe.to("cuda")
pipe.enable_attention_slicing()
log.info(f"SD 1.5 loaded in {time.time()-t0:.1f}s")

log.info(f"Loading Briony LoRA from {LORA_PATH}...")
t0 = time.time()
pipe.load_lora_weights(LORA_PATH)
log.info(f"LoRA loaded in {time.time()-t0:.1f}s")
log.info("All models ready.")

app = FastAPI()

def _depth_map(img):
    inputs = depth_processor(images=img, return_tensors="pt").to("cuda")
    with torch.no_grad():
        depth_out = depth_model(**inputs).predicted_depth
    depth = depth_out.squeeze().cpu().numpy()
    depth = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)
    return Image.fromarray((depth * 255).astype(np.uint8)).convert("RGB").resize((IMG_SIZE, IMG_SIZE), Image.LANCZOS)

def _style(img_bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((IMG_SIZE, IMG_SIZE), Image.LANCZOS)
    depth_img = _depth_map(img)
    result = pipe(
        prompt=PROMPT, negative_prompt=NEG_PROMPT,
        image=depth_img,
        num_inference_steps=STEPS, guidance_scale=GUIDANCE,
        controlnet_conditioning_scale=CONTROLNET_SCALE,
        width=IMG_SIZE, height=IMG_SIZE,
    ).images[0]
    buf = io.BytesIO()
    result.save(buf, format="JPEG", quality=92)
    return buf.getvalue()

@app.get("/health")
async def health():
    return {"status": "ok", "pipeline": "sd15+controlnet+briony_lora", "device": "3090"}

@app.post("/style")
async def style(request: Request):
    t0 = time.time()
    try:
        img_bytes = await request.body()
        if not img_bytes:
            return Response(content=b"no image", status_code=400)
        out_bytes = _style(img_bytes)
        log.info(f"Styled {len(img_bytes)}B -> {len(out_bytes)}B in {time.time()-t0:.1f}s")
        return Response(content=out_bytes, media_type="image/jpeg")
    except Exception as e:
        log.error(f"Style failed: {e}")
        return Response(content=img_bytes, media_type="image/jpeg")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")
