# -*- coding: utf-8 -*-
"""SD 处理：按 sd处理.py 逻辑 → 336×480 透明 PNG 居中"""
import os, sys, glob
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8")

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src外", "sd")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "common", "sd")
os.makedirs(OUT, exist_ok=True)
TW, TH = 336, 480
RATIO = 7 / 10
OFFSET_Y = 15

def process():
    files = sorted(glob.glob(os.path.join(SRC, "*.png")))
    print(f"待处理 SD: {len(files)}")
    ok = 0
    for f in files:
        try:
            img = Image.open(f).convert("RGBA")
            w0, h0 = img.size
            # 中间 7:10 画布
            if w0 / h0 > RATIO:
                W_mid, H_mid = w0, int(w0 / RATIO)
            else:
                H_mid, W_mid = h0, int(h0 * RATIO)
            x_mid = (W_mid - w0) // 2
            y_mid = (H_mid - h0) // 2 - OFFSET_Y
            if y_mid < 0:
                y_mid = 0
            scale = TW / W_mid
            x_f = int(x_mid * scale)
            y_f = int(y_mid * scale)
            w_f = int(w0 * scale)
            h_f = int(h0 * scale)
            final = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
            resized = img.resize((w_f, h_f), Image.LANCZOS)
            final.paste(resized, (x_f, y_f), resized)
            clean = Image.frombytes("RGBA", final.size, final.tobytes())
            clean.save(os.path.join(OUT, os.path.basename(f)), "PNG")
            ok += 1
        except Exception as e:
            print(f"!! {os.path.basename(f)}: {e}")
    print(f"SD 处理完成: {ok} 张 -> src/common/sd/")

if __name__ == "__main__":
    process()
