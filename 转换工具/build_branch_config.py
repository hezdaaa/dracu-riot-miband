"""DRACU-RIOT 分支配置生成器
================================================
输入:
  剧本json/剧本/*.ks.json   原剧本结构（scenes/selects/nexts）
  手环脚本/*.json + *.map.json  已转换脚本 + label 映射
输出:
  branchConfig.js           注入 detail.ux 的 branchConfig 数据
  (直接) 剧本_合并/scriptData*.txt  flag 型选项目标修正（c1t → dummy 公共内容起点）

branchConfig 结构（参考千恋万花移植 detail.ux）:
  noNextPages: {分支末尾页: 合流页}         前进特判（分支末尾跳过兄弟分支到合流）
  noBackPages: {合流页: 合流页}             回退堵死（自环）
  hiddenPages: {路由页: fn(choice) => 目标页}  条件路由（flag 判定、路线分叉）
  choices: {}
  end: {结局页: 路线名 END}

用法:
  python build_branch_config.py [--no-patch] [--script-dir 剧本_合并]
"""
import json, os, sys, re, glob, ctypes
from functools import cmp_to_key
sys.stdout.reconfigure(encoding="utf-8")

# ---------------- 路径 ----------------
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG_DIR = os.path.join(BASE, "剧本json", "剧本")
SCRIPT_DIR = os.path.join(BASE, "手环脚本")
MERGE_DIR = os.path.join(BASE, "剧本_合并")
OUT_FILE = os.path.join(BASE, "转换工具", "branchConfig.js")

PATCH = "--no-patch" not in sys.argv

# ---------------- Windows 自然排序（与 dr_merge 一致） ----------------
def _str_cmp(a, b):
    try:
        fn = ctypes.windll.shlwapi.StrCmpLogicalW
        fn.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
        fn.restype = ctypes.c_int
        return fn(a, b)
    except Exception:
        return (a > b) - (a < b)

def natural_sorted(lst):
    return sorted(lst, key=cmp_to_key(_str_cmp))

# ---------------- 工具函数 ----------------
def scene_page_count(scene):
    """按 dr_script_converter 逻辑计算场景占据的页数。
    = chapter 行(至多1) + 非空对白 + 选项页(至多1)"""
    n = 0
    for line in scene.get("lines", []):
        if isinstance(line, list) and len(line) >= 2 and line[0] == "chapter":
            n += 1
            break
    for tb in scene.get("texts", []):
        if (isinstance(tb, list) and len(tb) >= 3 and isinstance(tb[2], str)
                and tb[2].strip()):
            n += 1
    if scene.get("selects"):
        n += 1
    return n

def clean_label(t):
    """label:N → label（KiriKiri 跳行语法，统一按 label 起点处理）"""
    if not t:
        return t
    return t.split(":", 1)[0]

def is_exit_target(storage, target):
    """是否跳回标题/结束（start.ks / *gameend_* / replay.ks）"""
    if not target:
        return False
    if storage and "start.ks" in storage:
        return True
    if target.startswith("*gameend") or target.startswith("*endrecollection"):
        return True
    return False

def eval_vals(expr):
    """提取 eval 表达式里的所有 ==N 数值（用于选项→分支匹配）"""
    if not expr:
        return []
    return [int(m) for m in re.findall(r"==\s*(\d+)", expr)]

# 模块级全局（供 write_flag_rules 等使用）
label_global = {}
orig_cache = {}

