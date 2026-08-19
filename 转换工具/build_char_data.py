# -*- coding: utf-8 -*-
"""DR 立绘实时拼装数据重建器 v3（姿势差分正确版）

核心规则（从剧本 64,866 条立绘引用的 face 归属统计得出）:
  * stand 块 = 姿势差分集。pose=N → 块[N-1]（越界取最后块）
  * 每个姿势块有自己的一套表情规则（{base}_info.txt 的 face 定义）
  * 表情表 = 该 pose 块优先，face 不在该块时按块序回退（a→b→c）
    例: 美羽 pose=1 用 a 表(face02=笑顔1)；pose=2 用 b 表(face02=笑顔2)；
        但 face21-37 仅 a 有 → pose=2 回退到 a 的图层
  * 身体层 = 该 pose 块内 dress 的全部差分图层合成（主体+指+腕差分）
  * 多图层表情（如 04h=焦る+頬）预合成单张

输出: src/common/char_data.txt（播放器读取）+ 立绘数据.json
"""
import os, sys, glob, re, json, subprocess, collections
import numpy as np
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8")

FG = r"E:\文档\桌面\gal\DR_extract\fgimage"
SRC = r"E:\HP\Documents\1\DRACU-RIOT\src\common"
OUT_IMG = os.path.join(SRC, "cimg")
OUT_DATA_TXT = os.path.join(SRC, "char_data.txt")
OUT_DATA_JSON = os.path.join(SRC, "立绘数据.json")
IC = r"E:\文档\桌面\文件\杂项\KRKR解包工具\GARbro2\Image.Convert.exe"
TARGET_W = 320
SCALE_MIN, SCALE_MAX = 0.15, 0.6

def read_decode(path):
    for enc in ("shift_jis", "gbk", "utf-8"):
        try:
            return open(path, "rb").read().decode(enc)
        except Exception:
            continue
    return ""

def parse_layer_txt(path):
    out = {}
    for ln in read_decode(path).splitlines():
        if not ln or ln.startswith("#"):
            continue
        a = ln.split("\t")
        if len(a) >= 10 and a[0] == "0":
            try:
                out[int(a[9])] = {"name": a[1], "left": int(a[2]), "top": int(a[3]),
                                  "w": int(a[4]), "h": int(a[5]), "visible": int(a[8])}
            except (ValueError, IndexError):
                pass
    return out

def norm_name(s):
    s = s.strip()
    s = re.sub(r"[\s　]+", "", s)
    s = re.sub(r"^[０-９\d]+", "", s)
    return s

def parse_info(path):
    face_map, dress_map = collections.defaultdict(list), collections.defaultdict(list)
    for ln in read_decode(path).splitlines():
        p = ln.split("\t")
        if len(p) >= 4 and p[0] == "face" and p[2] == "base":
            face_map[p[1]].append(p[3])
        elif len(p) >= 5 and p[0] == "dress" and p[2] == "diff":
            dress_map[p[1]].append((p[3], p[4]))
    return face_map, dress_map

def resolve_names(layers, names):
    by_name = {}
    for lid, l in layers.items():
        by_name.setdefault(l["name"].strip(), []).append(lid)
        by_name.setdefault(norm_name(l["name"]), []).append(lid)
    lids = []
    for n in names:
        cand = by_name.get(n.strip()) or by_name.get(norm_name(n))
        if cand:
            lids.extend(cand)
    return sorted(set(lids))

def tlg_to_png(char_dir, base, lid):
    png = os.path.join(char_dir, f"{base}_{lid}.png")
    if not os.path.exists(png):
        tlg = os.path.join(char_dir, f"{base}_{lid}.tlg")
        if not os.path.exists(tlg):
            return None
        subprocess.run([IC, "-t", "png", os.path.basename(tlg)], cwd=char_dir, capture_output=True)
    return png if os.path.exists(png) else None

def alpha_sum(img):
    a = img.split()[3] if img.mode == "RGBA" else None
    return sum(a.getdata()) if a else 0

