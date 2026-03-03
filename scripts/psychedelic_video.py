# Psychedelic Video Effect Chain v4 - ACTUALLY COLORFUL
# Removed broken RGB separation, using simpler color approach

project = op('/project1')

# Clean up previous run
for name in ['hsv_shift', 'feedback', 'feedback_xform', 'feedback_fade',
             'mix_feedback', 'edges', 'edge_color', 'edge_boost', 'combined',
             'glow', 'with_glow', 'mirror', 'kaleido', 'psychedelic_out',
             'glow_fade', 'rgb_shift_r', 'rgb_shift_g', 'rgb_shift_b', 'rgb_combined',
             'feedback_hue', 'glow_color', 'color_boost']:
    if op('/project1/' + name):
        op('/project1/' + name).destroy()

video_in = op('/project1/videodevin1')

if not video_in:
    print("ERROR: No videodevin1 found.")
else:
    # === PUMP UP THE COLOR ===
    hsv = project.create(hsvadjustTOP, 'hsv_shift')
    hsv.inputConnectors[0].connect(video_in)
    hsv.par.hueoffset.expr = 'absTime.seconds * 0.1'
    hsv.par.saturationmult = 2.5
    hsv.par.valuemult = 1.0
    hsv.nodeX = 200
    hsv.nodeY = 0

    # === FEEDBACK LOOP with rainbow trails ===
    feedback = project.create(feedbackTOP, 'feedback')
    feedback.par.resolutionw = 1280
    feedback.par.resolutionh = 720
    feedback.nodeX = 400
    feedback.nodeY = -200

    feedback_xform = project.create(transformTOP, 'feedback_xform')
    feedback_xform.inputConnectors[0].connect(feedback)
    feedback_xform.par.sx = 1.02
    feedback_xform.par.sy = 1.02
    feedback_xform.par.rotate.expr = '1.5'
    feedback_xform.nodeX = 600
    feedback_xform.nodeY = -200

    # Hue shift feedback for rainbow trails
    feedback_hue = project.create(hsvadjustTOP, 'feedback_hue')
    feedback_hue.inputConnectors[0].connect(feedback_xform)
    feedback_hue.par.hueoffset = 0.03
    feedback_hue.par.saturationmult = 1.1
    feedback_hue.nodeX = 800
    feedback_hue.nodeY = -200

    feedback_fade = project.create(levelTOP, 'feedback_fade')
    feedback_fade.inputConnectors[0].connect(feedback_hue)
    feedback_fade.par.brightness1 = 0.85
    feedback_fade.nodeX = 1000
    feedback_fade.nodeY = -200

    # Mix current frame with feedback
    mix_feedback = project.create(compositeTOP, 'mix_feedback')
    mix_feedback.par.operand = 'over'
    mix_feedback.inputConnectors[0].connect(hsv)
    mix_feedback.inputConnectors[1].connect(feedback_fade)
    mix_feedback.nodeX = 400
    mix_feedback.nodeY = 0

    feedback.inputConnectors[0].connect(mix_feedback)

    # === EDGES - colorized ===
    edges = project.create(edgeTOP, 'edges')
    edges.inputConnectors[0].connect(mix_feedback)
    edges.nodeX = 600
    edges.nodeY = 0

    # Color the edges with cycling hue
    edge_color = project.create(hsvadjustTOP, 'edge_color')
    edge_color.inputConnectors[0].connect(edges)
    edge_color.par.hueoffset.expr = 'absTime.seconds * -0.15'
    edge_color.par.saturationmult = 5
    edge_color.par.valuemult = 1.5
    edge_color.nodeX = 800
    edge_color.nodeY = 0

    edge_boost = project.create(levelTOP, 'edge_boost')
    edge_boost.inputConnectors[0].connect(edge_color)
    edge_boost.par.brightness1 = 1.5
    edge_boost.par.gamma1 = 0.8
    edge_boost.nodeX = 1000
    edge_boost.nodeY = 0

    # === COMBINE video + edges ===
    combined = project.create(compositeTOP, 'combined')
    combined.par.operand = 'screen'
    combined.inputConnectors[0].connect(mix_feedback)
    combined.inputConnectors[1].connect(edge_boost)
    combined.nodeX = 1200
    combined.nodeY = 0

    # === GLOW ===
    glow = project.create(blurTOP, 'glow')
    glow.inputConnectors[0].connect(edge_boost)
    glow.par.size = 25
    glow.nodeX = 1000
    glow.nodeY = -100

    glow_fade = project.create(levelTOP, 'glow_fade')
    glow_fade.inputConnectors[0].connect(glow)
    glow_fade.par.brightness1 = 0.3
    glow_fade.nodeX = 1200
    glow_fade.nodeY = -100

    with_glow = project.create(compositeTOP, 'with_glow')
    with_glow.par.operand = 'add'
    with_glow.inputConnectors[0].connect(combined)
    with_glow.inputConnectors[1].connect(glow_fade)
    with_glow.nodeX = 1400
    with_glow.nodeY = 0

    # === MIRROR for symmetry ===
    mirror = project.create(flipTOP, 'mirror')
    mirror.inputConnectors[0].connect(with_glow)
    mirror.par.flipx = True
    mirror.nodeX = 1600
    mirror.nodeY = -100

    kaleido = project.create(compositeTOP, 'kaleido')
    kaleido.par.operand = 'average'
    kaleido.inputConnectors[0].connect(with_glow)
    kaleido.inputConnectors[1].connect(mirror)
    kaleido.nodeX = 1800
    kaleido.nodeY = 0

    # === FINAL COLOR BOOST ===
    color_boost = project.create(hsvadjustTOP, 'color_boost')
    color_boost.inputConnectors[0].connect(kaleido)
    color_boost.par.saturationmult = 1.5
    color_boost.nodeX = 2000
    color_boost.nodeY = 0

    # === OUTPUT ===
    out = project.create(outTOP, 'psychedelic_out')
    out.inputConnectors[0].connect(color_boost)
    out.nodeX = 2200
    out.nodeY = 0
    out.viewer = True
    out.display = True

    print("Psychedelic v4 - Simpler, more reliable color")