# 12 个条件路由的推导条件（按 flag 累计关系从选项记录 choice[选项页] 推导）
# 参考 flag_rules.md。格式: 路由页 -> (条件JS, 推导说明)
CONDITIONS = {
    3870: ("if(choice[3113] === 2) return 3912; return 3871;", "sel_flag由3113(part003)设置"),
    3950: ("if(choice[3113] === 2) return 3952; return 3951;", "同上"),
    5749: ("if(choice[5080] === 2) return 5764; return 5750;", "sel_flag由5080(part007)设置"),
    8234: ("const R=choice[5080]===1&&choice[5658]===2&&choice[7022]===2&&choice[7669]===2;"
           "const E=choice[5080]===2&&choice[5658]===2&&choice[6822]===2&&choice[7669]===1;"
           "const N=choice[4418]===1&&choice[5080]===2&&choice[5658]===2&&choice[7669]===2;"
           "if(R||N)return 8431;if(E)return 8325;return 8235;", "本编14アンダーカバー: rio/nic→莉音版, eri→艾莉娜版"),
    8324: ("const M=choice[3113]===1&&choice[5658]===1&&choice[6822]===1&&choice[7669]===3;"
           "if(M)return 8597;return 8717;", "miu满4→美羽版"),
    8560: ("const N=choice[4418]===1&&choice[5080]===2&&choice[5658]===2&&choice[7669]===2;"
           "if(N)return 8596;return 8561;", "nic满4→尼古拉版"),
    8846: ("const R=choice[5080]===1&&choice[5658]===2&&choice[7022]===2&&choice[7669]===2;"
           "const N=choice[4418]===1&&choice[5080]===2&&choice[5658]===2&&choice[7669]===2;"
           "if(R||N)return 8847;return 8848;", "本编15: rio或nic满4"),
    8873: ("const E=choice[5080]===2&&choice[5658]===2&&choice[6822]===2&&choice[7669]===1;"
           "if(E)return 9028;return 8874;", "eri满4→艾莉娜undercover"),
    9019: ("const m=choice[3113]===1&&choice[5658]===1&&choice[6822]===1&&choice[7669]===3;"
           "const a=choice[3113]===2&&choice[5658]===2&&choice[7022]===1&&choice[7669]===3;"
           "const r=choice[5080]===1&&choice[5658]===2&&choice[7022]===2&&choice[7669]===2;"
           "const e=choice[5080]===2&&choice[5658]===2&&choice[6822]===2&&choice[7669]===1;"
           "const n=choice[4418]===1&&choice[5080]===2&&choice[5658]===2&&choice[7669]===2;"
           "if(!(m||a||r||e||n))return 9023;return 9020;", "全flag不满4→普通结局"),
    9022: ("const m=choice[3113]===1&&choice[5658]===1&&choice[6822]===1&&choice[7669]===3;"
           "if(m)return 32071;"
           "const a=choice[3113]===2&&choice[5658]===2&&choice[7022]===1&&choice[7669]===3;"
           "if(a)return 42333;"
           "const r=choice[5080]===1&&choice[5658]===2&&choice[7022]===2&&choice[7669]===2;"
           "if(r)return 22712;"
           "const e=choice[5080]===2&&choice[5658]===2&&choice[6822]===2&&choice[7669]===1;"
           "if(e)return 9340;"
           "const n=choice[4418]===1&&choice[5080]===2&&choice[5658]===2&&choice[7669]===2;"
           "if(n)return 18437;return 9023;", "路线分叉: 美羽/梓/莉音/艾莉娜/尼古拉"),
    38287: ("if(choice[38277] === 2) return 38302; return 38288;", "sel_flag由38277(美羽其7)设置"),
    52578: ("if(choice[51941] === 1) return 52596; return 52579;", "anus_flag由51941(梓fix9)设置"),
}

def exp_val(exp):
    """解析 exp 对 sel_flag 的设置: 'f.sel_flag = 2' → 2 ; 'f.sel_flag ++' → 'inc' ; 无 → None"""
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

