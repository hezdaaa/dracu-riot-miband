# -*- coding: utf-8 -*-
"""修复立绘 PNG 的预乘 alpha(premultiplied alpha)问题
TLG 图层多为预乘存储(半透明像素 RGB = 真色×alpha),导致在浅色背景上
半透明边缘显示偏暗(变灰)。unmultiply 把 RGB 还原为真色。
用法: python fix_premultiply.py"""
import os, sys
import numpy as np
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8")

CIMG = r"E:\HP\Documents\1\DRACU-RIOT\src\common\cimg"

def unmultiply(path):
    im = Image.open(path).convert("RGBA")
    arr = np.array(im).astype(np.float32)
    a = arr[..., 3]
    mask = (a > 0) & (a < 255)
    if not mask.any():
        return False
    for c in range(3):
        ac = arr[..., c].copy()
        ac[mask] = np.clip(ac[mask] * 255.0 / a[mask], 0, 255)
        arr[..., c] = ac
    Image.fromarray(arr.astype(np.uint8)).save(path)
    return True

fixed = 0
for f in sorted(os.listdir(CIMG)):
    if not f.lower().endswith(".png"):
        continue
    p = os.path.join(CIMG, f)
    try:
        if unmultiply(p):
            fixed += 1
    except Exception as e:
        print(f"失败 {f}: {e}")

print(f"已 unmultiply {fixed} 张立绘 PNG")
