# DRACU-RIOT 选项 flag 规则表（供填写 hiddenPages 条件）

> `choice[选项页]` = 玩家在该选项页选择的序号(1-5)。
> hiddenPages 条件写法参考千恋万花：`(choice) => { if(choice[3113] === 2) return 3912; return 3871; }`

### 选项页 3113  (★本編－その３（初事件）)
- **1. 和美羽一起**: exp=`f.sel_flag = 1 , f.miu_flag++`  eval=``  target=`*part003_01A`
- **2. 和布良同学一起**: exp=`f.sel_flag = 2 , f.azu_flag++`  eval=``  target=`*part003_01B`

### 选项页 4418  (★本編－その６（市長との出会い）)
- **1. 肯定是巨乳**: exp=`f.nic_flag ++`  eval=``  target=`*part006_01A`
- **2. 肯定是贫乳**: exp=``  eval=``  target=`*part006_01B`
- **3. 肯定是美乳**: exp=``  eval=``  target=`*part006_01C`
- **4. 说到底女性的价值并不在胸部**: exp=``  eval=``  target=`*part006_01D`

### 选项页 5080  (★本編－その７（莉音とエリナ）)
- **1. 作为回礼试着邀请稻丛同学**: exp=`f.sel_flag = 1 , f.rio_flag ++`  eval=``  target=`*part007_01A`
- **2. 果然还是算了吧**: exp=`f.sel_flag = 2 , f.eri_flag ++ , f.nic_flag ++`  eval=``  target=`*part007_01B`

### 选项页 5658  (★本編－その８（第一部完？）)
- **1. 没办法，打吧**: exp=`f.miu_flag ++`  eval=``  target=`*part008_01A`
- **2. 怎么可能打得下去**: exp=`f.azu_flag ++ , f.eri_flag ++ , f.rio_flag ++ , f.nic_flag ++`  eval=``  target=`*part008_01B`

### 选项页 6800  (★本編－その１１（ＥＶ枚数豪華だな）)
- **1. 帮她涂吧**: exp=``  eval=``  target=`*part011_01A`
- **2. 想想其他办法**: exp=``  eval=``  target=`*part011_01B`

### 选项页 6822  (★本編－その１１（ＥＶ枚数豪華だな）)
- **1. 问问她要不要我来涂**: exp=`f.miu_flag ++`  eval=``  target=`*part011_02A`
- **2. 什么也不说**: exp=`f.eri_flag ++`  eval=``  target=`*part011_02B`

### 选项页 7022  (★本編－その１１（ＥＶ枚数豪華だな）)
- **1. 也让布良同学来帮忙吧**: exp=`f.azu_flag ++`  eval=``  target=`*part011_03A`
- **2. 自己一个人没问题的**: exp=`f.rio_flag ++`  eval=``  target=`*part011_03B`

### 选项页 7669  (★本編－その１２（クスリ再び）)
- **1. 那就拜托你了，艾莉娜**: exp=`f.eri_flag ++ , f.sel_flag = 1`  eval=`f.eri_flag == 3`  target=`*part012_01A`
- **2. 那就拜托你了，稻丛同学**: exp=`f.rio_flag ++ , f.nic_flag ++ , f.sel_flag = 2`  eval=`f.rio_flag == 3 || f.nic_flag == 3`  target=`*part012_01B`
- **3. 这还是太给她们添麻烦了吧**: exp=`f.miu_flag ++ , f.azu_flag ++`  eval=``  target=`*part012_01C`

### 选项页 12794  (エリナ－その４_θ（初体験）)
- **1. 在里面射出**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=``
- **2. 在外面射出**: exp=`f.sel_flag = 1`  eval=`checkIN && checkOUT`  target=``
- **3. 绝对要在外面射出**: exp=`f.sel_flag = 2`  eval=`checkOUT`  target=``

### 选项页 14098  (エリナ－その５_θ（来訪者）)
- **1. 中出**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=``
- **2. 外射**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=``

### 选项页 15113  (エリナ－その６_β（邂逅）)
- **1. 在里面射出**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=``
- **2. 在外面射出**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=``

### 选项页 15954  (エリナ－その７_β（デートと急変）)
- **1. 在口中射出**: exp=`f.sel_flag = 0`  eval=`checkMOUTH`  target=`*eri07_01A`
- **2. 在口外射出**: exp=`f.sel_flag = 2`  eval=`checkFACE`  target=`*eri07_01B`

### 选项页 16013  (エリナ－その７_β（デートと急変）)
- **1. 就这样射出来**: exp=``  eval=`checkMOUTH`  target=``
- **2. 抵抗一下**: exp=`f.sel_flag ++`  eval=`checkFACE`  target=``

### 选项页 16191  (エリナ－その７_β（デートと急変）)
- **1. 中出**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=``
- **2. 外射**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=``

### 选项页 18410  (エリナ－その１０（マンネリ）)
- **1. 中出**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=``
- **2. 外射**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=``

