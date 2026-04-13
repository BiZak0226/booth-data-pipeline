import json, os

def load(p):
    if not os.path.exists(p):
        return {}
    return json.load(open(p, encoding="utf-8"))

old = load("data/raw/previous/sat.json")
new = load("data/raw/latest/sat.json")

changed = old != new

if changed:
    print("변경 있음")
else:
    print("변경 없음")
    