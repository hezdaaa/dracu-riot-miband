# -*- coding: utf-8 -*-
import json, os
S = r"E:\HP\Documents\1\DRACU-RIOT\src\common"
r = json.load(open(os.path.join(S, "gallery_rules.json"), encoding="utf-8"))
chars = json.load(open(os.path.join(S, "char_data.txt"), encoding="utf-8"))

# 立绘: bodies = pose×dress 组合
new_chars = []
for name, poses in chars.items():
    bodies = []
    for pn, pd in poses.items():
        for dr, b in pd.get("bodies", {}).items():
            bodies.append({"pose": pn, "dress": dr, "img": b["img"],
                           "left": b.get("left", 0), "top": b.get("top", 0),
                           "w": b.get("w", 0), "h": b.get("h", 0)})
    faces = list((poses.get("1") or list(poses.values())[0]).get("face_map", {}).keys())
    new_chars.append({"name": name, "bodies": bodies, "faces": faces})

r["characters"] = new_chars
json.dump(r, open(os.path.join(S, "gallery_rules.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("规则已更新。角色样例:", json.dumps(new_chars[0], ensure_ascii=False)[:200])
