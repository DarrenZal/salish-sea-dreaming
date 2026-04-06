"""
ssd_osc_in_callbacks.py — OSC In DAT callback for Salish Sea Dreaming.
Paste into /project1/ssd_osc_in_callbacks in TouchDesigner.

Fires on every OSC receive — bypasses the rolling-window dedup problem
that breaks row-count detection in frameStart after ~11 messages.
"""
from typing import List, Any


def onReceiveOSC(dat, rowIndex: int, message: str,
                 byteData: bytes, timeStamp: float, address: str,
                 args: List[Any], peer):
    if address == '/salish/prompt/visitor' and args:
        prompt_text = str(args[0]).strip()
        if prompt_text:
            queue = op('/project1/visitor_queue')
            if queue:
                queue.appendRow([prompt_text, str(absTime.seconds)])
                print(f"[SSD] Queued via callback: {prompt_text[:60]}")
