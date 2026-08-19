# -*- coding: utf-8 -*-
"""CG 合成质量验证：
1. 局部差分(引用层<60%)的合成图与底图差异应小(≈层面积占比)
2. 合成图背景不应大面积变黑(底图选错会引入暗层)"""
import os, sys, glob, re, collections
from PIL import Image, ImageChops
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cg_compose import find_base
sys.stdout.reconfigure(encoding="utf-8")

CG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src外", "cg")
UNPACK = r"E:\文档\桌面\gal\DR_extract\evimage\拆解"

def diff_ratio(a, b):
    if a.size != b.size:
        return 1.0
    d = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
    nz = sum(1 for p in d.getdata() if p != (0, 0, 0))
    return nz / (a.size[0] * a.size[1])

def main():
    problems = []
    dark = []
    checked = 0
    for f in sorted(os.listdir(CG_DIR)):
        m = re.match(r'^(ev\d+)([a-z]{2})\.png$', f.lower())
        if not m:
            continue
        num, suf = m.group(1), m.group(2).upper()
        pimg = num + "a"
        jp = os.path.join(UNPACK, pimg + ".json")
        if not os.path.exists(jp):
            continue
        import json
        d = json.load(open(jp, encoding="utf-8"))
        W, H = d.get("width"), d.get("height")
        layers = {l["name"]: l for l in d.get("layers", [])}
        layer = layers.get(suf)
        if not layer:
            continue
        checked += 1
        ratio = layer["width"] * layer["height"] / (W * H)
        # 背景非黑检测
        img = Image.open(os.path.join(CG_DIR, f)).convert("RGB")
        sm = img.resize((64, 36))
        px = list(sm.getdata())
        nonblack = sum(1 for q in px if sum(q) > 30) / len(px)
        if nonblack < 0.5:
            dark.append((f, f"{nonblack:.0%}", f"{ratio:.0%}"))
        # 局部差分：与底图(find_base)差异应≈层占比
        if ratio < 0.6:
            base_layer = find_base(layers, W, H, pimg)
            if base_layer:
                bp = os.path.join(UNPACK, pimg, f"{base_layer['layer_id']}.png")
                if os.path.exists(bp):
                    base = Image.open(bp).convert("RGB")
                    diff = diff_ratio(base, img)
                    if diff > ratio + 0.3:  # 差异远大于差分面积 → 底图可能选错
                        problems.append((f, f"层占比{ratio:.0%} 但差异{diff:.0%}"))
    print(f"检查: {checked} 张")
    print(f"背景过暗(<50%非黑): {len(dark)}")
    for f, nb, r in dark[:30]:
        print(f"  {f}: 非黑{nb} 层占比{r}")
    print(f"\n底图疑似选错: {len(problems)}")
    for f, msg in problems[:30]:
        print(f"  {f}: {msg}")

if __name__ == "__main__":
    main()