# ---------------- 主流程 ----------------
def main():
    global label_global, orig_cache
    # 0. 先用 dr_merge 重新生成合并数据（保留 cg/sd/文本处理），再套用分支修正
    if not PATCH:
        print("(--no-patch 模式：不写回剧本_合并)")
    else:
        print("第 0 步：调用 dr_merge 重新生成合并数据（保留 cg/sd/文本处理）...")
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        try:
            import dr_merge
            dr_merge.main()
            print("dr_merge 重新生成完成")
        except Exception as e:
            print(f"  !! dr_merge 重生成失败（将基于现有 剧本_合并 直接修正）: {e}")
    # 1. 文件顺序 + 全局偏移（与 dr_merge 完全一致）
    files = natural_sorted([f for f in os.listdir(SCRIPT_DIR)
                            if f.endswith(".json") and ".map.json" not in f])
    label_global = {}          # (file_base, label) -> 全局页码
    file_offsets = {}          # file_base -> 起始全局页码
    script_pages = {}          # file_base -> {rel_page: entry}
    orig_cache = {}            # file_base -> 原剧本 JSON
    gid = 1
    for f in files:
        base = f.replace(".json", "")
        file_offsets[base] = gid
        d = json.load(open(os.path.join(SCRIPT_DIR, f), encoding="utf-8"))
        m = json.load(open(os.path.join(SCRIPT_DIR, base + ".map.json"), encoding="utf-8"))
        script_pages[base] = d
        for lbl, rel in m.get("labels", {}).items():
            label_global[(base, lbl)] = gid + rel - 1
        gid += len(d)
    total = gid - 1
    print(f"剧本数 {len(files)}  总页码 {total}")

    # 2. 载入原剧本结构
    for f in files:
        base = f.replace(".json", "")
        op = os.path.join(ORIG_DIR, base + ".ks.json")
        if os.path.exists(op):
            orig_cache[base] = json.load(open(op, encoding="utf-8"))
        else:
            print(f"  !! 缺少原剧本: {base}.ks.json")

    def resolve_target(storage, target, cur_base):
        """label 目标 → 全局页码。返回 int 或 None。
        先按完整 label（含 :N 跳行）查找，找不到再剥离 :N。"""
        if not target:
            return None
        t_full = target
        t_stripped = clean_label(target)
        candidates = [t_full, t_stripped] if t_full != t_stripped else [t_full]
        for t in candidates:
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

    # 3. 逐剧本构建场景全局区间 + 生成配置
    no_next = {}        # 页面(字符串key) -> 目标页
    no_back = {}
    hidden = {}         # 页面(int key) -> (选项页, 各选项分支目标, 备注)
    ends = {}           # 页面 -> 文本
    h_fix = {}          # 选项页 -> {旧cNt: 新cNt}

    route_names = {"梓": "梓线", "美羽": "美羽线", "莉音": "莉音线",
                   "エリナ": "艾莉娜线", "ニコラ": "尼古拉线"}

    def route_name_for(base):
        for k, v in route_names.items():
            if base.startswith(k):
                return v
        return ""

    # 4. 逐文件处理
    for f in files:
        base = f.replace(".json", "")
        off = file_offsets[base]
        d = script_pages[base]
        orig = orig_cache.get(base)
        if not orig:
            continue
        scenes = orig.get("scenes", [])
        m = json.load(open(os.path.join(SCRIPT_DIR, base + ".map.json"), encoding="utf-8"))
        labels = m.get("labels", {})

        # 4.1 计算每个 scene 的全局区间（0 页场景跳过）
        scene_ranges = []     # [(label, start_g, end_g, scene)]
        for scene in scenes:
            lbl = scene.get("label", "")
            rel = labels.get(lbl)
            if rel is None:
                continue
            n = scene_page_count(scene)
            if n <= 0:
                continue
            start_g = off + rel - 1
            scene_ranges.append((lbl, start_g, start_g + n - 1, scene))

        def scene_range(label):
            if not label:
                return None, None
            for lbl, s, e, sc in scene_ranges:
                if lbl == label or lbl == clean_label(label):
                    return s, e
            return None, None

        # 4.2 处理每个 scene
        for lbl, start_g, end_g, scene in scene_ranges:
            last = end_g
            nxts = scene.get("nexts") or []
            sels = scene.get("selects") or []

            # ---- 选项页：修正 flag 型选项目标（指向 dummy 公共内容起点） ----
            if sels:
                opt_page = start_g
                sel_nexts = [n for n in nxts if n.get("target")]
                routing_lbl = sel_nexts[0]["target"] if sel_nexts else None
                routing_start, routing_end = (scene_range(routing_lbl)
                                              if routing_lbl else (None, None))
                routing_has_content = (routing_start is not None
                                       and routing_end is not None
                                       and routing_end >= routing_start)
                flag_options = [s for s in sels if not s.get("target")]
                if flag_options and routing_has_content:
                    # 有 flag 型选项且 dummy 有公共内容
                    branch_targets = []
                    unresolved = []
                    for s in sels:
                        blbl = _resolve_branch_target(s, scene, routing_lbl, scenes)
                        page = resolve_target(None, blbl, base)
                        branch_targets.append(page)
                        if page is None:
                            unresolved.append(blbl)
                    distinct = {t for t in branch_targets if t is not None}
                    if len(distinct) < 2 and not unresolved:
                        # 假分支：所有选项指向同一目标 → 保持现状（c1t 已指向 dummy 起点）
                        continue
                    if unresolved:
                        print(f"  !! 选项页 {opt_page} 有未解析分支目标: {unresolved} (需人工确认)")
                    # 真分支：选项指向公共内容起点, dummy 末尾加 choice 路由
                    hidden[int(routing_end)] = {
                        "opt_page": opt_page,
                        "targets": branch_targets,
                        "default": routing_end + 1,
                        "note": f"flag型选项: {len(sels)} 项, dummy={routing_lbl}",
                    }
                    if unresolved:
                        hidden[int(routing_end)]["unresolved"] = unresolved
                    # 修正选项页 c1t..cNt → 公共内容起点
                    fix = {}
                    for i, s in enumerate(sels):
                        slot = f"c{i+1}t"
                        old = (d.get(str(opt_page)) or {}).get(slot)
                        fix[slot] = {"old": old, "new": routing_start}
                    h_fix[str(opt_page)] = fix
                    # 选项路由分支目标的回退 → 回到 routing 末页（跳入点）
                    for t in branch_targets:
                        if t is not None and t != routing_end + 1 and str(t) not in no_back:
                            no_back[str(t)] = routing_end

            # ---- 跳转处理 ----
            conds = [n for n in nxts if n.get("eval")]
            defaults = [n for n in nxts if not n.get("eval")]
            default = defaults[-1] if defaults else None
            real_conds = [c for c in conds
                          if "isRecollection" not in (c.get("eval") or "")
                          and "sf.clear" not in (c.get("eval") or "")]

            if real_conds:
                # 该页若已被"选项路由"占用（来自前一个 flag 型选项场景）→ 优先选项路由，跳过
                if int(last) in hidden and hidden[int(last)].get("opt_page"):
                    continue
                # 条件路由 → hiddenPages（条件由用户根据原 eval 填写）
                targets = []
                for c in real_conds:
                    tgt = resolve_target(c.get("storage"), c.get("target"), base)
                    targets.append((c.get("eval", ""), tgt))
                    # 条件跳转目标的回退 → 回到本路由页
                    if tgt is not None and tgt != last + 1 and str(tgt) not in no_back:
                        no_back[str(tgt)] = last
                dflt = None
                if default:
                    dflt = resolve_target(default.get("storage"), default.get("target"), base)
                    if dflt is not None and dflt != last + 1 and str(dflt) not in no_back:
                        no_back[str(dflt)] = last
                hidden[int(last)] = {
                    "opt_page": None,
                    "targets": targets,
                    "default": dflt,
                    "note": f"条件跳转 scene={lbl}",
                }
            elif default:
                if is_exit_target(default.get("storage"), default.get("target")):
                    # 结局（target 指向 start.ks / *gameend_*，无需在 label 映射里）
                    rn = route_name_for(base)
                    ends[str(last)] = (rn + " END") if rn else "END"
                    continue
                tgt = resolve_target(default.get("storage"), default.get("target"), base)
                if tgt is None:
                    print(f"  !! 无法解析默认跳转: {base} {lbl} → {default.get('target')}")
                    continue
                if tgt != last + 1:
                    # 前进特判 + 回退堵死
                    no_next[str(last)] = tgt
                    no_back[str(tgt)] = tgt
            else:
                # 无 nexts：normal_end 等纯终点
                if lbl == "*normal_end":
                    ends[str(last)] = "普通结局 END"

        # 4.3 0 页 exit 场景（如 *dummyN → start.ks，不占页面的结局中转）
        for scene in scenes:
            lbl = scene.get("label", "")
            rel = labels.get(lbl)
            if rel is None:
                continue
            n = scene_page_count(scene)
            if n > 0:
                continue
            nxts = scene.get("nexts") or []
            defaults = [x for x in nxts if not x.get("eval")]
            default = defaults[-1] if defaults else None
            if default and is_exit_target(default.get("storage"), default.get("target")):
                end_page = off + rel - 2   # 前一真实场景的末页
                rn = route_name_for(base)
                ends[str(end_page)] = (rn + " END") if rn else "END"

    # 5. 应用选项目标修正（写回 剧本_合并，仅一次）
    if PATCH and h_fix:
        _apply_fix(h_fix)

    # 5.5 选项跳转目标的回退处理（noBackPages[选项目标] = 选项页）
    #     直接跳到远处分支时，回退应回选项页，而非兄弟分支内容
    _add_option_back(no_back)

    # 5.6 end 页回退阻断：结局页及其下一页不能回退（从后日谈进入时防止回到已结束剧情）
    _add_end_back(no_back, ends, total)

    # 6. 输出 branchConfig.js + flag 规则参考
    write_config(no_next, no_back, hidden, ends)
    write_flag_rules(files, script_pages, file_offsets)

    # 7. 报告
    print(f"\nnoNextPages: {len(no_next)}   noBackPages: {len(no_back)}"
          f"   hiddenPages: {len(hidden)}   end: {len(ends)}   h_fix选项页: {len(h_fix)}")
    print(f"\n===== hiddenPages 明细（条件需人工确认/填写） =====")
    for k in sorted(hidden, key=int):
        h = hidden[k]
        if h["opt_page"]:
            ts = ", ".join(f"opt{i+1}→{t}" for i, t in enumerate(h["targets"]))
            print(f"  {k}: [选项页{h['opt_page']}] {ts}  默认→{h['default']}   ({h['note']})")
        else:
            ts = ", ".join(f"{ev[:30]}→{t}" for ev, t in h["targets"])
            print(f"  {k}: [条件路由] {ts}  默认→{h['default']}   ({h['note']})")
    print(f"\n===== end 明细 =====")
    for k in sorted(ends, key=int):
        print(f"  {k}: {ends[k]}")
    print(f"\n输出: {OUT_FILE}")

