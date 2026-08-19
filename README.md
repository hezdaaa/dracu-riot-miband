# DRACU-RIOT 小米手环移植工具

将《**DRACU-RIOT!**》（柚子社 / Yuzusoft，2012 中文版）移植到 **小米手环**（快应用，336×480 竖屏）的一整套转换脚本。

从游戏资源解包 → 剧本转换 → 分支/路线配置生成 → 立绘/背景/CG 资源处理 → 打包，全流程脚本化，可重复执行。

> 📖 **想移植新作品？请先读 [《移植指南.md》](./移植指南.md)** —— 完整讲解「任何 KiriKiri2 文字冒险 → 小米手环」的通用方法论（解包/反编译/分支解析/转换/资源处理/验证），DRACU-RIOT 作为贯穿示例。

## 功能特性

- **完整剧本**：70 个剧本、383 场景、52,733 条文本 → 全局线性页表 52,787 页
- **分支系统**：54 个选项点、flag 路线判定（5 位女主）、本编 4 版アンダーカバー变体
- **5 条女主路线**：梓 / 美羽 / 莉音 / 艾莉娜 / 尼古拉 + 各自**后日谈**（经 lct 流程图 / more 后日谈入口）
- **立绘实时合成**：身体 + 表情分层拼装（`char_data.txt` 驱动）
- **特效还原**：闪光弹、震动、模糊、立绘滑入、交叉淡化
- **资源压缩**：背景/CG/SD 批量处理，evig 控制在 10MB 内
- **CG 鉴赏** / 流程图 / 章节跳转 / 存档读档

## 项目结构（期望布局）

```
仓库根/
├── 移植指南.md            # ★ 通用移植方法论（新作品先读这个）
├── README.md              # 本项目说明
├── 转换工具/              # ★ 本仓库：转换脚本 + 生成数据
│   ├── *.py
│   ├── cg_dedup_map.json   # CG 去重映射（dr_merge 依赖）
│   ├── branchConfig.js     # 生成的分支配置（参考）
│   └── docs/               # 生成文档
├── 剧本json/              # FreeMote 反编译的原剧本 JSON（需自行生成）
├── 手环脚本/              # 转换中间产物（逐剧本页表 + .map.json）
├── 剧本_合并/             # 合并后的全局线性页表 scriptData*.txt（500 页/块）
├── src外/                 # 资源处理中间目录（bg/cg/cimg/sd/立绘源）
└── src/                   # 小米手环快应用源码（播放器、各页面）
```

> 注意：**剧本/图片等游戏资源不包含在本仓库**（版权原因）。转换脚本假设上述目录布局与游戏资源已就位。

## 转换管线

```
① 解包 xp3 ─────────── unpack（自写，KiriKiri2）
② .ks.scn → JSON ───── FreeMote PsbDecompile.exe（外部工具）
③ JSON → 手环脚本 ───── scn2json.py + dr_script_converter.py
④ 合并全局页表 ──────── dr_merge.py（70 剧本 → scriptData*.txt）
⑤ 分支配置 ──────────── build_branch_config.py（选项/路由/跳转/结局）
⑥ 多立绘缩减 ────────── reduce_chars.py（按说话人只留一个）
⑦ 资源处理 ──────────── 立绘合成 / 背景 / CG / SD / 压缩
⑧ 打包 ──────────────── 小米手环快应用（rpk）
```

### 分支配置生成（核心，可重复执行）

```
cd 转换工具
python build_branch_config.py --patch   # dr_merge 重生成 + 选项目标修正 + 生成 branchConfig
python reduce_chars.py                  # 多立绘缩减（必须在 dr_merge 之后）
```

- `build_branch_config.py` 输出 `branchConfig.js`（注入播放器 `detail.ux` 的 `branchConfig` 对象）与 `flag_rules.md`。
- 12 个条件路由（路线分叉/变体选择）按 flag 累计关系自动推导，注释保留原始 `eval` 条件供人工核对。
- `dr_merge.py` 重新生成会覆盖脚本修正 → 需按上述顺序重跑。

## 工具说明

### 剧本管线
| 脚本 | 作用 |
|---|---|
| `scn2json.py` | 用 FreeMote 批量把 `.ks.scn` → JSON 剧本 |
| `dr_script_converter.py` | 剧本 JSON → 手环脚本格式（文本/背景/立绘/CG/特效字段） |
| `dr_merge.py` | 70 个剧本合并为全局线性页表，背景/CG/SD 映射 |
| `build_branch_config.py` | 分支配置生成（noNextPages / noBackPages / hiddenPages / end / 条件推导） |
| `reduce_chars.py` | 多立绘按说话人缩减为 1 个（匹配 → 延续 → 兜底） |
| `extract_jumps.py` | 全量跳转提取分类表（`跳转分类表.md`） |
| `validate_jumps.py` | 跳转数据交叉校验 |
| `analyze_scripts.py` | 剧本资源引用分析 |

### 资源处理
| 脚本 | 作用 |
|---|---|
| `build_char_data.py` | 立绘合成数据 `char_data.txt` 生成（身体/表情坐标、缩放） |
| `fg_asset.py` / `fg_compose.py` / `fg_prepare.py` | 立绘分层合成（身体 + 表情差分） |
| `cg_compose.py` / `cg_unpack.py` / `cg_process.py` / `cg_verify.py` / `dedup_cg.py` | CG 解包/旋转/裁切/去重/校验 |
| `build_cg_map_extra.py` | CG 去重映射补充 |
| `bg_mapping.py` / `bg_process.py` | 背景 stagename/timename → 实际图片映射与处理 |
| `sd_process.py` | SD 小人处理（336×480 透明 PNG） |
| `compress_cimg.py` / `clean_cimg.py` / `fix_premultiply.py` | 图片压缩/清理/预乘修复 |
| `gen_gallery_rules.py` / `update_gallery_rule.py` / `update_image_config.py` | CG 鉴赏规则与图片配置生成 |

## 前置要求

- **正版《DRACU-RIOT!》**（柚子社，中文版 2012，KiriKiri2 引擎）
- **FreeMote**（`PsbDecompile.exe`，scn → JSON）
- **Python 3** + `Pillow`（图片处理）
- **小米手环快应用开发环境**（打包 rpk）

## 免责声明

- 本仓库**仅包含转换工具脚本与生成文档，不含任何游戏资源/数据**。
- 请使用**合法取得**的游戏副本，仅用于个人学习与移植研究。
- 《DRACU-RIOT!》版权归 **柚子社（Yuzusoft）** 所有，本工具与官方无关。

## 致谢

- 柚子社（Yuzusoft）：原作《DRACU-RIOT!》
- FreeMote：KiriKiri 脚本反编译工具
- 参考移植框架：缘之空、千恋万花 小米手环移植项目
