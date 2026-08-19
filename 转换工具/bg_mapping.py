# -*- coding: utf-8 -*-
"""背景映射：解析 base.stage，把剧本引用的 stagename_timename → 实际背景图名。
规则：image 含 TIME 时用时间段 prefix 替换；否则固定图。"""
import re, os, sys, json, glob
sys.stdout.reconfigure(encoding="utf-8")

BG_DIR = r"E:\文档\桌面\gal\DR_extract\bgimage"
SCRIPT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "手环脚本")

def match_block(src, start):
    """从 src 的 %[ 开始，返回 (block_content, 结束位置)"""
    i = src.find("%[", start)
    if i < 0:
        return None, -1
    depth = 0
    j = i
    while j < len(src):
        if src.startswith("%[", j):
            depth += 1
            j += 2
        elif src[j] == "]":
            depth -= 1
            if depth == 0:
                return src[i+2:j], j
            j += 1
        else:
            j += 1
    return None, -1

def parse_blocks(src, section):
    """解析顶层 hash 块（如 "times" / "stages"），返回 {name: body}"""
    pos = src.find(f'"{section}"')
    if pos < 0:
        return {}
    block, _ = match_block(src, pos)
    if block is None:
        return {}
    out = {}
    k = 0
    while k < len(block):
        m = re.search(r'"([^"]+)"\s*=>\s*%\[', block[k:])
        if not m:
            break
        name = m.group(1)
        body, end = match_block(block, k + m.start())
        if body is None:
            break
        out[name] = body
        k = end + 1
    return out

def parse_stage(fn):
    """解析 base.stage 返回 (times_prefix, stage_image)"""
    s = open(fn, encoding="shift_jis").read()
    times = {}
    for name, body in parse_blocks(s, "times").items():
        pm = re.search(r'"prefix"\s*=>\s*"([^"]+)"', body)
        if pm:
            times[name] = pm.group(1)
    stages = {}
    for name, body in parse_blocks(s, "stages").items():
        im = re.search(r'"image"\s*=>\s*"([^"]+)"', body)
        if im:
            stages[name] = im.group(1)
    return times, stages

def resolve(stage, time, times, stages):
    """stagename + timename → 实际图片名（无后缀）"""
    if time not in times:
        time = "昼"
    prefix = times[time]
    if stage not in stages:
        return None, f"无此场景: {stage}"
    img = stages[stage]
    if "TIME" in img:
        img = img.replace("TIME", prefix)
    return img, None

def main():
    times, stages = parse_stage(os.path.join(BG_DIR, "base.stage"))
    pngs = {os.path.splitext(f)[0] for f in os.listdir(BG_DIR) if f.endswith(".png")}
    print(f"时间段 prefix: {times}")
    print(f"场景数: {len(stages)}, bgimage PNG 数: {len(pngs)}")

    # 收集所有剧本引用的背景
    refs = set()
    for p in glob.glob(os.path.join(SCRIPT_DIR, "*.json")):
        if ".map.json" in p:
            continue
        d = json.load(open(p, encoding="utf-8"))
        for v in d.values():
            b = v.get("b", "")
            if b:
                refs.add(b)
    print(f"剧本背景引用种类: {len(refs)}")

    mapping = {}
    missing = []
    special = {"暗転": "画面_黒", "白画面": "画面_白"}
    for ref in sorted(refs):
        if "_" in ref:
            stage, time = ref.rsplit("_", 1)
        else:
            stage, time = ref, "昼"
        if stage in special:
            img = special[stage]
        else:
            img, err = resolve(stage, time, times, stages)
            if err:
                # 尝试去掉 stagename 的歧义（如 昼 单独出现）
                missing.append((ref, err))
                continue
        exists = img in pngs or img in ("画面_黒", "画面_白")
        mapping[ref] = {"image": img, "exists": exists}
        if not exists:
            missing.append((ref, f"图片不存在: {img}"))

    print("\n=== 映射结果 ===")
    for ref, m in sorted(mapping.items()):
        print(f"  {ref:<30} → {m['image']:<28} {'✅' if m['exists'] else '❌'}")
    print(f"\n可映射: {sum(1 for m in mapping.values() if m['exists'])} / {len(mapping)}")
    if missing:
        print("\n=== 无法映射/缺失 ===")
        for ref, err in missing:
            print(f"  {ref}: {err}")

    # 保存映射表
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "剧本json", "_背景映射.json")
    json.dump({"times": times, "stages": stages, "mapping": mapping},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n映射表已保存: {out}")

if __name__ == "__main__":
    main()
