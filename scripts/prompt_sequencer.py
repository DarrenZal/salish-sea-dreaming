_state = {}

_last_osc_content = ""  # track last OSC row content — survives rolling window


SEQUENCE = [
    (0,  26, 6),   # pacific northwest coast dawn mist
    (1,  26, 6),   # northwest forest shore morning light
    (2,  26, 6),   # children on seashore
    (3,  26, 6),   # tide pools intertidal
    (4,  26, 6),   # nudibranch
    (5,  26, 6),   # shipping tanker
    (6,  26, 6),   # black oil spill shore
    (7,  26, 6),   # kelp forest underwater
    (8,  26, 6),   # herring spawn silver
    (9,  26, 6),   # red sockeye salmon
    (10, 26, 6),   # orca whale
    (11, 26, 6),   # humpback whale
    (12, 26, 6),   # fishing trawler
    (13, 26, 6),   # red octopus
    (14, 26, 6),   # pacific coral reef
    (15, 26, 6),   # neurons bioluminescent
    (16, 26, 6),   # neurons electric
    (17, 26, 6),   # mycelium network
    (18, 26, 6),   # mushrooms log
    (19, 26, 6),   # cedar roots old growth
    (20, 26, 6),   # black raven in forest
    (21, 26, 6),   # bald eagle on seashore
    (22, 26, 6),   # northwest coast night -> loops to 0
]


TOTAL_DURATION = sum(d for _, d, _ in SEQUENCE)

NUM_PROMPTS = 23

VISITOR_SLOT = 22

ORIG_SLOT22 = "northwest coast night"

VISITOR_DURATION = 30

VISITOR_FADE = 6


def _get_current_loop_prompt(loop_elapsed):
    """Return (current_prompt_idx, next_prompt_idx, fade_progress)"""
    t = 0
    for i, (prompt_idx, duration, fade) in enumerate(SEQUENCE):
        if loop_elapsed < t + duration:
            segment_elapsed = loop_elapsed - t
            next_i = (i + 1) % len(SEQUENCE)
            fade_start = duration - fade
            fp = 0.0
            if segment_elapsed >= fade_start:
                fp = max(0.0, min(1.0, (segment_elapsed - fade_start) / fade))
            return prompt_idx, SEQUENCE[next_i][0], fp
        t += duration
    return 0, 1, 0.0

def _time_for_prompt(prompt_idx):
    """Return elapsed time when a given prompt starts"""
    t = 0
    for pidx, dur, _ in SEQUENCE:
        if pidx == prompt_idx:
            return t
        t += dur
    return 0

def frameStart(frame):
    global _state, _last_osc_content
    sd = op("/project1/StreamDiffusionTD")
    if sd is None:
        return

    queue = op("/project1/visitor_queue")
    osc_in = op("/project1/ssd_osc_in")

    # --- CHECK OSC ---
    # Track last row content not row count — OSC In DAT rolls at ~11 rows
    # so numRows never grows past the cap and count-based detection breaks.
    if osc_in and osc_in.numRows > 1:
        last_content = str(osc_in[osc_in.numRows - 1, 0].val)
        if last_content != _last_osc_content:
            _last_osc_content = last_content
            try:
                if last_content.startswith("/salish/prompt/visitor"):
                    prompt_text = last_content.replace("/salish/prompt/visitor", "").strip().strip('"')
                    if prompt_text and queue:
                        queue.appendRow([prompt_text, str(absTime.seconds)])
                        print(f"[SSD] Queued: {prompt_text[:60]}")
            except Exception:
                pass

    # --- INIT ---
    if "start_time" not in _state:
        _state["start_time"] = absTime.seconds
        _state["visitor_active"] = False
        _state["visitor_start"] = 0
        _state["interrupted_prompt"] = 0

    now = absTime.seconds
    has_visitor = queue and queue.numRows > 1

    # --- VISITOR ARRIVES: capture where we are in the loop ---
    if has_visitor and not _state["visitor_active"]:
        _state["visitor_active"] = True
        _state["visitor_start"] = now
        # Figure out where we are in the loop right now
        elapsed = now - _state["start_time"]
        loop_elapsed = elapsed % TOTAL_DURATION
        cur, nxt, _ = _get_current_loop_prompt(loop_elapsed)
        _state["interrupted_prompt"] = cur
        _state["resume_prompt"] = (cur + 1) % NUM_PROMPTS
        # Set visitor prompt text
        prompt_text = str(queue[1, 0].val)
        sd.par["Promptdict" + str(VISITOR_SLOT) + "concept"] = prompt_text
        print(f"[SSD] Playing visitor (interrupted {cur}): {prompt_text[:50]}")

    # --- VISITOR ACTIVE ---
    if _state["visitor_active"]:
        visitor_elapsed = now - _state["visitor_start"]

        # Check if done
        if visitor_elapsed >= VISITOR_DURATION:
            if queue and queue.numRows > 1:
                queue.deleteRow(1)
            if queue and queue.numRows > 1:
                # Next visitor in queue
                _state["visitor_start"] = now
                nxt_p = str(queue[1, 0].val)
                sd.par["Promptdict" + str(VISITOR_SLOT) + "concept"] = nxt_p
                print(f"[SSD] Next visitor: {nxt_p[:50]}")
                return
            else:
                # Queue empty — resume loop from next prompt
                _state["visitor_active"] = False
                sd.par["Promptdict" + str(VISITOR_SLOT) + "concept"] = ORIG_SLOT22
                # Set loop time to start of resume prompt
                resume = _state["resume_prompt"]
                _state["start_time"] = now - _time_for_prompt(resume)
                print(f"[SSD] Resuming loop at prompt {resume}")

        if _state["visitor_active"]:
            visitor_elapsed = now - _state["visitor_start"]
            interrupted = _state["interrupted_prompt"]
            resume = _state["resume_prompt"]

            # Fade envelope
            if visitor_elapsed < VISITOR_FADE:
                blend = visitor_elapsed / VISITOR_FADE
            elif visitor_elapsed > VISITOR_DURATION - VISITOR_FADE:
                blend = max(0, (VISITOR_DURATION - visitor_elapsed) / VISITOR_FADE)
            else:
                blend = 1.0

            # Set weights
            for j in range(NUM_PROMPTS):
                sd.par["Promptdict" + str(j) + "weight"] = 0.0

            # Visitor weight
            sd.par["Promptdict" + str(VISITOR_SLOT) + "weight"] = round(blend, 4)

            # During fade-in: blend FROM interrupted prompt
            if visitor_elapsed < VISITOR_FADE:
                sd.par["Promptdict" + str(interrupted) + "weight"] = round(1.0 - blend, 4)
            # During fade-out: blend TO resume prompt
            elif visitor_elapsed > VISITOR_DURATION - VISITOR_FADE:
                sd.par["Promptdict" + str(resume) + "weight"] = round(1.0 - blend, 4)
            return

    # --- DEFAULT LOOP ---
    elapsed = now - _state["start_time"]
    loop_elapsed = elapsed % TOTAL_DURATION
    cur, nxt, fade_progress = _get_current_loop_prompt(loop_elapsed)

    for j in range(NUM_PROMPTS):
        sd.par["Promptdict" + str(j) + "weight"] = 0.0

    if fade_progress < 0.001:
        sd.par["Promptdict" + str(cur) + "weight"] = 1.0
    else:
        sd.par["Promptdict" + str(cur) + "weight"] = round(1.0 - fade_progress, 4)
        sd.par["Promptdict" + str(nxt) + "weight"] = round(fade_progress, 4)
