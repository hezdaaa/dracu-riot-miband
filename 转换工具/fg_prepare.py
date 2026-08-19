# -*- coding: utf-8 -*-
"""立绘实时拼装数据准备：解析角色规则txt → 身体+表情坐标JSON
- 身体层：dress（如 581私服/826水着），作为立绘基准
- 表情层：face 编号 → layer，offset 相对身体
- 参照 krkrFgiEditor：offset = 层left/top - 身体left/top"""
import os, sys, json, re, glob
sys.stdout.reconfigure(encoding="utf-8")

FG = r"E:\文档\桌面\gal\DR_extract\fgimage"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "剧本json", "_立绘坐标.json")

def parse_rule(txt_path):
    for enc in ('shift_jis', 'gbk', 'utf-8'):
        try:
            s = open(txt_path, encoding=enc).read()
            break
        except Exception:
            continue
    layers = {}
    for line in s.splitlines():
        if not line or line.startswith('#'):
            continue
        a = line.split('\t')
        if len(a) >= 10 and a[0] == "0":
            try:
                name = a[1].strip()
                lid = int(a[9])
                m = re.match(r'^(\d+)', name)
                num = int(m.group(1)) if m else None
                layers[lid] = {"name": name, "left": int(a[2]), "top": int(a[3]),
                               "w": int(a[4]), "h": int(a[5]), "face_num": num}
            except (ValueError, IndexError):
                pass
    return layers

def build_character(char_dir, rule_name):
    """构建角色坐标：身体层 + 表情层"""
    rule = os.path.join(char_dir, rule_name + ".txt")
    if not os.path.exists(rule):
        return None
    layers = parse_rule(rule)
    # 身体层：全身立绘（高>2000），排除 背景/顔表示/腕差分
    bodies = {}  # name -> {layer_id, left, top, w, h}
    for lid, l in layers.items():
        if l["h"] > 2000 and l["name"] not in ("背景",) and "腕差分" not in l["name"]:
            bodies[l["name"]] = {"layer_id": lid, "left": l["left"], "top": l["top"], "w": l["w"], "h": l["h"]}
    if not bodies:
        return None
    # 表情层：非身体层（排除高>2000 的）
    body_ids = {v["layer_id"] for v in bodies.values()}
    faces = {}
    for lid, l in layers.items():
        if lid not in body_ids and l["name"] not in ("背景",):
            faces[lid] = l
    # 主身体（第一个）
    body_name = list(bodies)[0]
    body = bodies[body_name]
    # 表情 offset 相对身体
    face_map = {}
    for lid, l in faces.items():
        face_map[str(lid)] = {
            "name": l["name"],
            "offset_x": l["left"] - body["left"],
            "offset_y": l["top"] - body["top"],
            "w": l["w"], "h": l["h"],
        }
    return {
        "rule": rule_name,
        "body": {"name": body_name, **body},
        "bodies": bodies,
        "faces": face_map,
    }

if __name__ == "__main__":
    # 测试直太
    result = build_character(os.path.join(FG, "直太"), "直太a")
    if result:
        print("=== 直太 立绘坐标 ===")
        print("身体层:", {k: v for k, v in result["bodies"].items()})
        print("表情层数:", len(result["faces"]))
        for lid, f in list(result["faces"].items())[:6]:
            print(f"  layer {lid}: {f['name'][:10]:<12} offset=({f['offset_x']},{f['offset_y']})")
        json.dump(result, open("_直太_test.json", "w", encoding='utf-8'), ensure_ascii=False, indent=1)
        print("已保存测试 JSON")
