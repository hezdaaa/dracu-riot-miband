# -*- coding: utf-8 -*-
"""CG/SD 去重应用：按 cg_cluster 结果备份并删除 evig 冗余图,生成运行时映射 cg_map.json
- 只保留动作差分(每个构图簇一张代表),表情差分(同簇其余)删除
- 被删图若被剧本引用,由播放器通过 cg_map.json 映射到保留代表
用法: python dedup_cg.py [--dry]"""
import os, sys, json, shutil
sys.stdout.reconfigure(encoding="utf-8")

EVIG = r"E:\HP\Documents\1\DRACU-RIOT\src\common\evig"
SRC = r"E:\HP\Documents\1\DRACU-RIOT\src\common"
BACKUP = r"E:\文档\桌面\dr移植\src外\cg_dedup_backup"
RESULT = r"C:\Users\HP\AppData\Roaming\CherryStudio\Data\Agents\t-default\cg_cluster_result.json"
DRY = "--dry" in sys.argv

r = json.load(open(RESULT, encoding="utf-8"))
cg_map = r["cg_map"]   # removed -> kept

# 校验 keep 图都存在
missing_keep = [k for k in set(cg_map.values()) if not os.path.exists(os.path.join(EVIG, k))]
print(f"映射 {len(cg_map)} 条 | 保留图缺失: {len(missing_keep)} {missing_keep[:5]}")

# 校验被删图都存在
deletable = [f for f in cg_map if os.path.exists(os.path.join(EVIG, f))]
print(f"待删除(存在): {len(deletable)} 张, 已不存在跳过: {len(cg_map)-len(deletable)} 张")

if DRY:
    print("[dry-run] 不实际删除")
    sys.exit(0)

os.makedirs(BACKUP, exist_ok=True)
deleted = 0
for f in deletable:
    shutil.copy2(os.path.join(EVIG, f), os.path.join(BACKUP, f))
    os.remove(os.path.join(EVIG, f))
    deleted += 1

json.dump(cg_map, open(os.path.join(SRC, "cg_map.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"已删除 {deleted} 张, 备份到 {BACKUP}")
print(f"已生成 {os.path.join(SRC, 'cg_map.json')} ({len(cg_map)} 条映射)")
print(f"evig 剩余文件: {len(os.listdir(EVIG))}")
