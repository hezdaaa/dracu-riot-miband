# -*- coding: utf-8 -*-
"""背景处理：裁切 7:10 → 336×480，量化压缩；生成黑/白屏图。
教程参数：PNG 18色 10%色散，背景 ≤12KB/张。"""
import os, sys, glob
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8")

SRC = r"E:\文档\桌面\gal\DR_extract\bgimage"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "common", "bg")
os.makedirs(OUT, exist_ok=True)

TW, TH = 336, 480  # 手环尺寸

def fit_crop(img, tw=TW, th=TH):
    """中心裁切为 tw:th 比例后缩放到 tw×th"""
    iw, ih = img.size
    target_ratio = tw / th  # 0.7
    img_ratio = iw / ih
    if img_ratio > target_ratio:  # 太宽，裁宽
        new_w = int(ih * target_ratio)
        x = (iw - new_w) // 2
        box = (x, 0, x + new_w, ih)
    else:  # 太高，裁高
        new_h = int(iw / target_ratio)
        y = (ih - new_h) // 2
        box = (0, y, iw, y + new_h)
    return img.crop(box).resize((tw, th), Image.LANCZOS)

def process():
    pngs = sorted(f for f in os.listdir(SRC) if f.endswith(".png"))
    ok, big = 0, []
    for f in pngs:
        im = Image.open(os.path.join(SRC, f)).convert("RGBA")
        # 白底（部分背景透明）
        bg = Image.new("RGB", im.size, (0, 0, 0))
        bg.paste(im, mask=im.split()[3])
        im = fit_crop(bg)
        # 量化压缩
        q = im.quantize(colors=18, method=Image.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
        out = os.path.join(OUT, os.path.splitext(f)[0] + ".png")
        q.save(out, optimize=True)
        sz = os.path.getsize(out) / 1024
        if sz > 12:
            big.append((f, f"{sz:.1f}KB"))
        else:
            ok += 1
    print(f"背景处理完成: {len(pngs)} 张, ≤12KB: {ok} 张")
    if big:
        print("超过 12KB 的:")
        for f, sz in big[:20]:
            print("  ", f, sz)
    # 生成黑/白屏
    for name, color in (("画面_黒", (0,0,0)), ("画面_白", (255,255,255))):
        Image.new("RGB", (TW, TH), color).save(os.path.join(OUT, name + ".png"), optimize=True)
    print("已生成 画面_黒/画面_白")

if __name__ == "__main__":
    process()
