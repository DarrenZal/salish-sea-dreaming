"""Fix the visitor snapshot timing bug.

Current: relay schedules ONE upload at T+8s after OSC dispatch. But StreamDiffusion
needs 5-10s to lock onto a new prompt past the cross-fade, so T+8s often captures
the tail of the previous prompt's render.

Fix: schedule TWO uploads — at T+15s (definitive, well into render) AND at T+25s
(safety, overrides T+15 if late dream-quality framing emerged). Second upload
OVERWRITES first via the same prompt_id, so visitor sees the latest captured frame.

Run on 3090 (windows-desktop-remote):
  python C:\\Users\\user\\fix_visitor_snapshot_timing.py
"""
import pathlib

p = pathlib.Path(r"C:\Users\user\td_relay.py")
text = p.read_text(encoding="utf-8")

if "SSD-2026-05-27 visitor-snap-double" in text:
    print("already patched")
    raise SystemExit(0)

# 1. Bump default delay 8.0 -> 15.0
old_delay = 'VISITOR_SNAP_DELAY_SECS = float(os.getenv("VISITOR_SNAP_DELAY_SECS", "8.0"))'
new_delay = 'VISITOR_SNAP_DELAY_SECS = float(os.getenv("VISITOR_SNAP_DELAY_SECS", "15.0"))  # SSD-2026-05-27 visitor-snap-double: bumped 8->15 so StreamDiffusion has time to lock onto the prompt past cross-fade\nVISITOR_SNAP_DELAY_SECS_2 = float(os.getenv("VISITOR_SNAP_DELAY_SECS_2", "25.0"))  # second pass — overrides first if a later/cleaner frame emerges'

if old_delay in text:
    text = text.replace(old_delay, new_delay)
    print("+ bumped delay 8->15s + added second pass at 25s")

# 2. In the dispatch block — schedule TWO timers instead of one
old_dispatch = """            # Schedule a visitor-tagged snapshot upload once TD has rendered the prompt.
            if prompt_id is not None:
                threading.Timer(
                    VISITOR_SNAP_DELAY_SECS,
                    _push_visitor_snapshot,
                    args=(prompt_id,),
                ).start()"""
new_dispatch = """            # SSD-2026-05-27 visitor-snap-double: schedule TWO uploads.
            # First at T+15s captures the initial settled render past cross-fade.
            # Second at T+25s overwrites it if a later, more prompt-aligned frame
            # has emerged (StreamDiffusion can keep refining for ~20s). The
            # second upload uses the same prompt_id, so server's _visitor_snapshots
            # dict naturally overwrites the first entry.
            if prompt_id is not None:
                threading.Timer(
                    VISITOR_SNAP_DELAY_SECS,
                    _push_visitor_snapshot,
                    args=(prompt_id,),
                ).start()
                threading.Timer(
                    VISITOR_SNAP_DELAY_SECS_2,
                    _push_visitor_snapshot,
                    args=(prompt_id,),
                ).start()"""

if old_dispatch in text:
    text = text.replace(old_dispatch, new_dispatch)
    print("+ scheduled second-pass timer")

p.write_text(text, encoding="utf-8")
print(f"\nWrote {p}")
print("\nNext: restart td_relay (kill python process, NSSM will restart it)")
