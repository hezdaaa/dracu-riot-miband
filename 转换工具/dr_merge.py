# -*- coding: utf-8 -*-
"""DR 剧本合并转换器：70 个手环脚本 → 千恋万花格式 scriptDataN.txt
- 全局连续页码，500 页/块
- 剧本顺序 = Windows 资源管理器自然排序(StrCmpLogicalW)
- 选项跳转 target label → 全局页码
- 背景 b 映射（stagename_timename → 实际背景图名）
- 立绘 c 保留 DR 引用（待合成后映射）
- 输出含千恋万花格式 + DR 扩展字段(blur/e/f)"""
import json, os, sys, glob, re, ctypes
from functools import cmp_to_key
sys.stdout.reconfigure(encoding="utf-8")

def _str_cmp(a, b):
    """Windows 资源管理器自然排序(数字按数值)"""
    try:
        fn = ctypes.windll.shlwapi.StrCmpLogicalW
        fn.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
        fn.restype = ctypes.c_int
        r = fn(a, b)
        return (r > 0) - (r < 0)
    except Exception:
        return (a > b) - (a < b)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_DIR = os.path.join(BASE, "手环脚本")
OUT_DIR = os.path.join(BASE, "剧本_合并")
BG_MAP = os.path.join(BASE, "剧本json", "_背景映射.json")
os.makedirs(OUT_DIR, exist_ok=True)
CHUNK = 500

# ---------- 剧本顺序（主线优先） ----------
MAIN_PREFIXES = ["★プロローグa", "★プロローグb", "★本編"]
CHAR_ORDER = ["梓シナリオ", "美羽－", "莉音－", "エリナ－", "ニコラ－"]

def sort_key(fn):
    base = fn.replace(".json", "")
    for i, p in enumerate(MAIN_PREFIXES):
        if base.startswith(p):
            return (0, i, base)
    for i, p in enumerate(CHAR_ORDER):
        if base.startswith(p):
            return (1, i, base)
    return (2, 0, base)

# ---------- 背景映射 ----------
bg_map = {}
if os.path.exists(BG_MAP):
    bm = json.load(open(BG_MAP, encoding="utf-8"))
    for ref, m in bm.get("mapping", {}).items():
        if m.get("exists"):
            bg_map[ref] = m["image"]
    # 特判
    bg_map["画面_白"] = "画面_白"
    bg_map["画面_黒"] = "画面_黒"
# 兜底：缺失场景替代
bg_map["ロビー_昼"] = "病院_ロビーC"
bg_map["美羽の部屋_夜"] = "寮_美羽の部屋D"

# CG/SD 去重映射(提取配置, 用于 cg 正确扩展名 + 映射到保留图)
CG_MAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cg_dedup_map.json")
cg_map = {}
if os.path.exists(CG_MAP):
    cg_map = json.load(open(CG_MAP, encoding="utf-8"))

Z_MAP = {"s": 0, "m": 1, "l": 2}

