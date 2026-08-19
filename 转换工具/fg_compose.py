# -*- coding: utf-8 -*-
"""DR 立绘合成器：TLG→PNG + 按规则txt合成（参照 krkrFgiEditor 逻辑）
合成 = 包围盒画布 + 逐层 DrawImage，alpha 大铺底，opacity 应用透明"""
import os, sys, glob, subprocess
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8")

IMAGE_CONVERT = r"E:\文档\桌面\文件\杂项\KRKR解包工具\GARbro2\Image.Convert.exe"

def tlg_to_png(directory):
    """批量 tlg → png"""
    tlgs = glob.glob(os.path.join(directory, "*.tlg"))
    done = 0
    for t in tlgs:
        png = os.path.splitext(t)[0] + ".png"
        if os.path.exists(png):
            done += 1
            continue
        subprocess.run([IMAGE_CONVERT, "-t", "png", os.path.basename(t)],
                       cwd=directory, capture_output=True)
        done += 1
    return done

def parse_rule(txt_path):
    """读规则 txt → 层列表 {name,left,top,opacity,layer_id}"""
    for enc in ('shift_jis', 'gbk', 'utf-8'):
        try:
            s = open(txt_path, encoding=enc).read()
            break
        except Exception:
            continue
    layers = []
    for line in s.splitlines():
        if not line or line.startswith('#'):
            continue
        attrs = line.split('\t')
        if len(attrs) >= 10 and attrs[0] == "0":
            try:
                layers.append({
                    "name": attrs[1], "left": int(attrs[2]), "top": int(attrs[3]),
                    "opacity": int(attrs[7]), "layer_id": int(attrs[9]),
                })
            except (ValueError, IndexError):
                pass
    return layers

def alpha_sum(img):
    """图层 alpha 像素总和（排序用，alpha 大铺底）"""
    a = img.split()[3] if img.mode == "RGBA" else None
    if a is None:
        return 0
    return sum(a.getdata())

def compose(rule_path, char_dir, layer_ids):
    """合成指定 layer_id 的图层"""
    layers = parse_rule(rule_path)
    # 选层
    sel = [l for l in layers if l["layer_id"] in layer_ids]
    if not sel:
        return None
    # 加载图片 + 计算 alpha
    for l in sel:
        png = os.path.join(char_dir, f"{os.path.splitext(os.path.basename(rule_path))[0]}_{l['layer_id']}.png")
        l["img"] = Image.open(png).convert("RGBA")
        l["alphas"] = alpha_sum(l["img"]) * l["opacity"] // 255
    # 排序（alpha 大铺底）
    sel.sort(key=lambda x: -x["alphas"])
    # 包围盒
    left = min(l["left"] for l in sel)
    top = min(l["top"] for l in sel)
    right = max(l["left"] + l["img"].width for l in sel)
    bottom = max(l["top"] + l["img"].height for l in sel)
    canvas = Image.new("RGBA", (right - left, bottom - top), (0, 0, 0, 0))
    for l in sel:
        img = l["img"]
        if l["opacity"] != 255:
            a = img.split()[3].point(lambda v: int(v * l["opacity"] / 255))
            img = Image.merge("RGBA", (*img.split()[:3], a))
        canvas.paste(img, (l["left"] - left, l["top"] - top), img)
    return canvas

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法: python fg_compose.py <角色目录> <规则txt> <layer_ids...>")
        sys.exit(1)
    char_dir, rule = sys.argv[1], sys.argv[2]
    ids = [int(x) for x in sys.argv[3:]]
    tlg_to_png(char_dir)
    img = compose(rule, char_dir, ids)
    if img:
        out = os.path.join(char_dir, f"_compose_{'_'.join(map(str,ids))}.png")
        img.convert("RGB").save(out)
        print(f"合成完成: {out} {img.size}")
    else:
        print("合成失败")
