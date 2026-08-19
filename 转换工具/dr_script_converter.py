# -*- coding: utf-8 -*-
"""DRACU-RIOT 剧本转换器：FreeMote 剧本 JSON → 小米手环脚本格式。
输出: {"1": {"s","t","b","c","cg","z","blur","e","f","co","c1","c1t",...}}
参考: 千恋万花移植《原作数据转换.py》、教程《提取工具.py》"""
import json, os, sys, glob, re
sys.stdout.reconfigure(encoding="utf-8")

# ---------------- 工具函数 ----------------
def clean_text(t):
    """清理文本并解析字号标记，返回 (文本, 字号缩放百分比 or None)。
    删除 [注音]标记、%0；开头 %NN 字号缩放(最低75%)存为 fs。"""
    if not t:
        return "", None
    t = t.replace("　", " ")
    t = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", t)
    t = re.sub(r"\[[^\]]*\]", "", t)   # 删 [xxx]
    t = re.sub(r"%0", "", t)           # 删 %0
    fs = None
    m = re.match(r"^%(\d+)\s*", t)     # 开头 %NN 字号缩放
    if m:
        fs = max(75, min(100, int(m.group(1))))
        t = t[m.end():]
    return t.strip(), fs


def extract_from_objects(objs):
    """从 objectList 提取 背景/立绘/CG/SD/立绘缩放"""
    bg, chars, cg, sd, blur, char_zoom = "", [], "", "", False, 100
    for obj in objs:
        if not isinstance(obj, dict):
            continue
        cname = obj.get("cname", "")
        img = obj.get("imageFile", {})
        if not isinstance(img, dict):
            continue
        file = img.get("file", "") or ""
        opts = img.get("options", {}) or {}
        s = json.dumps(obj, ensure_ascii=False)
        if "doBoxBlur" in s:
            blur = True
        if cname in ("stage", "stage2", "stage3") and file:
            if isinstance(opts, dict) and opts:
                st = opts.get("stagename") or ""
                tm = opts.get("timename") or ""
                bg = f"{st}_{tm}".strip("_") if (st or tm) else file
            else:
                bg = file
        elif cname == "character" and file:
            q = []
            for k in ("dress", "pose", "face", "add"):
                v = opts.get(k)
                if v:
                    q.append(f"{k}={v}")
            pos = obj.get("posName") or ""
            key = file.rsplit(".", 1)[0]  # 去掉 .stand
            if q:
                key += "?" + "&".join(q)
            if pos:
                key += f"@{pos}"
            chars.append(key)
            # 立绘缩放：posName 百分比 或 actionList zoomx
            zoom = 100
            if pos.rstrip('%').isdigit():
                zoom = int(pos.rstrip('%'))
            for item in obj.get("actionList", []) if isinstance(obj.get("actionList"), list) else []:
                if isinstance(item, list) and len(item) >= 3 and item[1] == "zoomx":
                    if isinstance(item[2], (int, float)) and 0 < item[2] <= 300:
                        zoom = int(item[2])
                        break
            if zoom != 100:
                char_zoom = zoom
        elif cname in ("event", "event2") and file:
            cg = file
        elif cname == "centerlayer" and file:
            # centerlayer：SD 小人（file 以 SD 开头）或 CG 事件图
            if file.upper().startswith("SD"):
                sd = file
            else:
                cg = file
        elif cname == "sdlayer" and file:
            sd = file
    return bg, ";".join(chars), cg, sd, blur, char_zoom

def entry_to_dict(tb):
    """text_block → 手环条目"""
    if not isinstance(tb, list) or len(tb) < 3:
        return None
    text, fs = clean_text(tb[2]) if isinstance(tb[2], str) else ("", None)
    if not text:
        return None
    speaker = tb[0] if isinstance(tb[0], str) else ""
    objs = tb[5].get("objectList", []) if len(tb) > 5 and isinstance(tb[5], dict) else []
    bg, chars, cg, sd, blur, char_zoom = extract_from_objects(objs)
    # 特效检测
    effect = flash = False
    obj_str = json.dumps(objs, ensure_ascii=False)
    if "vibration" in obj_str or "SinAction" in obj_str:
        effect = True
    if "画面_白" in obj_str or cg == "画面_白":
        flash = True
    entry = {
        "s": speaker,
        "t": text,
        "b": bg,
        "c": chars,
        "cg": cg,
        "sd": sd,
        "cs": char_zoom,      # 立绘缩放百分比（新字段，替换原 z）
        "blur": blur,          # 背景模糊 → 播放器做背景缩放
        "e": effect,
        "f": flash,
        "fs": fs,
    }
    # 只保留有意义的字段
    return {k: v for k, v in entry.items() if v not in ("", False, None)}

