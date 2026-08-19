# -*- coding: utf-8 -*-
"""立绘实时拼装素材准备（多姿势支持）：按 .stand 块(a/b/c)生成每 pose 的身体+表情
- pose N → stand 块[N-1]（a=pose1, b=pose2, c=pose3），超出用最后块
- 身体：裁顶部55%(半身)，缩放适配；表情：同比例 + offset"""
import os, sys, json, glob, re, subprocess
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8")

IC = r"E:\文档\桌面\文件\杂项\KRKR解包工具\GARbro2\Image.Convert.exe"
FG = r"E:\文档\桌面\gal\DR_extract\fgimage"
OUT_IMG = r"E:\HP\Documents\1\DRACU-RIOT\src\common\cimg"
OUT_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "剧本json", "_立绘拼装.json")
SRC_DATA = r"E:\HP\Documents\1\DRACU-RIOT\src\common\立绘数据.json"
os.makedirs(OUT_IMG, exist_ok=True)
DISPLAY_H = 480
CROP_RATIO = 0.55

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
                m = re.match(r'^(\d+)', name)
                layers[int(a[9])] = {"name": name, "left": int(a[2]), "top": int(a[3]),
                                     "w": int(a[4]), "h": int(a[5]), "num": int(m.group(1)) if m else None}
            except (ValueError, IndexError):
                pass
    return layers

def read_stand_blocks(char):
    """读角色 .stand → 块列表（规则文件名）"""
    sp = os.path.join(FG, char + ".stand")
    if not os.path.exists(sp):
        return [char + "a"]
    for enc in ('shift_jis', 'gbk', 'utf-8'):
        try:
            s = open(sp, encoding=enc).read()
            break
        except Exception:
            continue
    blocks = re.findall(r"filename:'([^']+)'", s)
    return blocks or [char + "a"]

def build_pose(char, rule_name, prefix):
    """生成一个 pose（块）的数据：身体+表情"""
    char_dir = os.path.join(FG, char)
    rule = os.path.join(char_dir, rule_name + ".txt")
    if not os.path.exists(rule):
        return None
    layers = parse_rule(rule)
    # 身体（全身高>2000，排除背景/腕差分）
    bodies = {}
    for lid, l in layers.items():
        if l["h"] > 2000 and l["name"] not in ("背景",) and "腕差分" not in l["name"]:
            bodies[l["name"]] = lid
    if not bodies:
        return None
    body_name = list(bodies)[0]
    body_lid = bodies[body_name]
    body = layers[body_lid]
    # 表情（非身体层）
    body_ids = set(bodies.values())
    face_lids = [lid for lid, l in layers.items() if lid not in body_ids and l["name"] not in ("背景",)]
    # 缩放
    crop_h = int(body["h"] * CROP_RATIO)
    scale = DISPLAY_H / crop_h
    # 转换身体图
    tlg = os.path.join(char_dir, f"{rule_name}_{body_lid}.tlg")
    if not os.path.exists(tlg):
        return None
    subprocess.run([IC, "-t", "png", os.path.basename(tlg)], cwd=char_dir, capture_output=True)
    body_img = Image.open(os.path.join(char_dir, f"{rule_name}_{body_lid}.png")).convert("RGBA")
    body_crop = body_img.crop((0, 0, body_img.width, int(body_img.height * CROP_RATIO)))
    body_resized = body_crop.resize((int(body_crop.width * scale), DISPLAY_H), Image.LANCZOS)
    body_file = f"{prefix}_{body_lid}.png"
    body_resized.save(os.path.join(OUT_IMG, body_file))
    # 表情图 + offset
    faces = {}
    for fid in face_lids:
        tlg = os.path.join(char_dir, f"{rule_name}_{fid}.tlg")
        if not os.path.exists(tlg):
            continue
        subprocess.run([IC, "-t", "png", os.path.basename(tlg)], cwd=char_dir, capture_output=True)
        fimg = Image.open(os.path.join(char_dir, f"{rule_name}_{fid}.png")).convert("RGBA")
        fw, fh = max(int(fimg.width * scale), 1), max(int(fimg.height * scale), 1)
        fimg_r = fimg.resize((fw, fh), Image.LANCZOS)
        ffile = f"{prefix}_{fid}.png"
        fimg_r.save(os.path.join(OUT_IMG, ffile))
        faces[str(fid)] = {
            "img": ffile,
            "x": int((layers[fid]["left"] - body["left"]) * scale),
            "y": int((layers[fid]["top"] - body["top"]) * scale),
            "w": fw, "h": fh,
            "face_num": layers[fid].get("num"),
        }
    # face_map
    face_map = {}
    for lid, l in layers.items():
        if l.get("num") is not None and l["num"] > 0:
            face_map[str(l["num"])] = str(lid)
    # 默认表情（名字"表情"层）
    base_id = None
    for lid, l in layers.items():
        if l["name"] == "表情":
            base_id = str(lid)
            break
    if base_id is None and faces:
        base_id = list(faces.keys())[0]
    face_map["1"] = base_id
    return {
        "body": {"img": body_file, "w": body_resized.width, "h": DISPLAY_H},
        "bodies": {n: {"layer": bodies[n], "img": f"{prefix}_{bodies[n]}.png"} for n in bodies},
        "faces": faces,
        "face_map": face_map,
    }

if __name__ == "__main__":
    data = {}
    for char in sorted(os.listdir(FG)):
        dp = os.path.join(FG, char)
        if not os.path.isdir(dp):
            continue
        blocks = read_stand_blocks(char)
        poses = {}
        for i, rule_name in enumerate(blocks):
            pose_num = str(i + 1)
            suffix = rule_name[len(char):] if rule_name.startswith(char) else chr(97 + i)
            prefix = f"{char}_{suffix}"
            result = build_pose(char, rule_name, prefix)
            if result:
                poses[pose_num] = result
        if poses:
            data[char] = poses
    json.dump(data, open(OUT_DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import shutil
    shutil.copy(OUT_DATA, SRC_DATA)
    print(f"多姿势立绘数据: {len(data)} 角色 -> {OUT_DATA}")
    for c, poses in data.items():
        print(f"  {c}: pose {list(poses.keys())}")