def unmultiply_if_premultiplied(im):
    """检测预乘 alpha 的图层并 unmultiply。
    预乘图层: 半透明像素 RGB=真色×alpha(偏暗), 浅色背景会显灰 → 还原真色。
    非预乘(亮色如頬): unmultiply 会过白 → 跳过。"""
    arr = np.array(im).astype(np.float32)
    a = arr[..., 3]
    mask = (a > 0) & (a < 255) & (a > 30)
    if not mask.any():
        return im
    ur = np.clip(arr[..., 0][mask] * 255 / a[mask], 0, 255).mean()
    ug = np.clip(arr[..., 1][mask] * 255 / a[mask], 0, 255).mean()
    ub = np.clip(arr[..., 2][mask] * 255 / a[mask], 0, 255).mean()
    if ur > 245 and ug > 245 and ub > 245:
        return im  # 非预乘(本来就亮), 保持原样
    for c in range(3):
        ac = arr[..., c].copy()
        ac[mask] = np.clip(ac[mask] * 255.0 / a[mask], 0, 255)
        arr[..., c] = ac
    return Image.fromarray(arr.astype(np.uint8))

def premult_resize(im, size):
    """预乘 alpha 的 resize: 缩放时半透明像素与透明(黑)混合会产生暗边,
    先 RGB×alpha 再缩放再还原, 避免黑边。"""
    arr = np.array(im).astype(np.float32)
    a = arr[..., 3:4] / 255.0
    rgb = arr[..., :3] * a
    imp = Image.fromarray(
        np.concatenate([rgb, arr[..., 3:4]], axis=-1).astype(np.uint8)
    ).resize(size, Image.LANCZOS)
    arr2 = np.array(imp).astype(np.float32)
    a2 = arr2[..., 3:4] / 255.0
    a2 = np.where(a2 > 0, a2, 1)
    out = np.concatenate([np.clip(arr2[..., :3] / a2, 0, 255), arr2[..., 3:4]], axis=-1)
    return Image.fromarray(out.astype(np.uint8))

def compose_layers(items):
    if not items:
        return None, 0, 0
    imgs = []
    for p, l, t, op in items:
        im = Image.open(p).convert("RGBA")
        im = unmultiply_if_premultiplied(im)   # 合成前修复预乘图层
        if op != 255:
            al = im.split()[3].point(lambda v: int(v * op / 255))
            im = Image.merge("RGBA", (*im.split()[:3], al))
        imgs.append((im, l, t))
    left = min(x[1] for x in items)
    top = min(x[2] for x in items)
    right = max(x1 + im.width for im, x1, x2 in imgs)
    bottom = max(x2 + im.height for im, x1, x2 in imgs)
    canvas = Image.new("RGBA", (right - left, bottom - top), (0, 0, 0, 0))
    order = sorted(range(len(imgs)), key=lambda i: -alpha_sum(imgs[i][0]))
    for i in order:
        im, l, t = imgs[i]
        # paste 对半透明像素会引入暗边, 改用标准 alpha 混合(alpha_composite)
        tmp = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        tmp.paste(im, (l - left, t - top))
        canvas.alpha_composite(tmp)
    return canvas, left, top

def read_stand_blocks(char):
    sp = os.path.join(FG, char + ".stand")
    if not os.path.exists(sp):
        return [(char + "a", 0)]
    blocks = []
    for m in re.finditer(r"filename:'([^']+)'[^}]*?yoffset:(-?\d+)", read_decode(sp)):
        blocks.append((m.group(1), int(m.group(2))))
    return blocks or [(char + "a", 0)]

# ---------- 第一步: 解析全部角色/base ----------
chars = {}
for char in sorted(os.listdir(FG)):
    dp = os.path.join(FG, char)
    if not os.path.isdir(dp):
        continue
    for base, _ in read_stand_blocks(char):
        rule = os.path.join(dp, base + ".txt")
        info = os.path.join(dp, base + "_info.txt")
        if not (os.path.exists(rule) and os.path.exists(info)):
            continue
        layers = parse_layer_txt(rule)
        fmap, dmap = parse_info(info)
        face = {}
        for fv, names in fmap.items():
            lids = resolve_names(layers, names)
            if lids:
                face[fv] = lids
        dress = {}
        for dr, items in dmap.items():
            m = collections.defaultdict(list)
            for diff, n in items:
                for lid in resolve_names(layers, [n]):
                    m[diff].append(lid)
            dress[dr] = dict(m)
        chars.setdefault(char, {})[base] = {"face": face, "dress": dress, "layers": layers}

