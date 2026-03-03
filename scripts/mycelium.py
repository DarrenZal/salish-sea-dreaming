# Mycelium Network v14 - Simple and reliable
# Static veins with animated brightness modulation

project = op('/project1')

if op('/project1/salish'):
    op('/project1/salish').destroy()

container = project.create(baseCOMP, 'salish')

# === STATIC NETWORK ===
network_noise = container.create(noiseTOP, 'network_noise')
network_noise.par.mono = True
network_noise.par.period = 1.2
network_noise.par.harmon = 4
network_noise.par.rough = 0.6
network_noise.par.seed = 5
network_noise.par.resolutionw = 1280
network_noise.par.resolutionh = 720
network_noise.par.tx = 0
network_noise.par.ty = 0
network_noise.nodeX = 0
network_noise.nodeY = 0

# Edge detect for veins
veins = container.create(edgeTOP, 'veins')
veins.inputConnectors[0].connect(network_noise)
veins.nodeX = 200
veins.nodeY = 0

# Boost veins strongly
veins_boost = container.create(levelTOP, 'veins_boost')
veins_boost.inputConnectors[0].connect(veins)
veins_boost.par.brightness1 = 5
veins_boost.par.gamma1 = 0.5
veins_boost.nodeX = 400
veins_boost.nodeY = 0

# === ANIMATED PULSE PATTERN ===
# Use noise that moves slowly - same seed creates correlated movement
pulse_noise = container.create(noiseTOP, 'pulse_noise')
pulse_noise.par.mono = True
pulse_noise.par.period = 0.8  # Smaller = more detail
pulse_noise.par.harmon = 2
pulse_noise.par.rough = 0.3
pulse_noise.par.seed = 5  # Same seed!
pulse_noise.par.resolutionw = 1280
pulse_noise.par.resolutionh = 720
pulse_noise.par.tx.expr = 'absTime.seconds * 0.1'
pulse_noise.par.ty.expr = 'absTime.seconds * 0.07'
pulse_noise.nodeX = 0
pulse_noise.nodeY = -200

# Sharpen the pulse noise to create distinct bright/dark bands
pulse_sharp = container.create(levelTOP, 'pulse_sharp')
pulse_sharp.inputConnectors[0].connect(pulse_noise)
pulse_sharp.par.gamma1 = 2.5
pulse_sharp.par.blacklevel = 0.3
pulse_sharp.nodeX = 200
pulse_sharp.nodeY = -200

# === COMBINE: veins * pulse = pulsing veins ===
pulsing = container.create(compositeTOP, 'pulsing')
pulsing.par.operand = 'multiply'
pulsing.inputConnectors[0].connect(veins_boost)
pulsing.inputConnectors[1].connect(pulse_sharp)
pulsing.nodeX = 400
pulsing.nodeY = -100

# Boost the pulsing result
pulse_boost = container.create(levelTOP, 'pulse_boost')
pulse_boost.inputConnectors[0].connect(pulsing)
pulse_boost.par.brightness1 = 3
pulse_boost.par.gamma1 = 0.7
pulse_boost.nodeX = 600
pulse_boost.nodeY = -100

# === COLORS ===
# Dim base veins (always visible)
dim_color = container.create(constantTOP, 'dim_color')
dim_color.par.colorr = 0.01
dim_color.par.colorg = 0.06
dim_color.par.colorb = 0.04
dim_color.par.resolutionw = 1280
dim_color.par.resolutionh = 720
dim_color.nodeX = 400
dim_color.nodeY = 100

dim_veins = container.create(compositeTOP, 'dim_veins')
dim_veins.par.operand = 'multiply'
dim_veins.inputConnectors[0].connect(veins_boost)
dim_veins.inputConnectors[1].connect(dim_color)
dim_veins.nodeX = 600
dim_veins.nodeY = 50

# Bright pulse color
bright_color = container.create(constantTOP, 'bright_color')
bright_color.par.colorr = 0.1
bright_color.par.colorg = 1.0
bright_color.par.colorb = 0.5
bright_color.par.resolutionw = 1280
bright_color.par.resolutionh = 720
bright_color.nodeX = 600
bright_color.nodeY = -250

bright_pulse = container.create(compositeTOP, 'bright_pulse')
bright_pulse.par.operand = 'multiply'
bright_pulse.inputConnectors[0].connect(pulse_boost)
bright_pulse.inputConnectors[1].connect(bright_color)
bright_pulse.nodeX = 800
bright_pulse.nodeY = -100

# === FINAL COMBINE ===
combined = container.create(compositeTOP, 'combined')
combined.par.operand = 'add'
combined.inputConnectors[0].connect(dim_veins)
combined.inputConnectors[1].connect(bright_pulse)
combined.nodeX = 1000
combined.nodeY = 0

# Glow effect
glow = container.create(blurTOP, 'glow')
glow.inputConnectors[0].connect(bright_pulse)
glow.par.size = 15
glow.nodeX = 800
glow.nodeY = -250

with_glow = container.create(compositeTOP, 'with_glow')
with_glow.par.operand = 'add'
with_glow.inputConnectors[0].connect(combined)
with_glow.inputConnectors[1].connect(glow)
with_glow.nodeX = 1200
with_glow.nodeY = 0

# Output
out = container.create(outTOP, 'output')
out.inputConnectors[0].connect(with_glow)
out.nodeX = 1400
out.nodeY = 0
out.viewer = True
out.display = True

print("v14 - Static veins with traveling brightness bands")
