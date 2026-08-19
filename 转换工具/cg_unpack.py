# -*- coding: utf-8 -*-
"""批量拆解 evimage 所有 pimg 差分包（PsbDecompile，完整路径调用）
PsbDecompile 输出到输入文件同目录(evimage/)，拆完后移动到 拆解/"""
import os, sys, subprocess, glob, shutil

sys.stdout.reconfigure(encoding="utf-8")
EV_DIR = r"E:\文档\桌面\gal\DR_extract\evimage"
OUT_DIR = os.path.join(EV_DIR, "拆解")
PSB = r"E:\文档\桌面\文件\杂项\KRKR解包工具\FreeMoteViewer\PsbDecompile.exe"
os.makedirs(OUT_DIR, exist_ok=True)

pimgs = sorted(glob.glob(os.path.join(EV_DIR, "*.pimg")))
print(f"待拆解: {len(pimgs)} 个 pimg")
ok = fail = 0
for p in pimgs:
    name = os.path.splitext(os.path.basename(p))[0]
    sub = os.path.join(OUT_DIR, name)
    if os.path.exists(sub) and os.listdir(sub):
        ok += 1
        continue
    try:
        subprocess.run([PSB, p], cwd=EV_DIR, check=True,
                       timeout=300, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # 移动输出到拆解/
        for item in (name, name + ".json", name + ".resx.json"):
            src = os.path.join(EV_DIR, item)
            if os.path.exists(src):
                shutil.move(src, os.path.join(OUT_DIR, item))
        ok += 1
    except Exception as ex:
        fail += 1
        print(f"!! {name}: {ex}")
print(f"拆解完成: 成功 {ok}, 失败 {fail}")
