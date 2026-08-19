# -*- coding: utf-8 -*-
"""CG 处理：向右旋转90° → fit(cover)裁切到 336×480 → jpg
教程：cg 向右旋转后 fit 裁切到 336×480，jpg 画质 32%"""
import os, sys, glob
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8")

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src外", "cg")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "common", "evig")
os.makedirs(OUT, exist_ok=True)
TW, TH = 336, 480
JPG_QUALITY = 32

def fit_cover(img, tw, th):
    """等比缩放铺满 + 中心裁切"""
    iw, ih = img.size
    scale = max(tw / iw, th / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    x = (nw - tw) // 2
    y = (nh - th) // 2
    return img.crop((x, y, x + tw, y + th))

def process():
    files = sorted(glob.glob(os.path.join(SRC, "*.png")))
    print(f"待处理 CG: {len(files)}")
    ok = 0
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        img = Image.open(f).convert("RGBA")
        # 白底（合成图有透明区域）
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        # 右旋90°（顺时针）
        rotated = bg.transpose(Image.ROTATE_270)
        # fit 336×480
        final = fit_cover(rotated, TW, TH)
        out = os.path.join(OUT, name + ".jpg")
        final.save(out, "JPEG", quality=JPG_QUALITY, optimize=True)
        ok += 1
    print(f"CG 处理完成: {ok} 张 -> src/common/evig/")
    # 统计大小
    sizes = [os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT) if f.endswith('.jpg')]
    if sizes:
        print(f"平均 {sum(sizes)/len(sizes)/1024:.0f}KB, 最大 {max(sizes)/1024:.0f}KB, 最小 {min(sizes)/1024:.0f}KB")

if __name__ == "__main__":
    process()
