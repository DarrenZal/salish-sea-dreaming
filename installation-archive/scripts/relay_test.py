import requests, sys, traceback
from pythonosc import udp_client

osc = udp_client.SimpleUDPClient('127.0.0.1', 7000)
POLY_URL = 'http://37.27.48.12:9000'
buf = ''
count = 0
try:
    with requests.get(POLY_URL+'/td/stream', stream=True, timeout=(10,None),
                      headers={'Accept':'text/event-stream','Cache-Control':'no-cache'}) as r:
        r.raise_for_status()
        print('connected', flush=True)
        for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
            if not chunk:
                continue
            buf += chunk
            while chr(10) in buf:
                line, buf = buf.split(chr(10), 1)
                line = line.rstrip(chr(13))
                if line.startswith('data:'):
                    prompt = line[5:].strip()
                    print('GOT:', repr(prompt[:50]), flush=True)
                    if prompt and prompt != 'ping':
                        osc.send_message('/salish/prompt/visitor', prompt)
                        print('OSC sent ok', flush=True)
                        count += 1
                        if count >= 2:
                            print('exit after 2 prompts', flush=True)
                            sys.exit(0)
except Exception:
    traceback.print_exc()
print('DONE', flush=True)