# ---------- 第二步: 全局 scale ----------
all_w = []
for char, bs in chars.items():
    for base, bd in bs.items():
        for lid, l in bd["layers"].items():
            if l["h"] > 2000 and l["name"] not in ("背景",) and "腕差分" not in l["name"]:
                all_w.append(l["w"])
gscale = max(SCALE_MIN, min(SCALE_MAX, TARGET_W / (sum(all_w) / len(all_w)))) if all_w else 0.35
print(f"全局 scale = {gscale:.4f}")
os.makedirs(OUT_IMG, exist_ok=True)

# ---------- 第二步半: 剧本中每角色出现的最大 pose 编号 ----------
JSON_DIR = r"E:\文档\桌面\dr移植\剧本json"
max_pose = collections.defaultdict(int)
for p in glob.glob(os.path.join(JSON_DIR, "*.json")):
    if ".resx" in p or not p.endswith(".ks.json"):
        continue
    d = json.load(open(p, encoding="utf-8"))
    def _walk(o):
        if isinstance(o, dict):
            img = o.get("imageFile")
            if isinstance(img, dict) and o.get("cname") == "character" and img.get("file"):
                f = img["file"].rsplit(".", 1)[0]
                po = str((img.get("options") or {}).get("pose") or "1")
                if po.isdigit():
                    max_pose[f] = max(max_pose[f], int(po))
            for v in o.values():
                _walk(v)
        elif isinstance(o, list):
            for v in o:
                _walk(v)
    _walk(d)

