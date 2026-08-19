"""全量跳转数据提取 + 分类 + 校验
================================================
遍历 70 个原剧本 JSON，把每个场景的跳转（nexts/selects）解析为全局页码，
按类型分类输出 markdown，并交叉校验已生成的 branchConfig.js。

输出: 跳转分类表.md
"""
import json, os, sys, glob, re, ctypes
from functools import cmp_to_key
sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG_DIR = os.path.join(BASE, "剧本json", "剧本")
SCRIPT_DIR = os.path.join(BASE, "手环脚本")
OUT = os.path.join(BASE, "转换工具", "跳转分类表.md")

def _str_cmp(a, b):
    try:
        fn = ctypes.windll.shlwapi.StrCmpLogicalW
        fn.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
        fn.restype = ctypes.c_int
        return fn(a, b)
    except Exception:
        return (a > b) - (a < b)

def scene_page_count(scene):
    n = 0
    for line in scene.get("lines", []):
        if isinstance(line, list) and len(line) >= 2 and line[0] == "chapter":
            n += 1; break
    for tb in scene.get("texts", []):
        if isinstance(tb, list) and len(tb) >= 3 and isinstance(tb[2], str) and tb[2].strip():
            n += 1
    if scene.get("selects"):
        n += 1
    return n

def clean_label(t):
    return t.split(":", 1)[0] if t else t

def is_exit_target(storage, target):
    if not target:
        return False
    if storage and "start.ks" in storage:
        return True
    if target.startswith("*gameend") or target.startswith("*endrecollection"):
        return True
    return False

def eval_vals(expr):
    if not expr:
        return []
    return [int(m) for m in re.findall(r"==\s*(\d+)", expr)]

def exp_val(exp):
    if not exp:
        return None
    m = re.search(r"sel_flag\s*=\s*(\d+)", exp)
    if m:
        return int(m.group(1))
    if re.search(r"sel_flag\s*(\+\+|(\+=)\s*\d*)", exp):
        return "inc"
    m = re.search(r"=\s*(\d+)", exp)
    if m:
        return int(m.group(1))
    return None