### 选项页 20586  (ニコラ－その４_β（既成事実）)
- **1. 在腔内射出来**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=``
- **2. 对着身体射出来**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=``

### 选项页 20994  (ニコラ－その４_β（既成事実）)
- **1. 在腔内射出来**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=``
- **2. 对着身体射出来**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=``

### 选项页 21625  (ニコラ－その５（説得_軽量化）)
- **1. 中出**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=``
- **2. 外射**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=``

### 选项页 21951  (ニコラ－その５（説得_軽量化）)
- **1. 中出**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=``
- **2. 外射**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=``

### 选项页 22248  (ニコラ－その６（ネコだにゃ）)
- **1. 在口中射出**: exp=`f.sel_flag = 0`  eval=`checkMOUTH`  target=``
- **2. 挂在脸上**: exp=`f.sel_flag = 1`  eval=`checkFACE`  target=``

### 选项页 22276  (ニコラ－その６（ネコだにゃ）)
- **1. 解下来**: exp=`f.eye_flag = 0`  eval=``  target=`*nicEX_02A`
- **2. 就这样吧**: exp=`f.eye_flag = 1`  eval=``  target=`*nicEX_02B`

### 选项页 22385  (ニコラ－その６（ネコだにゃ）)
- **1. 就这样射出来**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=``
- **2. 射到身体上**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=``

### 选项页 22543  (ニコラ－その６（ネコだにゃ）)
- **1. 在口中射出**: exp=`f.sel_flag = 0`  eval=`checkMOUTH`  target=``
- **2. 挂在脸上**: exp=`f.sel_flag = 1`  eval=`checkFACE`  target=``

### 选项页 22571  (ニコラ－その６（ネコだにゃ）)
- **1. 解下来**: exp=`f.eye_flag = 0`  eval=``  target=`*nicEX_02A`
- **2. 就这样吧**: exp=`f.eye_flag = 1`  eval=``  target=`*nicEX_02B`

### 选项页 22680  (ニコラ－その６（ネコだにゃ）)
- **1. 就这样射出来**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=``
- **2. 射到身体上**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=``

### 选项页 26472  (莉音－第４話（はじめての）ver5)
- **1. 中出**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=`*rio04_01A`
- **2. 外射**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=`*rio04_01B`

### 选项页 27463  (莉音－第５話（献身）ver5)
- **1. 希望她能张开嘴接住**: exp=`f.sel_flag = 1`  eval=`checkMOUTH`  target=`*rio05_01A`
- **2. 希望能吞下我的精液**: exp=`f.sel_flag = 0`  eval=`checkFACE`  target=`*rio05_01B`

### 选项页 27677  (莉音－第５話（献身）ver5)
- **1. 中出**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=`*rio05_02A`
- **2. 外射**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=`*rio05_02B`

### 选项页 29843  (莉音－第８話（失踪）ver5)
- **1. 就这样在腔内**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=`*rio08_01A`
- **2. 不管怎么说也要在腔外**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=`*rio08_01B`

### 选项页 31641  (莉音－第Ｘ話（恥ずかしいこと）ver5)
- **1. 想让她全部喝下去**: exp=`f.sel_flag = 0`  eval=`checkMOUTH`  target=`*rioEX_01A`
- **2. 想射在脸上**: exp=`f.sel_flag = 1`  eval=`checkFACE`  target=`*rioEX_01B`

### 选项页 31944  (莉音－第Ｘ話（恥ずかしいこと）ver5)
- **1. 中出**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=`*rioEX_02A`
- **2. 外射**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=`*rioEX_02B`

### 选项页 35286  (美羽－その４（初体験）)
- **1. 小鸡●鸡**: exp=`f.word_flag='a',f.word='小鸡●鸡', f.wordx='小，'`  eval=``  target=``
- **2. 大肉●棒**: exp=`f.word_flag='b',f.word='大肉●棒',f.wordx='大，'`  eval=``  target=``
- **3. 肉●棒**: exp=`f.word_flag='c',f.word='肉●棒',f.wordx='肉，'`  eval=``  target=``

### 选项页 35534  (美羽－その４（初体験）)
- **1. 中出**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=``
- **2. 外射**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=``

### 选项页 36903  (美羽－その６（囮）)
- **1. 中出**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=`*miu06_01A`
- **2. 外射**: exp=`f.sel_flag = 2`  eval=`checkOUT`  target=`*miu06_01B`

### 选项页 36994  (美羽－その６（囮）)
- **1. 中出**: exp=``  eval=`checkIN`  target=``
- **2. 外射**: exp=`f.sel_flag ++`  eval=`checkOUT`  target=``

### 选项页 38277  (美羽－その７（誘拐）)
- **1. 还是在嘴里射出来吧…**: exp=`f.sel_flag = 0`  eval=`checkMOUTH`  target=`*miu07_01A`
- **2. 还是射在脸上吧…**: exp=`f.sel_flag = 1`  eval=`checkFACE`  target=`*miu07_01B`

