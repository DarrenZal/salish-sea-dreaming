import subprocess, json
r = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw", "--format=csv,noheader,nounits"], capture_output=True, text=True)
print("GPU:", r.stdout.strip())
r2 = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader"], capture_output=True, text=True)
print("Processes:", r2.stdout.strip() if r2.stdout.strip() else "None")


