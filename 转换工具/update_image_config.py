# -*- coding: utf-8 -*-
"""更新 image-config.txt: cg/sd 列表中的被删图映射到保留图(大小写归一化)"""
import json, io, sys
sys.stdout.reconfigure(encoding="utf-8")
S = r"E:\HP\Documents\1\DRACU-RIOT\src\common"
P = S + r"\image-config.txt"
cg_map = json.load(io.open(S + r"\cg_map.json", encoding="utf-8"))
data = json.load(io.open(P, encoding="utf-8"))
for key in ("cg", "sd"):
    arr = data.get(key, [])
    new, changed = [], 0
    for item in arr:
        slash = item.rfind("/")
        base = item[slash + 1:]
        target = cg_map.get(base.lower())
        if target:
            new.append(item[:slash + 1] + target)
            changed += 1
        else:
            new.append(item)
    data[key] = new
    print(f"{key}: 映射 {changed} 项, 现 {len(new)} 项")
json.dump(data, io.open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("image-config.txt 已更新")