def _dscene_default(dscene):
    """routing 场景的默认分支 label（最后无 eval 的 nexts target，保留 :N 完整标签）"""
    if not dscene:
        return ""
    for nxt in reversed(dscene.get("nexts", [])):
        if not nxt.get("eval"):
            return nxt["target"]
    return ""

def _resolve_branch_target(select, sel_scene, routing_lbl, scenes):
    """解析单个 flag 型选项对应的最终分支场景 label（保留 :N 完整标签）。
    优先级: 选项自身 target > routing 场景 eval 匹配(sel_flag=N) > routing 默认分支。
    '++' 自增型无法静态确定 → 返回默认分支并交由调用方标记 TODO。"""
    if select.get("target"):
        return select["target"]
    val = exp_val(select.get("exp", ""))
    dscene = None
    if routing_lbl:
        for sc in scenes:
            if sc.get("label") == routing_lbl or sc.get("label") == clean_label(routing_lbl):
                dscene = sc
                break
    if dscene:
        if isinstance(val, int):
            for nxt in dscene.get("nexts", []):
                if val in eval_vals(nxt.get("eval") or ""):
                    return nxt["target"]
            # =N 但无对应 cond → 默认分支
            dflt = _dscene_default(dscene)
            return dflt or routing_lbl
        if val == "inc":
            # ++ 自增：唯一条件分支时取该分支目标；多条件时无法静态确定 → None(TODO)
            real_conds = [n for n in dscene.get("nexts", [])
                          if n.get("eval") and "isRecollection" not in (n.get("eval") or "")]
            if len(real_conds) == 1:
                return real_conds[0]["target"]
            if real_conds:
                return None
            dflt = _dscene_default(dscene)
            return dflt or routing_lbl
        # 无 exp：保持 sel_flag 原值走默认分支
        dflt = _dscene_default(dscene)
        if dflt:
            return dflt
    return routing_lbl if routing_lbl else ""

