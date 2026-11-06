/* ============================================================
   CONFIG —— 全站共享配置，改这里就能换成你自己的信息
   ============================================================ */
window.CONFIG = {
  handle: "V.ZR",                                // 你的代号
  /* 项目控制台（WorkBuddy 托管地址，独立应用直链） */
  dashboardUrl: "https://project-dashboard-demo.app.workbuddy.host/?sharecode=5I4RS6HMRS&shareId=46b3ce8f7da348518862b93cd07c467c",
  typedLines: [
    "醒来吧，武士。我们有一座城市要烧。",
    "在夜之城，要么燃烧殆尽，要么璀璨一生。",
    "代码即义体，IDE 即军火库。"
  ],
  quotes: [
    { t: "我目睹过公司夺走农民的水源，最后是土地。还目睹过夜之城变成一台机器，用人们崩溃的精神、破碎的梦想以及民脂民膏来做燃料。长久以来公司控制着民生，拿走了一切，现在就连灵魂也不放过。", a: "强尼·银手 JOHNNY SILVERHAND" },
    { t: "夜之城，要么名扬四海，要么一文不值。", a: "杰克·威尔斯 JACKIE WELLES" },
    { t: "我已经不再是人了，V。我是网络空间本身。", a: "奥特·坎宁安 ALT CUNNINGHAM" },
    { t: "在外面混不下去，就回我这儿，门永远为你开着。", a: "维克多 VIKTOR" },
    { t: "人类的情感，只是故障。", a: "亚当重锤 ADAM SMASHE" }
  ],
  posts: [
    { tag:"快速黑客", date:"2077.10.02", time:"8 MIN", videoKey:"quickhack", title:"用 Wireshark 拆解一座 ICE 防火墙：从抓包到 Root 权限", excerpt:"把企业级防火墙想象成荒坂塔的安保网格。这篇讲清楚如何找到那条没人看守的侧门——以及进去之后如何优雅地不留日志。" },
    { tag:"义体改造", date:"2077.09.18", time:"12 MIN", videoKey:"cyberware", title:"义体过载自救指南：当操作系统开始跟你抢身体的控制权", excerpt:"赛博精神病不是传说。讲讲我在 9/10 负载下出现的幻听、幻觉，以及维克托教我的三条保命设置。" },
    { tag:"前端工程", date:"2077.09.05", time:"6 MIN", videoKey:"frontend", title:"HUD 界面设计规范：为什么夜之城的所有界面都在闪烁", excerpt:"故障字、扫描线、色彩分离——赛博 UI 的三件套不是装饰，是信息密度的妥协。一篇写给前端工程师的 HUD 设计观察。" },
    { tag:"恶土见闻", date:"2077.08.21", time:"10 MIN", videoKey:"badlands", title:"恶土公路旅行：从夜之城到圣多明戈，一路上的流浪者营地", excerpt:"离开城市才发现，墙外的世界只是换了一种方式破碎。记一次和阿德卡多游牧民族的同行。" },
    { tag:"高塔晚风", date:"2077.08.03", time:"15 MIN", videoKey:"tower", title:"夜之城没有真东西，她不一样", excerpt:"废弃高塔的天台，晚风混着铁锈味吹了一整夜。这座城市的霓虹是投影，誓言有有效期，忠诚按小时计费——只有塔顶那个抱着狙击枪看夜景的人，是真的。" },
    { tag:"来世酒吧", date:"2077.07.19", time:"5 MIN", videoKey:"afterlife", title:"来世酒吧点单指南：一杯 Jackie Welles 的正确喝法", excerpt:"龙舌兰、啤酒加青柠汁的完整比例，以及为什么侍者会用点燃的方式上酒。" }
  ],
  cyberware: [
    { slot:"操作系统", icon:"🖥️", name:"网络接入仓 · 北极星", en:"CYBERDECK // NETDRIVER MK.5", rarity:"r-iconic", rarityText:"不朽 · ICONIC",
      desc:"属于网络浪人的心脏。五级接口全开，RAM 池扩容至极限，可以同时压制一整支荒坂突击小队的防火墙。",
      rows:[["RAM 池","14 / 满配"],["接口等级","Lv.5"],["过热保护","已启用"],["来源","网络观察者掉落"]],
      price:"€$ 42,000", req:"智力 20", warn:"⚠ 警告：该义体与生物体征存在兼容性冲突，已上报临床异常记录。" },
    { slot:"额叶皮质", icon:"🧠", name:"并联式记忆扩充", en:"FRONTAL CORTEX // COX-2 CESIUM", rarity:"r-legend", rarityText:"传说 · LEGENDARY",
      desc:"记忆带宽翻倍。快速黑客上传速度提升，锁定目标几乎瞬时完成——在别人反应过来之前，你的战争已经结束了。",
      rows:[["上传速度","+35%"],["快速黑客冷却","-20%"],["可用插槽","4 / 4"]],
      price:"€$ 28,750", req:"智力 16", warn:"" },
    { slot:"眼睛", icon:"👁️", name:"基洛希光学 · 定制版", en:"KIROSHI OPTICS // MK.3", rarity:"r-epic", rarityText:"史诗 · EPIC",
      desc:"扫描范围内敌人弱点自动标记，网络接入点在视野内直接高亮。夜之城没有秘密，只有还没被扫描到的。",
      rows:[["目标标记","自动"],["弱点分析","实时"],["威胁评估","已激活"]],
      price:"€$ 16,500", req:"—", warn:"" },
    { slot:"手臂", icon:"🗡️", name:"螳螂刀", en:"MANTIS BLADES // ARMACYCLE-9", rarity:"r-iconic", rarityText:"不朽 · ICONIC",
      desc:"从袖口弹出的单分子利刃。近战收割利器，跳劈可以撕开装甲。低调的时候，它只是两条优雅的银线。",
      rows:[["伤害类型","物理 / 出血"],["蓄力跳劈","已解锁"],["护甲穿透","85%"]],
      price:"€$ 22,300", req:"反应 18", warn:"" },
    { slot:"骨骼", icon:"🦴", name:"显存式钛合金骨架", en:"SKELETON // BIONIC JOINTS", rarity:"r-epic", rarityText:"史诗 · EPIC",
      desc:"整副骨骼换成军用级钛合金。负重翻倍，坠落伤害免疫——从荒坂塔跳下来这种事，现在只算下楼。",
      rows:[["负重","+120%"],["坠落伤害","免疫"],["结构强度","A+"]],
      price:"€$ 19,800", req:"体格 14", warn:"" },
    { slot:"皮肤", icon:"🛡️", name:"皮下装甲 · 纳米镀层", en:"INTEGUMENTARY // SUBDERMAL GRIP", rarity:"r-legend", rarityText:"传说 · LEGENDARY",
      desc:"真皮层下编织的防弹纳米纤维。挨一发霰弹枪只是有点痒。代价是从此不敢做核磁共振。",
      rows:[["护甲值","+186"],["伤害减免","18%"],["再生速率","战斗中 +0.5/s"]],
      price:"€$ 31,200", req:"体格 16", warn:"" }
  ],
  tickerItems: [
    ["NCPD 通缉","沃森区发生恶性义体抢劫案，嫌犯持有军用级螳螂刀，市民请勿靠近"],
    ["新闻","荒坂塔今日例行全网络扫描，网络浪人注意规避三号频段"],
    ["天气","夜之城 · 夜间 19°C · 酸雨概率 70%，出门记得带伞和一把枪"],
    ["交易","来世酒吧今晚特调：Jackie Welles，点单即赠青柠汁"],
    ["NCPD 通缉","恶土公路多起游牧者车队袭击事件，阿德卡多已介入"],
    ["新闻","创伤小组白金会员套餐限时 8 折，救护无人机响应时间 60 秒"],
    ["警告","检测到未知网络接入尝试，ICE 状态：已拦截"]
  ],
  contact: {
    "EMAIL": "1948702723@qq.com",
    "NET / GitHub": "https://github.com/JohnnySilverhandV",
    "频道加密通话": "NC-77012 // SIGNAL SECURE",
    "线下据点": "来世酒吧 AFTERLIFE · 沃森区"
  }
};
