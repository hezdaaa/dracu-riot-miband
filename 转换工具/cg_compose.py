# -*- coding: utf-8 -*-
"""CG 差分合成：底图 + 差分层 → 完整 CG。
规则：全屏层(>=画布90%)直接作为完整图；差分层合成到底图上。
输出到 src 外目录，命名与剧本引用一致（evXXXyy）。"""
import json, os, sys, glob, re
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8")

UNPACK_DIR = r"E:\文档\桌面\gal\DR_extract\evimage\拆解"
SCRIPT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "手环脚本")
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src外", "cg")
os.makedirs(OUT_DIR, exist_ok=True)

def get_layers(pimg):
    """读取 pimg 拆解 json，返回 (layers_dict, 画布W, 画布H)"""
    jp = os.path.join(UNPACK_DIR, pimg + ".json")
    if not os.path.exists(jp):
        return None
    d = json.load(open(jp, encoding="utf-8"))
    layers = {l["name"]: l for l in d.get("layers", [])}
    return layers, d.get("width", 1280), d.get("height", 720)

_base_cache = {}

def _nonblack_ratio(path):
    """读缩略图，计算内容比例：不透明且非黑的像素占比"""
    im = Image.open(path).convert("RGBA")
    im.thumbnail((32, 18))
    px = list(im.getdata())
    return sum(1 for (r, g, b, a) in px if a > 200 and (r + g + b) > 90) / len(px)

def find_base(layers, W, H, pimg):
    """选底图：全屏层(≥60%)中内容最丰富(非黑比例最高)的层；
    无全屏层则选面积最大层(≥40%)。结果缓存。"""
    if pimg in _base_cache:
        return _base_cache[pimg]
    canvas = W * H
    full = [l for l in layers.values() if l["width"] * l["height"] / canvas >= 0.6]
    if full:
        best, best_nb = None, -1
        for l in full:
            p = os.path.join(UNPACK_DIR, pimg, f"{l['layer_id']}.png")
            if not os.path.exists(p):
                continue
            nb = _nonblack_ratio(p)
            if nb > best_nb:
                best, best_nb = l, nb
        _base_cache[pimg] = best
        return best
    best, best_ratio = None, 0
    for l in layers.values():
        ratio = l["width"] * l["height"] / canvas
        if ratio >= 0.4 and ratio > best_ratio:
            best, best_ratio = l, ratio
    _base_cache[pimg] = best
    return best

def compose_cg(pimg, layer_name):
    """合成一张 CG 差分：底图(面积最大层) + 引用层叠加"""
    res = get_layers(pimg)
    if not res:
        return None
    layers, W, H = res
    layer = layers.get(layer_name)
    if not layer:
        return None
    tid = layer["layer_id"]
    tex_path = os.path.join(UNPACK_DIR, pimg, f"{tid}.png")
    if not os.path.exists(tex_path):
        return None
    tex = Image.open(tex_path).convert("RGBA")
    base_layer = find_base(layers, W, H, pimg)
    # 引用层就是底图 → 直接用
    if not base_layer or base_layer["layer_id"] == layer["layer_id"]:
        return tex
    bp = os.path.join(UNPACK_DIR, pimg, f"{base_layer['layer_id']}.png")
    if not os.path.exists(bp):
        return tex
    base = Image.open(bp).convert("RGBA")
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    canvas.paste(base, (base_layer["left"], base_layer["top"]), base)
    canvas.paste(tex, (layer["left"], layer["top"]), tex)
    return canvas

def main():
    # 收集剧本引用的 evXXXyy
    refs = {}
    for p in glob.glob(os.path.join(SCRIPT_DIR, "*.json")):
        if ".map.json" in p:
            continue
        d = json.load(open(p, encoding="utf-8"))
        for v in d.values():
            cg = v.get("cg", "")
            if cg:
                refs[cg] = refs.get(cg, 0) + 1
    # 解析 evXXX + 层名
    done = fail = 0
    for cg in sorted(refs, key=lambda x: (-refs[x], x)):
        m = re.match(r'^ev(\d+)([a-zA-Z]+)$', cg, re.I)
        if not m:
            continue
        num, layer = m.group(1).lower(), m.group(2).upper()
        pimg = "ev" + num + "a"
        img = compose_cg(pimg, layer)
        if img is None:
            fail += 1
            print(f"!! 无法合成 {cg} (pimg={pimg} layer={layer})")
            continue
        # 统一命名小写，去 .png
        out = os.path.join(OUT_DIR, cg.lower().split(".")[0] + ".png")
        img.convert("RGB").save(out)
        done += 1
    print(f"\nCG 合成: 成功 {done}, 失败 {fail}")

if __name__ == "__main__":
    main()
