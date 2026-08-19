# -*- coding: utf-8 -*-
"""清理 cimg 中不被 char_data/image-config 引用的旧图"""
import json, os, sys, shutil
sys.stdout.reconfigure(encoding="utf-8")
S = r"E:\HP\Documents\1\DRACU-RIOT\src\common"
CIMG = os.path.join(S, "cimg")
BIMG = r"E:\HP\Documents\1\DRACU-RIOT\build\common\cimg"

keep = set()
j = json.load(open(os.path.join(S, "char_data.txt"), encoding="utf-8"))
for ch, ps in j.items():
    for pn, pd in ps.items():
        keep.add(pd["body"]["img"])
        for b in pd.get("bodies", {}).values():
            keep.add(b["img"])
        for f in pd.get("faces", {}).values():
            keep.add(f["img"])
ic = json.load(open(os.path.join(S, "image-config.txt"), encoding="utf-8"))
for item in ic.get("characters", []):
    keep.add(item.rsplit("/", 1)[-1])

allf = set(os.listdir(CIMG))
rm = sorted(allf - keep)
print(f"cimg 总 {len(allf)}, 保留 {len(keep)}, 待删 {len(rm)}")
for f in rm:
    os.remove(os.path.join(CIMG, f))
    bp = os.path.join(BIMG, f)
    if os.path.exists(bp):
        os.remove(bp)
print(f"已删除 {len(rm)} 张, cimg 剩余 {len(os.listdir(CIMG))}")