# ---------- 第三步: 逐角色构建（每 pose 独立表情表）----------
data = {}
for char, bs in chars.items():
    blocks = [b for b, _ in read_stand_blocks(char) if b in bs]
    if not blocks:
        continue
    char_dir = os.path.join(FG, char)
    all_faces = sorted({f for b in blocks for f in bs[b]["face"]})

    # 每块的 pose 集合(从 dress diff 键)
    block_poses = {}
    for b in blocks:
        ps = set()
        for dr, diffs in bs[b]["dress"].items():
            ps |= set(diffs.keys())
        block_poses[b] = ps

    poses = {}
    n_poses = max(max_pose.get(char, 1), 1)
    for pose_num in range(1, n_poses + 1):
        pn = str(pose_num)
        # pose->块: 第一个包含该 pose 的块(引擎 currentPoseNameMap), 越界用最后块
        base = next((b for b in blocks if pn in block_poses[b]), blocks[-1])
        bd = bs[base]

        # --- 表情表 = 该块的 face 定义(引擎: 无跨块回退, 缺则默认表情) ---
        faces = {}
        for fv, lids in bd["face"].items():
            items = []
            for lid in lids:
                p = tlg_to_png(char_dir, base, lid)
                if p:
                    l = bd["layers"][lid]
                    items.append((p, l["left"], l["top"], 255))
            if not items:
                continue
            if len(items) == 1:
                p = items[0][0]
                im = Image.open(p).convert("RGBA")
                im = unmultiply_if_premultiplied(im)   # 修复预乘
                nw, nh = max(int(im.width * gscale), 1), max(int(im.height * gscale), 1)
                fname = f"{char}_{base}_{lids[0]}.png"
                premult_resize(im, (nw, nh)).save(os.path.join(OUT_IMG, fname))
                l = bd["layers"][lids[0]]
                faces[fv] = {"img": fname, "left": l["left"], "top": l["top"],
                             "w": l["w"], "h": l["h"]}
            else:
                img, bl, bt = compose_layers(items)
                nw, nh = max(int(img.width * gscale), 1), max(int(img.height * gscale), 1)
                fname = f"{char}_{base}_face_{fv}.png"
                premult_resize(img, (nw, nh)).save(os.path.join(OUT_IMG, fname))
                faces[fv] = {"img": fname, "left": bl, "top": bt, "w": img.width, "h": img.height}

        # --- 身体层: 只合成"当前 pose 编号对应的 diff 图层组" ---
        # dress diff 编号 == pose 编号(如 美羽a: diff1=私服+指, diff2=私服腕差分),
        # 它们是互斥的不同姿势身体, 不能全部叠加
        bodies = {}
        for dr, diffs in bd["dress"].items():
            # diffs 键是字符串 pose 编号, pose_num 是 int, 必须转 str
            lids = list(diffs.get(pn, []))
            items = []
            for lid in lids:
                l = bd["layers"][lid]
                if l["w"] <= 0 or l["h"] <= 0 or l["name"].strip() in ("空", ""):
                    continue   # 跳过空/占位层(如 おじい様 的 dress 空层)
                p = tlg_to_png(char_dir, base, lid)
                if p:
                    items.append((p, l["left"], l["top"], 255))
            # 兜底: 该 pose 无对应 diff 层时,用块内可见层作身体锚点(半身立绘如 おじい様)
            if not items:
                for lid, l in sorted(bd["layers"].items(), key=lambda kv: -kv[1]["visible"]):
                    if l["w"] <= 0 or l["h"] <= 0 or l["name"].strip() in ("空", "背景"):
                        continue
                    p = tlg_to_png(char_dir, base, lid)
                    if p:
                        items.append((p, l["left"], l["top"], 255))
                        break
            if not items:
                continue
            img, bl, bt = compose_layers(items)
            nw, nh = max(int(img.width * gscale), 1), max(int(img.height * gscale), 1)
            # 命名含 pose 编号, 避免不同 pose 的 body 图互相覆盖
            bname = f"{char}_{base}_body_{dr}_p{pose_num}.png"
            premult_resize(img, (nw, nh)).save(os.path.join(OUT_IMG, bname))
            bodies[dr] = {"img": bname, "left": bl, "top": bt, "w": nw, "h": nh, "scale": gscale}
        if not bodies:
            continue
        main = list(bodies)[0]
        poses[pose_num] = {
            "body": {**bodies[main], "name": main},
            "bodies": bodies,
            "faces": faces,
            "face_map": {fv: fv for fv in faces},   # 值=faces 的 key（face 值本身）
            "vy": 0,
            "scale": gscale,
        }
    if poses:
        data[char] = poses

json.dump(data, open(OUT_DATA_TXT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(data, open(OUT_DATA_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"已生成: {OUT_DATA_TXT}  ({len(data)} 角色)")
for c, ps in data.items():
    fm = ps[list(ps)[0]]["face_map"]
    print(f"  {c:<10} pose={list(ps)} face_map={len(fm)}")

# ---------- 校验: 剧本 face 覆盖（从磁盘读, 确保与产物一致）----------
JSON_DIR = r"E:\文档\桌面\dr移植\剧本json"
data = json.load(open(OUT_DATA_TXT, encoding="utf-8"))
n_ref = n_ok = 0
miss = collections.Counter()
for p in glob.glob(os.path.join(JSON_DIR, "*.json")):
    if ".resx" in p or not p.endswith(".ks.json"):
        continue
    d = json.load(open(p, encoding="utf-8"))
    def walk(o):
        global n_ref, n_ok
        if isinstance(o, dict):
            img = o.get("imageFile")
            if isinstance(img, dict) and o.get("cname") == "character" and img.get("file"):
                f = img["file"].rsplit(".", 1)[0]
                opts = img.get("options") or {}
                face = str(opts.get("face") or "").split("@")[0]
                pose = str(opts.get("pose") or "1")
                n_ref += 1
                ch = data.get(f, {})
                pd = ch.get(pose) or ch.get("1")
                fm = pd.get("face_map", {}) if pd else {}
                if face in fm:
                    n_ok += 1
                else:
                    miss[(f, pose, face)] += 1
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(d)
print(f"\n=== 剧本校验: {n_ok}/{n_ref} = {n_ok/n_ref*100:.2f}% ===")
for k, c in miss.most_common(10):
    print(f"  缺: {k} x{c}")
