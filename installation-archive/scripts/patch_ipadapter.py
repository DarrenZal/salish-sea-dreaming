path = r"C:\Users\user\TouchDesigner\StreamDiffusionTD\StreamDiffusionTD031\StreamDiffusion\src\streamdiffusion\preprocessing\processors\ipadapter_embedding.py"

with open(path, 'r') as f:
    content = f.read()

# Fix 1: clone after get_image_embeds in the cuda stream path
old = "            self._ipadapter_stream.synchronize()\n            \n            # Ensure tensors are accessible from default stream\n            if hasattr(image_embeds, 'record_stream'):\n                image_embeds.record_stream(torch.cuda.current_stream())\n            if hasattr(negative_embeds, 'record_stream'):\n                negative_embeds.record_stream(torch.cuda.current_stream())"

new = "            self._ipadapter_stream.synchronize()\n            \n            # Clone to convert inference tensors to normal tensors (avoids 'cannot save for backward' error)\n            image_embeds = image_embeds.clone()\n            negative_embeds = negative_embeds.clone()\n            \n            # Ensure tensors are accessible from default stream\n            if hasattr(image_embeds, 'record_stream'):\n                image_embeds.record_stream(torch.cuda.current_stream())\n            if hasattr(negative_embeds, 'record_stream'):\n                negative_embeds.record_stream(torch.cuda.current_stream())"

if old in content:
    content = content.replace(old, new)
    print("Fix 1 applied: clone after cuda stream sync")
else:
    print("Fix 1 pattern not found - may already be patched or content differs")

# Fix 2: also clone in the fallback path
old2 = "            image_embeds, negative_embeds = self.ipadapter.get_image_embeds(images=[image])\n            \n        return image_embeds, negative_embeds"
new2 = "            image_embeds, negative_embeds = self.ipadapter.get_image_embeds(images=[image])\n            image_embeds = image_embeds.clone()\n            negative_embeds = negative_embeds.clone()\n            \n        return image_embeds, negative_embeds"

if old2 in content:
    content = content.replace(old2, new2)
    print("Fix 2 applied: clone in fallback path")
else:
    print("Fix 2 pattern not found")

with open(path, 'w') as f:
    f.write(content)

print("Done")
