"""交叉校验生成的 branchConfig.js 与源数据是否一致
逐条核对 noNextPages / noBackPages / hiddenPages / end / 选项目标。
"""
import json, os, sys, re, glob, ctypes
from functools import cmp_to_key
sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG_DIR = os.path.join(BASE, "剧本json", "剧本")
SCRIPT_DIR = os.path.join(BASE, "手环脚本")
MERGE_DIR = os.path.join(BASE, "剧本_合并")
BC_FILE = os.path.join(BASE, "转换工具", "branchConfig.js")

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

def parse_branch_config(src):
    """解析 branchConfig.js 里的 noBackPages/noNextPages/end/hiddenPages"""
    def block(name):
        # 从 name: { 开始，匹配到缩进 2 的闭括号（最后一个块闭括号后无逗号）
        m = re.search(r'(?:^|\n)  ' + name + r'\s*:\s*\{(.*?)\n  \}', src, re.S)
        return m.group(1) if m else ""
    nb = {}
    nn = {}
    end = {}
    for k, v in re.findall(r'"(\d+)"\s*:\s*"(\d+)"', block('noBackPages')):
        nb[int(k)] = int(v)
    for k, v in re.findall(r'"(\d+)"\s*:\s*"(\d+)"', block('noNextPages')):
        nn[int(k)] = int(v)
    for k, v in re.findall(r'"(\d+)"\s*:\s*"([^"]+)"', block('end')):
        end[int(k)] = v
    hidden = {}
    for m in re.finditer(r'^\s+(\d+):\s*\(choice\)\s*=>\s*\{([^}]+)\}', src, re.M):
        pg = int(m.group(1))
        body = m.group(2)
        rets = [int(x) for x in re.findall(r'return\s+(\d+);', body)]
        opt_pages = [int(x) for x in re.findall(r'choice\[(\d+)\]', body)]
        has_todo = 'TODO' in body or '需人工' in body
        hidden[pg] = {"rets": rets, "opt": opt_pages[0] if opt_pages else None,
                      "todo": has_todo}
    return nb, nn, end, hidden

def main():
    src = open(BC_FILE, encoding="utf-8").read()
    noBack, noNext, ends, hidden = parse_branch_config(src)

    # 载入合并数据
    merged = {}
    for fp in glob.glob(os.path.join(MERGE_DIR, "scriptData*.txt")):
        for k, v in json.load(open(fp, encoding="utf-8")).items():
            merged[int(k)] = v

    # 全局 label 映射
    files = sorted([f for f in os.listdir(SCRIPT_DIR) if f.endswith(".json") and ".map.json" not in f],
                   key=cmp_to_key(_str_cmp))
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
        for t in [target, clean_label(target)]:
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

    # 建立 场景末页 → (scene, file, nexts) 索引
    last_page_map = {}
    for f in files:
        base = f.replace(".json", "")
        off = file_offsets[base]
        orig = json.load(open(os.path.join(ORIG_DIR, base + ".ks.json"), encoding="utf-8"))
        m = json.load(open(os.path.join(SCRIPT_DIR, base + ".map.json"), encoding="utf-8"))
        labels = m.get("labels", {})
        for sc in orig.get("scenes", []):
            rel = labels.get(sc.get("label", ""))
            if rel is None:
                continue
            n = scene_page_count(sc)
            if n <= 0:
                continue
            lp = off + rel - 1 + n - 1
            last_page_map[lp] = (base, sc.get("label", ""), sc)

    problems = []

    # 1) 校验 noNextPages
    print(f"== noNextPages {len(noNext)} 条 ==")
    for pg, tgt in sorted(noNext.items()):
        if tgt not in merged:
            problems.append(f"noNext[{pg}] → {tgt} 目标页不存在")
        if pg not in merged:
            problems.append(f"noNext[{pg}] 源页不存在")
            continue
        if pg in last_page_map:
            base, lbl, sc = last_page_map[pg]
            nxts = sc.get("nexts") or []
            defaults = [n for n in nxts if not n.get("eval")]
            default = defaults[-1] if defaults else None
            if default:
                exp_tgt = resolve(default.get("storage"), default.get("target"), base)
                if exp_tgt != tgt:
                    problems.append(f"noNext[{pg}] ({base} {lbl}) 目标={tgt} 但源场景默认nexts={default.get('target')}→{exp_tgt}")
        else:
            problems.append(f"noNext[{pg}] 源页不是任何场景的末页")

    # 2) 校验 noBackPages（语义混合: 合流自环 / 选项目标→选项页 / 分支目标→路由末页）
    print(f"== noBackPages {len(noBack)} 条 ==")
    self_loops = 0
    for pg, tgt in sorted(noBack.items()):
        if pg not in merged:
            problems.append(f"noBack[{pg}] 源页不存在")
        if tgt not in merged:
            problems.append(f"noBack[{pg}] → {tgt} 目标页不存在")
        if pg == tgt:
            self_loops += 1

    # 3) 校验 end
    print(f"== end {len(ends)} 条 ==")
    for pg in sorted(ends):
        if int(pg) not in merged:
            problems.append(f"end[{pg}] 页面不存在")

    # 4) 校验 hiddenPages
    print(f"== hiddenPages {len(hidden)} 条 ==")
    for pg, h in sorted(hidden.items()):
        if pg not in merged:
            problems.append(f"hidden[{pg}] 路由页不存在")
        for t in h["rets"]:
            if t not in merged:
                problems.append(f"hidden[{pg}] 目标 {t} 不存在")
        if h["opt"] is not None:
            # 选项路由：验证选项页存在且是选项页
            if h["opt"] not in merged or not merged[h["opt"]].get("co"):
                problems.append(f"hidden[{pg}] 引用选项页 {h['opt']} 不是有效选项页")

    # 5) 校验选项页 cNt 指向
    print("== 选项页 cNt ==")
    opt_bad = 0
    for pg, v in merged.items():
        if v.get("co"):
            for i in range(1, 6):
                t = v.get(f"c{i}t")
                if t and int(t) not in merged:
                    problems.append(f"选项页{pg} c{i}t → {t} 不存在")
                    opt_bad += 1
    print(f"   选项页 cNt 无效: {opt_bad}")

    # 6) 检查 noNextPages 目标是否为选项页（跳转到选项页可能有问题）
    for pg, tgt in sorted(noNext.items()):
        if merged.get(tgt) and merged[tgt].get("co"):
            problems.append(f"noNext[{pg}] → {tgt} 目标是选项页(可能需要玩家选择)")

    # 7) 检查 noBackPages 的目标是否符合跳转语义
    for pg, tgt in sorted(noBack.items()):
        if pg == tgt:
            continue
        # 目标应为选项页 / 路由场景末页 / 选项路由跳入点
        t_entry = merged.get(tgt)
        if t_entry and t_entry.get("co"):
            continue  # 回选项页，OK
        # 否则目标应为某场景的末页（回跳入点）
        if tgt not in last_page_map:
            problems.append(f"noBack[{pg}] → {tgt} 目标既非选项页也非场景末页")

    print(f"\n===== 问题总数: {len(problems)} =====")
    for p in problems:
        print("  !!", p)

if __name__ == "__main__":
    main()