def _apply_fix(h_fix):
    """把选项页 cNt 修正应用到 剧本_合并/scriptData*.txt"""
    merged = {}
    for fp in glob.glob(os.path.join(MERGE_DIR, "scriptData*.txt")):
        dd = json.load(open(fp, encoding="utf-8"))
        for k, v in dd.items():
            merged[int(k)] = v
    cnt = 0
    for page, fix in h_fix.items():
        p = int(page)
        if p not in merged:
            print(f"  !! 页面 {p} 不在合并输出中，跳过修正")
            continue
        entry = merged[p]
        for slot, fv in fix.items():
            if entry.get(slot) == fv["new"]:
                continue
            entry[slot] = fv["new"]
            cnt += 1
    # 写回分块
    chunks = {}
    for p, v in merged.items():
        chunk = (p - 1) // 500 + 1
        chunks.setdefault(chunk, {})[str(p)] = v
    for chunk, dd in chunks.items():
        fp = os.path.join(MERGE_DIR, f"scriptData{chunk}.txt")
        json.dump(dd, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if cnt:
        print(f"已修正 {cnt} 个选项目标（写回 {len(chunks)} 个分块）")

def _add_option_back(no_back):
    """为选项跳转目标补充回退：noBackPages[选项目标] = 选项页。
    直接跳到远处分支时，回退应回选项页，而非自然回退到兄弟分支内容。"""
    merged = {}
    for fp in glob.glob(os.path.join(MERGE_DIR, "scriptData*.txt")):
        for k, v in json.load(open(fp, encoding="utf-8")).items():
            merged[int(k)] = v
    cnt = 0
    for p, entry in merged.items():
        if not entry.get("co"):
            continue
        for i in range(1, 6):
            t = entry.get(f"c{i}t")
            if not t or not str(t).isdigit():
                continue
            t = int(t)
            if t == p + 1:
                continue           # 自然回退（目标即下一页），无需处理
            if str(t) in no_back:
                continue           # 已有（如合流自环/其他选项回退），保留
            if t not in merged:
                continue
            no_back[str(t)] = p
            cnt += 1
    if cnt:
        print(f"已补充 {cnt} 条选项回退（noBackPages[选项目标]=选项页）")

def _add_end_back(no_back, ends, total):
    """结局页回退阻断：noBackPages[结局页] = 结局页（自环）。
    并阻断结局页的下一页（noBackPages[结局页+1] = 自身），
    防止从后日谈/路线进入、结束翻页后回退到已结束的剧情。
    若下一页已有其他回退映射（如路线分叉目标），不覆盖。"""
    cnt = 0
    for k in list(ends.keys()):
        e = int(k)
        no_back[str(e)] = str(e)
        cnt += 1
        nxt = e + 1
        if nxt <= total and str(nxt) not in no_back:
            no_back[str(nxt)] = str(nxt)
            cnt += 1
    print(f"已阻断 {cnt} 个结局回退页（end 页及其下一页）")

def write_config(no_next, no_back, hidden, ends):
    """生成 branchConfig.js（可直接粘贴进 detail.ux）"""
    lines = []
    lines.append("branchConfig: {")
    lines.append("  noBackPages: {")
    for k in sorted(no_back, key=int):
        lines.append(f'    "{k}": "{no_back[k]}",')
    lines.append("  },")
    lines.append("  noNextPages: {")
    for k in sorted(no_next, key=int):
        lines.append(f'    "{k}": "{no_next[k]}",')
    lines.append("  },")
    lines.append("  hiddenPages: {")
    for k in sorted(hidden, key=int):
        h = hidden[k]
        if h["opt_page"]:
            # 选项直接映射（条件即 choice[选项页]）
            conds = []
            for i, t in enumerate(h["targets"]):
                if t is not None:
                    conds.append(f"if(choice[{h['opt_page']}] === {i+1}) return {t};")
                else:
                    conds.append(f"if(choice[{h['opt_page']}] === {i+1}) return {h['default']}; /* TODO 该选项分支目标未解析 */")
            conds.append(f"return {h['default']};")
            body = " ".join(conds)
            lines.append(f"    {k}: (choice) => {{ {body} }}, // {h['note']}")
        else:
            tgt_txt = ", ".join(f"{ev}→{t}" for ev, t in h["targets"])
            cond = CONDITIONS.get(int(k))
            if cond:
                lines.append(f"    {k}: (choice) => {{ {cond[0]} }}, // 条件已推导: {cond[1]} ({tgt_txt})")
            else:
                lines.append(f"    {k}: (choice) => {{ /* TODO 条件: {h['note']} */ return {h['default'] or '0'}; }}, // 目标: {tgt_txt}")
    lines.append("  },")
    lines.append("  choices: {},")
    lines.append("  end: {")
    for k in sorted(ends, key=int):
        lines.append(f'    "{k}": "{ends[k]}",')
    lines.append("  }")
    lines.append("}")
    open(OUT_FILE, "w", encoding="utf-8").write("\n".join(lines) + "\n")

def write_flag_rules(files, script_pages, file_offsets):
    """输出 flag 规则参考表（供填写 hiddenPages 条件时对照）"""
    OUT = os.path.join(BASE, "转换工具", "flag_rules.md")
    lines = ["# DRACU-RIOT 选项 flag 规则表（供填写 hiddenPages 条件）",
             "", "> `choice[选项页]` = 玩家在该选项页选择的序号(1-5)。",
             "> hiddenPages 条件写法参考千恋万花：`(choice) => { if(choice[3113] === 2) return 3912; return 3871; }`",
             ""]
    # 收集所有选项页的 flag 效果
    for f in files:
        base = f.replace(".json", "")
        off = file_offsets[base]
        orig = orig_cache.get(base)
        if not orig:
            continue
        mpath = os.path.join(SCRIPT_DIR, base + ".map.json")
        if not os.path.exists(mpath):
            continue
        mm = json.load(open(mpath, encoding="utf-8"))
        labels = mm.get("labels", {})
        scenes = orig.get("scenes", [])
        for scene in scenes:
            sels = scene.get("selects") or []
            if not sels:
                continue
            rel = labels.get(scene.get("label", ""))
            if rel is None:
                continue
            gp = off + rel - 1
            lines.append(f"### 选项页 {gp}  ({base[:40]})")
            for i, s in enumerate(sels, 1):
                exp = s.get("exp", "") or ""
                ev = s.get("eval", "") or ""
                tg = s.get("target", "") or ""
                lines.append(f"- **{i}. {s.get('text','')[:22]}**: exp=`{exp}`  eval=`{ev}`  target=`{tg}`")
            lines.append("")
    open(OUT, "w", encoding="utf-8").write("\n".join(lines))
    print(f"flag 规则表: {OUT}")

if __name__ == "__main__":
    main()
