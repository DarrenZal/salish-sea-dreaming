S = 0.1
DEPTH = 0.022000000000000002
PROFILE = [(0.1, 0.0), (0.05, 0.032), (0.010000000000000002, 0.03), (-0.010000000000000002, 0.027000000000000003), (-0.03, 0.024), (-0.05, 0.04000000000000001), (-0.034999999999999996, 0.0), (-0.05, -0.04000000000000001), (-0.03, -0.024), (-0.010000000000000002, -0.027000000000000003), (0.010000000000000002, -0.03), (0.05, -0.032)]

def onSetupParameters(scriptOp): return
def onPulse(par): return

def onCook(scriptOp):
    scriptOp.clear()
    n = len(PROFILE)
    front = []
    for (x, y) in PROFILE:
        p = scriptOp.appendPoint()
        p.x = x; p.y = y; p.z = -DEPTH * 0.5
        front.append(p)
    back = []
    for (x, y) in PROFILE:
        p = scriptOp.appendPoint()
        p.x = x; p.y = y; p.z = DEPTH * 0.5
        back.append(p)
    f = scriptOp.appendPoly(n, closed=True, addPoints=False)
    for i, p in enumerate(front):
        f[i].point = p
    b = scriptOp.appendPoly(n, closed=True, addPoints=False)
    for i, p in enumerate(reversed(back)):
        b[i].point = p
    for i in range(n):
        q = scriptOp.appendPoly(4, closed=True, addPoints=False)
        q[0].point = front[i]
        q[1].point = front[(i + 1) % n]
        q[2].point = back[(i + 1) % n]
        q[3].point = back[i]
