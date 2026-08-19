# -*- coding: utf-8 -*-
"""鉴赏模式规则提取器
- CG: 按 ev/sd 数字分组(ev101aa -> 组ev101 变体aa); 非 ev/sd 开头归入 other
- 立绘: 从 char_data 提取 角色/身体/表情 结构
输出: src/common/gallery_rules.json"""
import os, re, json, sys
sys.stdout.reconfigure(encoding="utf-8")
S = r"E:\HP\Documents\1\DRACU-RIOT\src\common"
evig = os.path.join(S, "evig")

# ---- CG 分组 ----
groups = {}
for f in sorted(os.listdir(evig)):
    m = re.match(r"^(ev\d+)([a-z]{2})\.jpg$", f, re.I)
    if m:
        g = m.group(1).lower()
        groups.setdefault(g, []).append(f)
        continue
    m2 = re.match(r"^(sd\d+)([a-z0-9]*)\.png$", f, re.I)
    if m2:
        g = m2.group(1).lower()
        groups.setdefault(g, []).append(f)
        continue
    groups.setdefault("other", []).append(f)

# 组内变体(后两位)排序
cg_groups = []
for g in sorted(groups):
    files = groups[g]
    if g == "other":
        cg_groups.append({"name": g, "files": files, "variants": []})
        continue
    variants = []
    for f in files:
        m = re.match(r"^(?:ev|sd)\d+(.*?)(\.\w+)$", f, re.I)
        variants.append(m.group(1) if m else f)
    cg_groups.append({"name": g, "files": files, "variants": sorted(set(variants))})

# ---- 立绘结构(char_data) ----
chars = json.load(open(os.path.join(S, "char_data.txt"), encoding="utf-8"))
char_list = []
for name, poses in chars.items():
    p1 = poses.get("1") or list(poses.values())[0]
    # 身体(服装)
    bodies = list(p1.get("bodies", {}).keys())
    # 表情
    faces = list(p1.get("face_map", {}).keys())
    char_list.append({"name": name, "bodies": bodies, "faces": faces})

out = {"cg_groups": cg_groups, "characters": char_list,
       "note": "ev/sd按数字分组, 变体为后两位; 立绘含角色/身体/表情"}
path = os.path.join(S, "gallery_rules.json")
json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"已生成 {path}")
print(f"CG组 {len(cg_groups)} (含other), 角色 {len(char_list)}")
for g in cg_groups[:4]:
    print(f"  {g['name']}: {len(g['files'])}张 变体{g['variants'][:4]}")
