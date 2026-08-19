# DRACU-RIOT 分支配置生成说明

> 生成时间：2026-08-19　生成器：`build_branch_config.py`

## 产物清单

| 文件 | 用途 |
|---|---|
| `branchConfig.js` | 注入 `detail.ux` 的 `branchConfig` 数据（整体替换原空对象） |
| `flag_rules.md` | 全部选项页的 flag 效果表，供填写 hiddenPages 条件 |
| `剧本_合并/scriptData*.txt` | 已修正 flag 型选项目标（指向 dummy 公共内容起点） |

## 如何接入 detail.ux

1. 打开 `src/pages/detail/detail.ux`，定位 `branchConfig: {`（约 275 行）。
2. 用 `branchConfig.js` 的内容**整体替换**该对象（当前是 4 个空对象 `{}`）。
3. **填写 12 个 hiddenPages 条件路由**（见下节），把 `/* TODO 条件 */` 替换成真实的 `choice[选项页]` 条件。
4. 重新打包测试。

> 注意：`branchConfig.js` 是一个对象字面量片段（`branchConfig: {...}`），直接粘贴到原位置即可。

## 待人工填写的 12 个条件路由

生成器已把页面 key、目标页、原 eval 条件写在注释里。你只需按 `flag_rules.md` 把 flag 判断翻译成 `choice[选项页]` 形式。

| 路由页 | 位置 | 原条件 | 建议写法（需对照原作核实） |
|---|---|---|---|
| 3870 | 本编その４ Main_part_4 | `f.sel_flag == 2` | `if(choice[3113] === 2) return 3912; return 3871;`（sel_flag 由 3113 设定） |
| 3950 | 本编その４ part4_01com | `f.sel_flag == 2` | `if(choice[3113] === 2) return 3952; return 3951;` |
| 5749 | 本编その８ part008_01B | `f.sel_flag == 2` | `if(choice[5080] === 2) return 5764; return 5750;`（sel_flag 由 5080 设定） |
| 8234 | 本编その１３ Main_part_13 | `rio/eri/nic_flag == 4` | 按 flag_rules 累计判断 |
| 8324 | 本编その１３ dummy1 | `miu_flag == 4` | 同上 |
| 8560 | 本编その１４莉音 Main_part_14rio | `nic_flag == 4` | 同上 |
| 8846 | 本编その１５ Main_part_15 | `rio_flag==4 ‖ nic_flag==4` | 同上 |
| 8873 | 本编その１５ com15_com | `eri_flag == 4` | 同上 |
| 9019 | 本编その１５_２ Main_part_15_ret | 全 flag != 4 → normal_end | 同上（路线前判定） |
| 9022 | 本编その１５_２ dummy1 | 5 个女孩 flag == 4 | **路线分叉**，核心路由 |
| 38287 | 美羽その７ miu07_01com | `sel_flag == 1` | `if(choice[38277] === 2) return 38302; return 38288;` |
| 52578 | 梓 fix9 azuEX_01com | `anus_flag == 1` | 需追查 anus_flag 由哪个选项设置 |

### 女孩 flag 路线判定（9022）

flag 累计来源（见 flag_rules.md）：
- **miu_flag**：3113-①、5658-①、6822-①、7669-③
- **azu_flag**：3113-②、7022-①、7669-③
- **rio_flag**：5080-①、7022-②、7669-②
- **eri_flag**：5080-②、6822-②、7669-①
- **nic_flag**：4418-①、5080-②、7669-②

`f.xxx_flag == 4` ≈ 玩家在该女孩的所有累计选项里全选她。可据此写条件，或用运行时累计。

## 生成逻辑摘要

- **线性模型**：合并流是全局线性页表，翻页 = +1，特判跳转由 branchConfig 处理。
- **noNextPages**：场景默认跳转目标 ≠ 物理下一页时，`{分支末页: 目标页}`（分支跳过兄弟分支到合流）。
- **noBackPages**：所有 noNextPages 目标页 `{页: 页}` 自环（回退堵死，参考千恋万花）。
- **hiddenPages**（选项路由，20 个自动生成）：flag 型选项场景的 dummy 公共内容末尾，按 `choice[选项页]` 路由到分支内容。**已修复原转换器跳过公共高潮内容的 bug。**
- **hiddenPages**（条件路由，12 个待填）：flag 条件跳转（路线分叉、变体选择、跨场景 sel_flag 检查）。
- **end**：各路线结尾场景末页 + normal_end（11 处）。

## 已知事项

1. **向后跳转 11 处**均为合法结构：`9339→8981` 是艾莉娜アンダーカバー(Eri_part_00)演完回路线分叉；其余 10 处为尼可拉 `:N` 二周目 H 结构（正常流程不可达）。
2. **`label:N` 跳行**：`*nic04_01A:2` 等是独立标签（FreeMote 保留），已按完整标签解析。
3. **`kag.isRecollection` / `sf.clear_*` 条件已忽略**（回想模式与二周目解锁，本移植不实现）。
4. **部分路线有多个 end 点**（如梓 fix8 与 fix9 都指向回标题）——正常流程只会到达其一，另一个对应"后日谈/章节"，需你确认是否可达。
5. **选项可见性 eval**（checkIN/f.eri_flag==3 等）未做过滤——所有选项都显示。如需按原作隐藏选项，需要在 detail.ux 选项页加条件渲染。
6. **`剧本_合并` 已被本脚本修改**，重新跑 `dr_merge.py` 会覆盖选项目标修正，需在合并后重跑本脚本（或把修正逻辑并入 dr_merge）。