### 选项页 38391  (美羽－その７（誘拐）)
- **1. 中出**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=`*miu07_02A`
- **2. 外射**: exp=`f.sel_flag = 2`  eval=`checkOUT`  target=`*miu07_02B`

### 选项页 38482  (美羽－その７（誘拐）)
- **1. 中出**: exp=``  eval=`checkIN`  target=``
- **2. 外射**: exp=`f.sel_flag ++`  eval=`checkOUT`  target=``

### 选项页 41693  (美羽－その１０（エピ）)
- **1. 中出**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=``
- **2. 外射**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=``

### 选项页 41802  (美羽－その１１（おまけ）)
- **1. 小鸡●鸡**: exp=`f.word_flag='a',f.word='小鸡●鸡', f.wordx='小，'`  eval=``  target=``
- **2. 大肉●棒**: exp=`f.word_flag='b',f.word='大肉●棒',f.wordx='大，'`  eval=``  target=``
- **3. 肉●棒**: exp=`f.word_flag='c',f.word='肉●棒',f.wordx='肉，'`  eval=``  target=``

### 选项页 42151  (美羽－その１１（おまけ）)
- **1. 中出**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=``
- **2. 外射**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=``

### 选项页 42270  (美羽－その１１（おまけ）)
- **1. 中出**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=``
- **2. 外射**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=``

### 选项页 47052  (梓シナリオ_５話hシーンスキップ)
- **1. 射在嘴里**: exp=`f.sel_flag = 0`  eval=`checkMOUTH`  target=`*azu05_01A`
- **2. 射在脸上**: exp=`f.sel_flag = 1`  eval=`checkFACE`  target=`*azu05_01B`

### 选项页 47887  (梓シナリオ_５話hシーンスキップ)
- **1. 在梓的里面释放出我的爱意！**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=`*azu05_02A`
- **2. 不对等等，第一次应该在外面吧！**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=`*azu05_02B`

### 选项页 48836  (梓シナリオ_fix6（台詞数調整後）)
- **1. 在最深处射精！**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=`*azu06_01A`
- **2. 在屁股上射精！**: exp=`f.sel_flag = 2`  eval=`checkOUT`  target=`*azu06_01B`

### 选项页 48875  (梓シナリオ_fix6（台詞数調整後）)
- **1. 再用屁股来……**: exp=`f.anus_flag = 1`  eval=``  target=`*azu06_02A`
- **2. 果然还是太勉强了**: exp=`f.anus_flag = 0`  eval=``  target=`*azu06_02B`

### 选项页 48934  (梓シナリオ_fix6（台詞数調整後）)
- **1. 在屁股里面射出来**: exp=``  eval=`checkIN`  target=`*azu06_03A`
- **2. 拔到外面射出来**: exp=`f.sel_flag ++`  eval=`checkOUT`  target=`*azu06_03B`

### 选项页 49860  (梓シナリオ_fix6（台詞数調整後）)
- **1. 在口中！**: exp=`f.sel_flag = 0`  eval=`checkMOUTH`  target=`*azu06_04A`
- **2. 在口外！**: exp=`f.sel_flag = 2`  eval=`checkFACE`  target=`*azu06_04B`

### 选项页 50008  (梓シナリオ_fix6（台詞数調整後）)
- **1. 在梓的口中！**: exp=``  eval=`checkMOUTH`  target=`*azu06_05A`
- **2. 在梓的脸上！**: exp=`f.sel_flag ++`  eval=`checkFACE`  target=`*azu06_05B`

### 选项页 50168  (梓シナリオ_fix6（台詞数調整後）)
- **1. 在腔内射精！**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=`*azu06_06A`
- **2. 在外面射精！**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=`*azu06_06B`

### 选项页 51941  (梓シナリオ_fix9（台詞数調整後）)
- **1. 再用屁股来……**: exp=`f.anus_flag = 1`  eval=``  target=``
- **2. 果然还是太勉强了**: exp=`f.anus_flag = 0`  eval=``  target=``

### 选项页 52356  (梓シナリオ_fix9（台詞数調整後）)
- **1. 就这样射精**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=`*azuEX_01A`
- **2. 在屁股上射精**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=`*azuEX_01B`

### 选项页 52579  (梓シナリオ_fix9（台詞数調整後）)
- **1. 插入里面射精！**: exp=`f.sel_flag = 0`  eval=`checkIN`  target=`*azuEX_02A`
- **2. 按住阴蒂射精！**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=`*azuEX_02B`

### 选项页 52672  (梓シナリオ_fix9（台詞数調整後）)
- **1. 就这样在肠内射精！**: exp=``  eval=`checkIN`  target=`*azuEX_03A`
- **2. 按住阴蒂射精！**: exp=`f.sel_flag = 1`  eval=`checkOUT`  target=`*azuEX_02B`
