# -*- coding: utf-8 -*-
"""补充 cg_map.json: 大小写修正 + evXXXa 遗留引用映射
确保剧本引用的每个 cg/sd 都能解析到 evig 实际文件"""
import json, glob, os, re, io, sys
sys.stdout.reconfigure(encoding="utf-8")
S = r"E:\HP\Documents\1\DRACU-RIOT\src\common"
EVIG = os.path.join(S, "evig")
cg_map = json.load(io.open(os.path.join(S, "cg_map.json"), encoding="utf-8"))
evig_files = set(os.listdir(EVIG))
evig_lower = {}
for f in evig_files:
    evig_lower.setdefault(f.lower(), []).append(f)

refs = set()
for p in glob.glob(os.path.join(S, "script", "scriptData*.txt")):
    try:
        j = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        continue
    for v in j.values():
        for k in ("cg", "sd"):
            r = (v or {}).get(k) or ""
            if r:
                refs.add(r.lower())

added = 0
unresolved = []
for ref in sorted(refs):
    if ref in cg_map or ref in evig_files:
        continue
    cand = evig_lower.get(ref)
    if cand:
        cg_map[ref] = cand[0]
        added += 1
        continue
    # evXXXa -> 该事件保留代表
    m = re.match(r"^(ev\d+)a(\.\w+)$", ref)
    if m:
        base, ext = m.group(1), m.group(2)
        aa = base + "aa" + ext
        if aa in evig_files:
            cg_map[ref] = aa
        else:
            reps = [v for v in cg_map.values() if v.startswith(base)]
            if reps:
                cg_map[ref] = reps[0]
            else:
                unresolved.append(ref)
                continue
        added += 1
    else:
        unresolved.append(ref)

json.dump(cg_map, io.open(os.path.join(S, "cg_map.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"补充 {added} 条, 总映射 {len(cg_map)} 条")
print(f"仍无法解析: {unresolved}")
