# -*- coding: utf-8 -*-
"""分析 dracu-riot 全部剧本 JSON，提取资源引用清单（说话者/立绘/背景/CG/特效）"""
import json, glob, os, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

JSON_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "剧本json")

def iter_objects(scene):
    """遍历 scene 中所有 text_block 的 objectList 对象"""
    for tb in scene.get("texts", []):
        if isinstance(tb, list) and len(tb) > 5 and isinstance(tb[5], dict):
            for obj in tb[5].get("objectList", []):
                if isinstance(obj, dict):
                    yield obj

def extract_objs(obj):
    """从 objectList 对象递归提取 imageFile 和 actionList"""
    out = {}
    for k in ("file", "options", "actionList", "cname", "disp", "posName", "cameraMode"):
        if k in obj:
            out[k] = obj[k]
    return out

speakers = collections.Counter()
chars = collections.Counter()      # 立绘引用
stages = collections.Counter()     # 背景引用
events = collections.Counter()     # CG 引用
effects = collections.Counter()    # 特效
text_total = 0
scene_total = 0
char_files = collections.Counter() # 立绘文件名

for p in sorted(glob.glob(os.path.join(JSON_DIR, "*.json"))):
    if ".resx" in p:
        continue
    d = json.load(open(p, encoding="utf-8"))
    for scene in d.get("scenes", []):
        scene_total += 1
        for tb in scene.get("texts", []):
            if isinstance(tb, list) and len(tb) >= 3 and tb[2]:
                text_total += 1
                # 说话者
                if tb[0]:
                    speakers[tb[0]] += 1
        for obj in iter_objects(scene):
            cname = obj.get("cname", "?")
            img = obj.get("imageFile", {})
            if isinstance(img, dict):
                file = img.get("file", "")
                opts = img.get("options", {})
                if cname == "character" and file:
                    key = file
                    if isinstance(opts, dict):
                        q = "&".join(f"{k}={v}" for k, v in opts.items() if v)
                        if q: key = f"{file}?{q}"
                    chars[key] += 1
                    char_files[file] += 1
                elif cname in ("stage", "stage2", "stage3") and file:
                    if isinstance(opts, dict):
                        key = file + "|" + "+".join(f"{k}={v}" for k, v in opts.items() if v)
                    else:
                        key = file
                    stages[key] += 1
                elif cname in ("event", "event2") and file:
                    events[file] += 1
            # 特效检测
            s = json.dumps(obj, ensure_ascii=False)
            for eff in ("vibration", "doBoxBlur", "ZoomAction", "blur"):
                if eff in s:
                    effects[eff] += 1

print(f"剧本数: {len([p for p in glob.glob(os.path.join(JSON_DIR,'*.json')) if '.resx' not in p])}")
print(f"scene 总数: {scene_total}")
print(f"文本条数: {text_total}")
print(f"\n=== 说话者 Top 25 ===")
for s, c in speakers.most_common(25):
    print(f"  {s:<12} {c}")
print(f"\n=== 立绘引用数: {len(chars)} 种, 立绘文件名 {len(char_files)} 种 ===")
for f, c in char_files.most_common(30):
    print(f"  {f:<20} {c}")
print(f"\n=== 背景引用: {len(stages)} 种 ===")
for s, c in stages.most_common(20):
    print(f"  {s:<40} {c}")
print(f"\n=== CG 引用: {len(events)} 种 ===")
for e, c in events.most_common(20):
    print(f"  {e:<30} {c}")
print(f"\n=== 特效 ===")
for e, c in effects.most_common():
    print(f"  {e}: {c}")

# 保存清单
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "剧本json", "_资源清单.json")
json.dump({
    "speakers": dict(speakers), "chars": dict(chars), "char_files": dict(char_files),
    "stages": dict(stages), "events": dict(events), "effects": dict(effects),
    "text_total": text_total, "scene_total": scene_total,
}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\n清单已保存: {out}")
