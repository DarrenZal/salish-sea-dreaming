import urllib.request, time
req = urllib.request.Request("http://37.27.48.12:9000/td/stream", headers={"Accept": "text/event-stream"})
r = urllib.request.urlopen(req, timeout=30)
print("Connected", flush=True)
start = time.time()
while time.time() - start < 20:
    line = r.readline().decode("utf-8").strip()
    if line:
        print(f"GOT: {line}", flush=True)
print("Done", flush=True)
