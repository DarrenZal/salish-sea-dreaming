import pickle, os
for i in (0, 1):
    p = rf"C:\Users\user\Documents\presets\{i}\pickle.pkl"
    print(f"\n=== preset {i} ({os.path.getsize(p)} bytes) ===")
    try:
        with open(p, "rb") as f:
            obj = pickle.load(f)
        print(type(obj).__name__, "->", obj)
    except Exception as e:
        print("load error:", e)