def main():
    files = sorted([f for f in os.listdir(SCRIPT_DIR) if f.endswith(".json") and ".map.json" not in f],
                   key=cmp_to_key(_str_cmp))
    # 全局映射
    label_global = {}
    file_offsets = {}
    gid = 1
    for f in files:
        base = f.replace(".json", "")
        file_offsets[base] = gid
        m = json.load(open(os.path.join(SCRIPT_DIR, base + ".map.json"), encoding="utf-8"))
        for lbl, rel in m.get("labels", {}).items():
            label_global[(base, lbl)] = gid + rel - 1
        d = json.load(open(os.path.join(SCRIPT_DIR, f), encoding="utf-8"))
        gid += len(d)
    total = gid - 1

    def resolve(storage, target, cur_base):
        if not target:
            return None
        t_full = target
        t_stripped = clean_label(target)
        for t in [t_full, t_stripped] if t_full != t_stripped else [t_full]:
            if storage:
                sb = storage.replace(".ks", "")
                if (sb, t) in label_global:
                    return label_global[(sb, t)]
            if (cur_base, t) in label_global:
                return label_global[(cur_base, t)]
            for (fb, lb), gv in label_global.items():
                if lb == t:
                    return gv
        return None

    L = []
    W = []   # 警告
    def add(s=""):
        L.append(s)

    add("# DRACU-RIOT 全量跳转分类表")
    add(f"\n> 生成自 70 个原剧本 JSON + 手环脚本 map。总页码 {total}。")
    add(f"> 各条跳转标注: 源页(源场景) → 目标页(目标场景/标签)，以及跳转性质。\n")

    route_names = {"梓": "梓", "美羽": "美羽", "莉音": "莉音", "エリナ": "艾莉娜", "ニコラ": "尼可拉"}
    def route_name_for(base):
        for k, v in route_names.items():
            if base.startswith(k):
                return v
        return ""

    # 分类统计
    stats = {"选项页": 0, "条件路由": 0, "选项路由": 0, "静态跳转": 0, "回退堵死": 0, "结局": 0}
    sections = {}   # 大类 -> list
    def sec(name, line):
        sections.setdefault(name, []).append(line)

    # 逐文件
    for f in files:
        base = f.replace(".json", "")
        off = file_offsets[base]
        orig = json.load(open(os.path.join(ORIG_DIR, base + ".ks.json"), encoding="utf-8"))
        m = json.load(open(os.path.join(SCRIPT_DIR, base + ".map.json"), encoding="utf-8"))
        labels = m.get("labels", {})
        scenes = orig.get("scenes", [])
        # 场景区间
        ranges = []
        for sc in scenes:
            rel = labels.get(sc.get("label", ""))
            if rel is None:
                continue
            n = scene_page_count(sc)
            if n <= 0:
                continue
            ranges.append((sc["label"], off + rel - 1, off + rel - 1 + n - 1, sc))
        def srange(lbl):
            for a, s, e, sc in ranges:
                if a == lbl or a == clean_label(lbl):
                    return s, e, a
            return None, None, None

        # 故事大类
        if base.startswith(("★プロローグ", "★本編")):
            section = "共通线"
        elif base.startswith("梓"):
            section = "梓线"
        elif base.startswith("美羽"):
            section = "美羽线"
        elif base.startswith("莉音"):
            section = "莉音线"
        elif base.startswith("エリナ"):
            section = "艾莉娜线"
        elif base.startswith("ニコラ"):
            section = "尼可拉线"
        else:
            section = "其他"
        if section not in sections:
            sections[section] = []

        add(f"\n## {base}")
        # 场景列表（带页码）
        add(f"\n| 场景 | 页码区间 | 说明 |")
        add(f"|---|---|---|")
        for a, s, e, sc in ranges:
            sel = " [选项]" if sc.get("selects") else ""
            add(f"| `{a}` | {s}-{e} |{sel} texts={len(sc.get('texts',[]))}|")

        # 逐场景分类跳转
        for a, s, e, sc in ranges:
            nxts = sc.get("nexts") or []
            sels = sc.get("selects") or []
            last = e

            # --- 选项页 ---
            if sels:
                stats["选项页"] += 1
                add(f"\n### 选项页 {s}（场景 {a}）")
                opts_txt = []
                for i, sel in enumerate(sels, 1):
                    exp = sel.get("exp", "") or ""
                    ev = sel.get("eval", "") or ""
                    tg = sel.get("target", "") or ""
                    tgt_page = resolve(None, tg, base)
                    tgt_scene = srange(tg)[2] if tg else ""
                    mode = "直接" if tg else ("flag" if exp else "无目标")
                    add(f"- **{i}. {sel.get('text','')}**  [{mode}] 目标={tg} →页{tgt_page}({tgt_scene})  exp=`{exp}`  eval=`{ev}`")
                    opts_txt.append(f"{i}:{sel.get('text','')[:10]}")
                sections[section].append(f"选项页 {s}: " + " / ".join(opts_txt))

            # --- 条件路由（有 eval 的 nexts）---
            conds = [n for n in nxts if n.get("eval")]
            defaults = [n for n in nxts if not n.get("eval")]
            default = defaults[-1] if defaults else None
            real_conds = [c for c in conds if "isRecollection" not in (c.get("eval") or "")
                          and "sf.clear" not in (c.get("eval") or "")]
            recol_conds = [c for c in conds if "isRecollection" in (c.get("eval") or "")]

            if real_conds:
                stats["条件路由"] += 1
                add(f"\n### 条件路由页 {last}（场景 {a}，末页）")
                cond_txt = []
                for c in real_conds:
                    tp = resolve(c.get("storage"), c.get("target"), base)
                    ts = srange(c.get("target"))[2] if c.get("target") else ""
                    add(f"- 若 `{c.get('eval')}` → 页{tp}(`{c.get('target')}` {ts})")
                    cond_txt.append(f"`{c.get('eval')}`→页{tp}")
                if default:
                    tp = resolve(default.get("storage"), default.get("target"), base)
                    ts = srange(default.get("target"))[2] if default.get("target") else ""
                    add(f"- 否则(默认) → 页{tp}(`{default.get('target')}` {ts})")
                    cond_txt.append(f"默认→页{tp}")
                else:
                    add(f"- 否则(默认) → 无默认分支!")
                sections[section].append(f"路由页 {last} ({a}): " + " ".join(cond_txt))
            if recol_conds:
                add(f"- [忽略] 回想条件 {[c.get('eval') for c in recol_conds]}")

            # --- 静态跳转 / 结局 ---
            if not real_conds and default:
                if is_exit_target(default.get("storage"), default.get("target")):
                    rn = route_name_for(base)
                    stats["结局"] += 1
                    add(f"\n### 结局页 {last}（场景 {a}，末页）→ 回标题" + (f"  [{rn}后日谈]" if rn else ""))
                    sections[section].append(f"结局页 {last} ({a})")
                else:
                    tp = resolve(default.get("storage"), default.get("target"), base)
                    physical = last + 1
                    if tp is None:
                        add(f"\n### [无法解析] 场景 {a} 默认跳转 → {default.get('target')}")
                    elif tp != physical:
                        stats["静态跳转"] += 1
                        ts = srange(default.get("target"))[2] if default.get("target") else ""
                        note = "跨文件" if default.get("storage") and default.get("storage").replace(".ks","") != base else ""
                        add(f"\n### 静态跳转页 {last}（场景 {a}）→ 页{tp}(`{default.get('target')}` {ts}) {note}  [物理下一页={physical}]")
                        sections[section].append(f"静态跳转页 {last} ({a})→页{tp}")
                    # 若 tp == physical：自然线性，不记录
            elif not real_conds and not nxts:
                if a == "*normal_end":
                    stats["结局"] += 1
                    add(f"\n### 结局页 {last}（场景 {a}）→ 普通结局")
                    sections[section].append(f"结局页 {last} ({a})")

        # 0 页 exit 场景（不占页面的结局中转）
        for sc in scenes:
            lbl = sc.get("label", "")
            rel = labels.get(lbl)
            if rel is None:
                continue
            if scene_page_count(sc) > 0:
                continue
            nxts = sc.get("nexts") or []
            defaults = [n for n in nxts if not n.get("eval")]
            default = defaults[-1] if defaults else None
            if default and is_exit_target(default.get("storage"), default.get("target")):
                ep = off + rel - 2
                stats["结局"] += 1
                add(f"\n### 结局页 {ep}（{lbl} 0页exit场景 → 回标题）")
                sections[section].append(f"结局页 {ep} ({lbl} 0页exit)")

    # 汇总
    summary = ["# DRACU-RIOT 跳转分类·汇总",
               "",
               f"总页数 {total}。跳转类型与数量：",
               "| 类型 | 数量 | 含义 |",
               "|---|---|---|",
               f"| 选项页 | {stats['选项页']} | 玩家选择，跳转到选项目标 |",
               f"| 条件路由 | {stats['条件路由']} | 场景末页按 flag 条件跳转（hiddenPages） |",
               f"| 静态跳转 | {stats['静态跳转']} | 分支末页/跨文件跳到固定目标（noNextPages） |",
               f"| 结局 | {stats['结局']} | 路线/后日谈终点（end） |",
               ""]
    for sec_name, items in sections.items():
        summary.append(f"## {sec_name}（{len(items)} 条跳转）")
        summary.append("")
        summary.append("```")
        summary.extend(items)
        summary.append("```")
        summary.append("")

    # 输出：汇总 + 明细
    open(OUT, "w", encoding="utf-8").write("\n".join(summary) + "\n" + "\n".join(L) + "\n")
    print(f"统计: {stats}")
    print(f"输出: {OUT}")
    print(f"警告数: {len(W)}")

if __name__ == "__main__":
    main()