# ---------- 主流程 ----------
def main():
    files = sorted([f for f in os.listdir(SCRIPT_DIR) if f.endswith(".json") and not ".map.json" in f and not "资源清单" in f],
                   key=cmp_to_key(_str_cmp))
    print(f"剧本数: {len(files)}")

    # 1) 第一遍：分配全局页码 + 收集 (剧本, label) → 全局页码
    label_global = {}   # (file_base, label) -> 全局页码
    file_offsets = {}   # file_base -> 起始全局页码
    gid = 1
    for f in files:
        base = f.replace(".json", "")
        file_offsets[base] = gid
        d = json.load(open(os.path.join(SCRIPT_DIR, f), encoding="utf-8"))
        m = json.load(open(os.path.join(SCRIPT_DIR, base + ".map.json"), encoding="utf-8"))
        for label, rel in m.get("labels", {}).items():
            label_global[(base, label)] = gid + rel - 1
        gid += len(d)
    total = gid - 1
    print(f"总页码: {total}")

    # 2) 第二遍：重写选项跳转 + 背景映射 + 输出分块
    chunks = {}   # chunk_num -> {page: entry}
    cur_gid = 1
    prev_b, prev_c, prev_cg, prev_sd = "", "", "", ""   # 上一页(选项页继承用)
    for f in files:
        base = f.replace(".json", "")
        d = json.load(open(os.path.join(SCRIPT_DIR, f), encoding="utf-8"))
        m = json.load(open(os.path.join(SCRIPT_DIR, base + ".map.json"), encoding="utf-8"))
        labels = m.get("labels", {})
        # 反向 label 查找（本剧本）
        for page_key, entry in d.items():
            rel = int(page_key)
            g = cur_gid + rel - 1
            # 选项页: 继承上一页的背景/立绘/CG/SD(保持观感)
            if entry.get("co"):
                if not entry.get("b"): entry["b"] = prev_b
                if not entry.get("c"): entry["c"] = prev_c
                if not entry.get("cg"): entry["cg"] = prev_cg
                if not entry.get("sd"): entry["sd"] = prev_sd
            # 选项跳转解析
            if entry.get("co"):
                for i in range(1, 6):
                    tgt = entry.get(f"c{i}t", "")
                    if tgt and isinstance(tgt, str):
                        if tgt in labels:
                            entry[f"c{i}t"] = labels[tgt] + cur_gid - 1
                        elif (base, tgt) in label_global:
                            entry[f"c{i}t"] = label_global[(base, tgt)]
                        else:
                            # 跨剧本搜索 label
                            found = False
                            for (fb, lb), gv in label_global.items():
                                if lb == tgt:
                                    entry[f"c{i}t"] = gv
                                    found = True
                                    break
                            if not found:
                                print(f"  !! 未找到选项跳转目标: {tgt} in {base}")
                                entry[f"c{i}t"] = g
            # 背景映射(stagename_timename → 图片名); 已是图片名或选项页继承的保留
            if entry.get("b") and entry["b"] in bg_map:
                entry["b"] = bg_map[entry["b"]]
            # 立绘缩放 cs 保留数字
            if entry.get("cs"):
                entry["cs"] = int(entry["cs"])
            # cg: 用小写查去重映射(键为小写), 命中用保留图(正确大小写); 无映射补 .jpg(素材多为 jpg)
            if entry.get("cg"):
                cl = entry["cg"].lower()
                mapped = cg_map.get(cl) or cg_map.get(cl + ".png") or cg_map.get(cl + ".jpg")
                if mapped:
                    entry["cg"] = mapped
                elif cl.endswith((".png", ".jpg", ".jpeg")):
                    entry["cg"] = cl
                else:
                    entry["cg"] = cl + ".jpg"
            # sd: 小写 + .png + 去重映射
            if entry.get("sd"):
                s = entry["sd"].lower().split(".")[0]
                entry["sd"] = cg_map.get(s + ".png") or (s + ".png")
            # 分块
            chunk = (g - 1) // CHUNK + 1
            chunks.setdefault(chunk, {})[str(g)] = entry
            # 记录上一页条目(供选项页继承: 只复制上一页, 空字段不强求补齐)
            prev_b = entry.get("b", "")
            prev_c = entry.get("c", "")
            prev_cg = entry.get("cg", "")
            prev_sd = entry.get("sd", "")
        cur_gid += len(d)

    # 3) 写出分块
    for chunk in sorted(chunks):
        fn = os.path.join(OUT_DIR, f"scriptData{chunk}.txt")
        json.dump(chunks[chunk], open(fn, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"输出 {len(chunks)} 个分块到 {OUT_DIR}")
    # 汇总信息
    info = {"total_pages": total, "chunks": len(chunks),
            "files": [f.replace(".json","") for f in files]}
    json.dump(info, open(os.path.join(OUT_DIR, "_info.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
