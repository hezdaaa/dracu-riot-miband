# -*- coding: utf-8 -*-
"""压缩 src/common/cimg 下的立绘 PNG，压缩后同步到 build/common/cimg
- 身体图(_body_)目标 <=30KB，其余 PNG 目标 <=20KB
- 先试 PNG optimize 原图(不量化)；超目标再量化 256->128->64->32 色
- 保留 alpha 透明(量化保留 alpha 梯度)
用法: python compress_cimg.py [--dry]"""
import os, sys, io, shutil
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8")

CIMG = r"E:\HP\Documents\1\DRACU-RIOT\src\common\cimg"
BCIMG = r"E:\HP\Documents\1\DRACU-RIOT\build\common\cimg"
BODY_TARGET = 30_000
OTHER_TARGET = 20_000
DRY = "--dry" in sys.argv

def save_png(im, fmt="PNG", optimize=True, colors=None):
    buf = io.BytesIO()
    if colors:
        # RGBA 量化只支持 FastOctree；dither 对 octree 无效，不设
        q = im.quantize(colors=colors, method=Image.Quantize.FASTOCTREE)
        q.save(buf, "PNG", optimize=optimize)
    else:
        im.save(buf, "PNG", optimize=optimize)
    return buf.getvalue()

def compress(path):
    """返回 (新字节, 压缩标志)"""
    with Image.open(path) as im:
        im.load()
        if im.mode != "RGBA":
            im = im.convert("RGBA")
    target = BODY_TARGET if "_body_" in os.path.basename(path) else OTHER_TARGET
    # 1) 原图 optimize
    data = save_png(im)
    if len(data) <= target:
        return data, "opt"
    # 2) 量化自适应
    for colors in (256, 128, 64, 32):
        data = save_png(im, colors=colors)
        if len(data) <= target:
            return data, f"q{colors}"
    return data, "q32"

total_before = total_after = 0
n_changed = n_skipped = 0
for f in sorted(os.listdir(CIMG)):
    if not f.lower().endswith(".png"):
        continue
    p = os.path.join(CIMG, f)
    if not os.path.exists(p):
        continue   # 跳过(文件已清理/列表延迟)
    before = os.path.getsize(p)
    if DRY:
        # 试算
        data, mode = compress(p)
        total_before += before
        total_after += len(data)
        if len(data) < before:
            n_changed += 1
        print(f"  {f:<48} {before//1024:>4}KB -> {len(data)//1024:>3}KB [{mode}]")
        continue
    data, mode = compress(p)
    total_before += before
    total_after += len(data)
    if len(data) < before:
        with open(p, "wb") as fh:
            fh.write(data)
        n_changed += 1
    else:
        n_skipped += 1

print(f"\n=== 结果 ===")
print(f"PNG 数: {len([f for f in os.listdir(CIMG) if f.lower().endswith('.png')])}")
print(f"压缩: {n_changed} 张, 跳过(已达标): {n_skipped} 张")
print(f"总大小: {total_before//1024//1024}MB -> {total_after//1024//1024}MB "
      f"({total_after/max(total_before,1)*100:.0f}%)")

if not DRY:
    # 同步到 build
    if os.path.isdir(BCIMG):
        for f in os.listdir(CIMG):
            if f.lower().endswith(".png"):
                shutil.copy2(os.path.join(CIMG, f), os.path.join(BCIMG, f))
        print(f"已同步到 build/common/cimg ({len(os.listdir(BCIMG))} 张)")
