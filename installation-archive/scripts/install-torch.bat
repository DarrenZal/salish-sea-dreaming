python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118 --no-cache-dir  
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"  
DONE 
