import torch
import time
from diffusers import StableDiffusionPipeline

print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU: {torch.cuda.get_device_name(0)}')
print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')

# Load a small SD model
print('\nLoading model (first run downloads ~4GB)...')
t0 = time.time()
pipe = StableDiffusionPipeline.from_pretrained(
    'stabilityai/sd-turbo',
    torch_dtype=torch.float16,
    variant='fp16'
)
pipe = pipe.to('cuda')
print(f'Model loaded in {time.time()-t0:.1f}s')

# Generate one image
print('\nGenerating test image...')
t0 = time.time()
image = pipe(
    'a coral reef in the Salish Sea, vibrant colors',
    num_inference_steps=4,
    guidance_scale=0.0
).images[0]
elapsed = time.time() - t0
print(f'Generated in {elapsed:.2f}s')

# Save
image.save('C:\\Users\\user\\test_output.png')
print(f'Saved to C:\\Users\\user\\test_output.png')
print(f'Image size: {image.size}')
print('\nGPU inference test PASSED')
