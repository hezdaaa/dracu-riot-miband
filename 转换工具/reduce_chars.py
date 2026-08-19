"""多立绘缩减：按说话人只保留一个立绘
================================================
手环屏幕小，一个页面同时出现多个立绘时只显示说话人对应的那个。
逻辑:
  1. 说话人(s) 匹配到场立绘(c)中的角色 → 保留该立绘
  2. 无匹配（旁白/佑斗/群口） → 延续上一页保留的立绘（若仍在场）
  3. 都不行 → 保留第一个立绘

输入: 剧本_合并/scriptData*.txt
输出: 写回（仅改 c 字段）
"""
import json, os, sys, glob, re
sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERGE_DIR = os.path.join(BASE, "剧本_合并")

# 说话人(中文/日文) -> 立绘角色名(日文，与 c 字段一致)
SPEAKER_TO_CHAR = {
    "梓": "梓", "美羽": "美羽", "莉音": "莉音",
    "艾莉娜": "エリナ", "尼古拉": "ニコラ", "尼可拉": "ニコラ", "ニコラ": "ニコラ",
    "直太": "直太", "小夜": "小夜", "楓": "楓", "萌香": "萌香",
    "元树": "元樹", "元樹": "元樹", "兵马": "兵馬", "兵馬": "兵馬",
    "安娜": "アンナ", "アンナ": "アンナ",
    "索菲亚": "ソフィーヤ", "ソフィーヤ": "ソフィーヤ",
    "おじい様": "おじい様", "ひよ里": "ひよ里",
}

def speaker_parts(s):
    """拆分说话人 → 候选角色名列表（去括号注释、按复合分隔符拆分）"""
    if not s:
        return []
    s = s.strip("【】")
    s = re.sub(r"[（(].*?[）)]", "", s)   # 去掉 （梓）/（ゲッペルさん） 等注释
    parts = re.split(r"[・&、,，/／]", s)
    return [p.strip() for p in parts if p.strip()]

def char_name_of(c):
    return c.split("?")[0]

def main():
    merged = {}
    for fp in sorted(glob.glob(os.path.join(MERGE_DIR, "scriptData*.txt")),
                     key=lambda f: int(re.search(r"scriptData(\d+)", f).group(1))):
        for k, v in json.load(open(fp, encoding="utf-8")).items():
            merged[int(k)] = v

    last_char = None          # 上一页保留的立绘角色名
    stat_match = 0; stat_cont = 0; stat_first = 0; changed = 0
    for p in sorted(merged):
        v = merged[p]
        c = v.get("c")
        if not c or ";" not in c:
            # 单立绘：更新延续态
            if c:
                last_char = char_name_of(c.split(";")[0])
            continue
        chars = c.split(";")
        spk = v.get("s", "")
        parts = speaker_parts(spk)

        keep = None
        # 1) 说话人匹配
        for sp in parts:
            target = SPEAKER_TO_CHAR.get(sp)
            if not target:
                continue
            for ch in chars:
                if char_name_of(ch) == target:
                    keep = ch
                    break
            if keep:
                break
        if keep:
            stat_match += 1
        else:
            # 2) 延续上一页立绘
            if last_char:
                for ch in chars:
                    if char_name_of(ch) == last_char:
                        keep = ch
                        break
            if keep:
                stat_cont += 1
            else:
                # 3) 第一个
                keep = chars[0]
                stat_first += 1
        if keep != c:
            v["c"] = keep
            changed += 1
        last_char = char_name_of(keep)

    # 写回
    chunks = {}
    for p, v in merged.items():
        chunk = (p - 1) // 500 + 1
        chunks.setdefault(chunk, {})[str(p)] = v
    for chunk, dd in chunks.items():
        fp = os.path.join(MERGE_DIR, f"scriptData{chunk}.txt")
        json.dump(dd, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"多立绘条目处理: 说话人匹配 {stat_match}, 延续上一页 {stat_cont}, 兜底第一个 {stat_first}")
    print(f"实际改动: {changed} 条 (c 字段缩减)")

if __name__ == "__main__":
    main()