# ---------------- 选项跳转解析 ----------------
def resolve_select_target(select, sel_scene, scenes_map):
    """解析选项的真实跳转 target label。
    结构1: selects 自带 target
    结构2: selects 用 exp 设 flag，dummy 场景 nexts 用 eval 条件跳转"""
    if not isinstance(select, dict):
        return ""
    if select.get("target"):
        return select["target"]
    # 解析 flag 值
    val = None
    exp = select.get("exp", "")
    m = re.search(r"=\s*(\d+)", exp)
    if m:
        val = m.group(1)
    elif "++" in exp or "+=" in exp:
        val = "1"  # 自增：从 0 变为 1（简化）
    # 找 sel_scene 的 nexts 第一个目标（dummy 点）
    dummy = ""
    for nxt in sel_scene.get("nexts", []):
        if nxt.get("target"):
            dummy = nxt["target"]
            break
    if dummy and val is not None:
        dscene = scenes_map.get(dummy)
        if dscene:
            for nxt in dscene.get("nexts", []):
                if val in (nxt.get("eval") or ""):
                    return nxt["target"]
            if dscene.get("nexts"):
                return dscene["nexts"][-1]["target"]  # 默认分支
    # 无 flag 可解析 → 指向 dummy 合并点
    return dummy

# ---------------- 主转换 ----------------
def convert_script(json_path):
    with open(json_path, encoding="utf-8") as f:
        d = json.load(f)
    scenes_map = {s.get("label"): s for s in d.get("scenes", [])}
    entries = []
    label_to_id = {}
    scene_meta = {}
    current_id = 1
    for scene in d.get("scenes", []):
        label = scene.get("label", "")
        scene_start = current_id
        # chapter 行
        for line in scene.get("lines", []):
            if isinstance(line, list) and len(line) >= 2 and line[0] == "chapter":
                entries.append({"is_chapter": True, "t": str(line[1])})
                if label and label not in label_to_id:
                    label_to_id[label] = current_id
                current_id += 1
                break
        # 对话
        for tb in scene.get("texts", []):
            d2 = entry_to_dict(tb)
            if d2:
                entries.append(d2)
                if label and label not in label_to_id:
                    label_to_id[label] = current_id
                current_id += 1
        # 选项
        selects = scene.get("selects", [])
        if selects:
            opt = {"co": True, "c1": "", "c1t": "", "c2": "", "c2t": "",
                   "c3": "", "c3t": "", "c4": "", "c4t": "", "c5": "", "c5t": ""}
            for idx, sel in enumerate(selects[:5]):
                text = sel.get("text", "") if isinstance(sel, dict) else ""
                target = resolve_select_target(sel, scene, scenes_map)
                if idx == 0:
                    opt["c1"], opt["c1t"] = text, target
                elif idx == 1:
                    opt["c2"], opt["c2t"] = text, target
                elif idx == 2:
                    opt["c3"], opt["c3t"] = text, target
                elif idx == 3:
                    opt["c4"], opt["c4t"] = text, target
                elif idx == 4:
                    opt["c5"], opt["c5t"] = text, target
            entries.append(opt)
            if label and label not in label_to_id:
                label_to_id[label] = current_id
            current_id += 1
        if label and label not in label_to_id:
            label_to_id[label] = current_id
        # scene 元数据（跳转）
        scene_end = current_id - 1
        if scene_end >= scene_start:
            nexts = []
            for nxt in scene.get("nexts", []):
                if isinstance(nxt, dict) and nxt.get("target"):
                    nexts.append({"target": nxt["target"], "storage": nxt.get("storage", "")})
            scene_meta[label] = {"start": scene_start, "end": scene_end, "nexts": nexts}
    # 组装为 {页码: 条目}
    out = {}
    for i, e in enumerate(entries, 1):
        out[str(i)] = e
    return out, label_to_id, scene_meta

if __name__ == "__main__":
    JSON_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "剧本json")
    OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "手环脚本")
    os.makedirs(OUT_DIR, exist_ok=True)
    total_pages = 0
    for p in sorted(glob.glob(os.path.join(JSON_DIR, "*.json"))):
        if ".resx" in p or not p.endswith(".ks.json"):
            continue
        base = os.path.basename(p).replace(".ks.json", "")
        out, label_to_id, scene_meta = convert_script(p)
        # 保存脚本 + 跳转映射
        json.dump(out, open(os.path.join(OUT_DIR, f"{base}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        json.dump({"labels": label_to_id, "scenes": scene_meta},
                  open(os.path.join(OUT_DIR, f"{base}.map.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        total_pages += len(out)
        print(f"{base:<45} {len(out):>6} 页, {len(label_to_id):>4} labels, {len(scene_meta)} scenes")
    print(f"\n共 {len([p for p in glob.glob(os.path.join(JSON_DIR,'*.json')) if '.resx' not in p])} 个剧本, 总计 {total_pages} 页")
