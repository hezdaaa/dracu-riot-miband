# -*- coding: utf-8 -*-
"""批量把 dracu-riot 中文剧本 .ks.scn (PSB) 转换为 JSON。
依赖 FreeMote PsbDecompile.exe。"""
import os, sys, glob, subprocess, shutil

sys.stdout.reconfigure(encoding="utf-8")
PSB_DECOMPILE = r"E:\文档\桌面\文件\杂项\KRKR解包工具\FreeMoteViewer\PsbDecompile.exe"
SCN_DIR  = r"E:\文档\桌面\gal\DR_extract\dtcn\cnpatch"
OUT_DIR  = r"E:\HP\Documents\1\DRACU-RIOT\剧本json"

os.makedirs(OUT_DIR, exist_ok=True)
scns = sorted(glob.glob(os.path.join(SCN_DIR, "*.ks.scn")))
print(f"待转换剧本: {len(scns)} 个")

ok = fail = 0
for scn in scns:
    base = os.path.splitext(os.path.basename(scn))[0]  # 去掉 .scn
    out_json = os.path.join(OUT_DIR, base + ".json")
    if os.path.exists(out_json) and os.path.getsize(out_json) > 1000:
        ok += 1
        continue
    try:
        subprocess.run([PSB_DECOMPILE, scn], cwd=SCN_DIR,
                       check=True, timeout=300,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # PsbDecompile 输出到 cwd(SCN_DIR)，找刚生成的 json
        for suffix in (".json", ".resx.json"):
            src = os.path.join(SCN_DIR, base + suffix)
            if os.path.exists(src):
                shutil.move(src, os.path.join(OUT_DIR, os.path.basename(src)))
        if os.path.exists(out_json):
            ok += 1
        else:
            fail += 1
            print("!! 未生成输出:", base)
    except Exception as ex:
        fail += 1
        print(f"!! {base}: {ex}")
print(f"完成: 成功 {ok}, 失败 {fail}")
