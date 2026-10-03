---
name: AI 测试用例生成助手
description: 图书馆卡片目录 —— 以冷调纸白、索引线与唯一冰川蓝印章组织的高密度测试工作台
colors:
  stamp: "#1a7fa9"
  stamp-deep: "#12607f"
  stamp-wash: "#e2f1f8"
  cabinet: "#13232d"
  cabinet-2: "#1b2f3b"
  cabinet-3: "#27404e"
  cabinet-ink: "#e6eef3"
  cabinet-ink-2: "#93a8b5"
  paper: "#eef2f5"
  paper-sunk: "#e4eaf0"
  card: "#ffffff"
  card-edge: "#d5dfe7"
  rule: "#d2dce4"
  rule-strong: "#adbdc9"
  ink: "#12212b"
  ink-2: "#3f4f5b"
  ink-3: "#4b5c68"
  ink-4: "#5f6f7a"
  danger: "#9d2a21"
  danger-wash: "#f1dad6"
  warn: "#8a6114"
  warn-wash: "#f0e4cb"
  ok: "#2c6a4c"
  ok-wash: "#dce8dd"
  info: "#2b4a78"
  info-wash: "#dce3ee"
typography:
  display:
    fontFamily: "IBM Plex Sans, PingFang SC, Microsoft YaHei, Source Han Sans SC, system-ui, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 600
    lineHeight: 1.24
    letterSpacing: "-0.02em"
  title:
    fontFamily: "IBM Plex Sans, PingFang SC, Microsoft YaHei, Source Han Sans SC, system-ui, sans-serif"
    fontSize: "1.4375rem"
    fontWeight: 600
    lineHeight: 1.24
    letterSpacing: "-0.02em"
  heading:
    fontFamily: "IBM Plex Sans, PingFang SC, Microsoft YaHei, Source Han Sans SC, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.42
    letterSpacing: "0.01em"
  body:
    fontFamily: "IBM Plex Sans, PingFang SC, Microsoft YaHei, Source Han Sans SC, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.62
    letterSpacing: "normal"
  label:
    fontFamily: "IBM Plex Sans, PingFang SC, Microsoft YaHei, Source Han Sans SC, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1.42
    letterSpacing: "0.06em"
  data:
    fontFamily: "IBM Plex Mono, Cascadia Mono, Consolas, Menlo, monospace"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.42
    letterSpacing: "-0.01em"
rounded:
  sm: "2px"
  md: "4px"
spacing:
  s1: "4px"
  s2: "8px"
  s3: "12px"
  s4: "16px"
  s5: "24px"
  s6: "32px"
  s7: "48px"
components:
  card:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "{spacing.s5}"
  button-primary:
    backgroundColor: "{colors.stamp}"
    textColor: "#ffffff"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "8px 15px"
    height: "32px"
  button-primary-hover:
    backgroundColor: "{colors.stamp-deep}"
    textColor: "#ffffff"
  button-secondary:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink-2}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "8px 15px"
    height: "32px"
  field:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "1px 11px"
    height: "32px"
  chip:
    backgroundColor: "{colors.paper-sunk}"
    textColor: "{colors.ink-2}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "0 6px"
    height: "20px"
  stamp:
    backgroundColor: "{colors.stamp-wash}"
    textColor: "{colors.stamp-deep}"
    typography: "{typography.data}"
    rounded: "{rounded.sm}"
    padding: "1px 6px"
  table-head:
    backgroundColor: "{colors.paper-sunk}"
    textColor: "{colors.ink-3}"
    typography: "{typography.label}"
    height: "36px"
  rail:
    backgroundColor: "{colors.cabinet}"
    textColor: "{colors.cabinet-ink}"
    padding: "{spacing.s5} 0 {spacing.s5} {spacing.s4}"
    width: "236px"
  rail-item-active:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
  trace-card:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "{spacing.s4} {spacing.s5} {spacing.s5}"
---

# Design System: AI 测试用例生成助手

## Overview

这套界面的世界是**图书馆卡片目录（Library Card Catalogue）**。它不为测试工具发明隐喻，而是借用一种已经被证明能承载"大量条目 + 交叉检索 + 手写标注"的物理系统：抽屉、索引卡、蓝灰印线、一枚印章。界面因此不像仪表盘，更像一间阅览室——纸面安静，条目密集，唯一鲜艳的东西是盖章。

世界只出借四样东西：**字体、色彩、密度、一个招牌动作**。布局、导航模型、表单控件一律使用 Web 平台与 Element Plus 的标准件，不做世界观化改装。这样做的理由是产品处于 Operate 模式：测试工程师要在一个工作时段内读完几百条用例，任何"有个性"的自定义控件都在消耗他们的注意力。

色彩基调是**蓝白**：冷调纸白的阅览室纸面，配一枚**冰川蓝**印章。蓝是这套系统里唯一的品牌表达，也是唯一"可以点哪里"的信号。

**The Four Loan Rule.** 一个世界元素只有在"字体、色彩、密度、招牌动作"这四类里才允许出现在本产品中；超出范围的表现欲一律退回平台标准件。

## Colors

纸面是阅览室的**冷调蓝白**（`#eef2f5`），不是奶油色，也不是纯白——它让白卡纸（`#ffffff`）能够从底面上"浮"出来，而不需要阴影。两者相差极小，因此卡片的边界由 1px 描边（`#d5dfe7`）承担，而不是靠投影。

目录柜体的深墨蓝（`#13232d`）只出现在左侧导航轨与深色浮层上。它是房间里唯一暗下去的面，用重量把导航与内容分开，同时把"蓝"从底噪一直延伸到最深处。

**冰川蓝（`#1a7fa9`）是全站唯一强调色**，并且严格分成两层：

| 层 | 令牌 | 值 | 允许出现在 |
|---|---|---|---|
| 面（填充） | `stamp` | `#1a7fa9` | 主按钮底、选中底、滑杆/开关/勾选、焦点描边、3px 覆盖率条 |
| 字（文字） | `stamp-deep` | `#12607f` | 链接、悬停文字、印章编号字、选中项文字 |
| 底（浅底） | `stamp-wash` | `#e2f1f8` | 印章编号底、表格行悬停底、选区底 |

这样分层的原因是可访问性：`#1a7fa9` 在白底上是 4.51:1（够用作面，也刚好够白字压在上面），但在纸面 `#eef2f5` 上只有 4.01:1，不足 4.5:1——所以**任何落在纸面上的蓝色文字都必须用深一档的 `#12607f`（6.0:1 以上）**。

状态语义色单独成体系，不参与品牌表达：危险红 `#9d2a21`、警告赭 `#8a6114`、成功绿 `#2c6a4c`、信息蓝 `#2b4a78`，始终以"底色 + 深墨文字"成对出现。

**The Two-Tier Blue Rule.** 冰川蓝只做"面"，深冰蓝只做"字"。浅色底上的蓝色文字永远不直接使用 `--stamp`。

**The Severity-Not-Brand Rule.** 优先级与运行状态只用语义色（红 / 赭 / 描边 / 绿），永远不用品牌蓝。品牌蓝回答的是"哪里可以点"，不是"哪条更严重"。

## Typography

UI 字体是 **IBM Plex Sans**，中文回落到 PingFang SC / 微软雅黑 / 思源黑体。它带一点技术感但不冷，字怀开，适合中文小字号密排。

数据字体是 **IBM Plex Mono**，但等宽**只为可读的数据服务，不作为装饰**：用例编号（`TC-BV-001`）、需求编号（`REQ-001`）、文档/用例集 ID、字段名与取值、时间戳、表格里的数字列。正文段落、按钮文案、标题一律不用等宽字体。

字号是一套固定的 rem 级数（0.75 / 0.8125 / 0.875 / 1 / 1.1875 / 1.4375 / 1.75rem），比例约 1.2，不随视口缩放。标题字重 600 并收紧字距（-0.02em）；字段标签使用 0.75rem + 0.06em 宽字距，全大写仅在英文标签上使用。

**The Mono-For-Data Rule.** 等宽字体是一台打印机，不是一种风格；只有当字符串本身是"必须逐字符核对"的编号或取值时才动用它。

## Layout

内容区建立在 4px 网格上（`--u: 4px`），间距级数 4 / 8 / 12 / 16 / 24 / 32 / 48。页面结构固定为：左侧 236px 深墨蓝导轨（<900px 折叠成顶部标签条）+ 52px 顶栏 + 纸面内容区。工作台使用 1.9:1 的双栏（左输入、右设置），三个及以上等宽卡片用 2/3 栏网格，1100px 以下全部收成单栏。

**密度是功能，不是偏好。** 顶栏的三档开关（紧凑 / 标准 / 宽松）通过 `data-density` 一次性重写行高、卡片内边距、单元格内边距、堆叠间距、表格字号与导轨宽度，并持久化到 localStorage。紧凑档行高 32px、单元格 6px 10px；标准档 38px / 10px 12px；宽松档 46px / 14px 16px。测试工程师在浏览阶段调紧、在核对阶段调松，是同一个页面的两种读法。

表格在小屏不横向溢出页面，而是在卡片内部产生横向滚动，并让横向滚动条常显——8 列数据必须能被发现，而不是被隐藏。

**The Density-Is-Function Rule.** 任何"要不要更紧凑一点"的争论都由密度开关回答，而不是由某个页面私自调整间距。

## Elevation & Depth

这是一个**平面系统**。立面只声明一次：普通卡片是白底 + 1px 描边（`#d5dfe7`），不叠阴影、不叠第二层卡片。深度来自"纸面 / 白卡 / 下沉底"三个色阶（`#eef2f5` → `#ffffff` → `#e4eaf0`），而不是 blur 半径。

阴影只保留给真正浮在内容之上的表面：对话框、下拉、提示气泡。它们使用极短的上投影加一段低透明度的扩散，且投影颜色是冷调深墨蓝（`rgba(18, 33, 43, …)`）而不是暖黑——从纸面上掉下来的东西也应该是冷的。

**The Flat-Once Rule.** 每个面只声明一次它的高度。禁止在卡片里再套一张带描边的卡片；需要分组时用一条 1px 细线或虚线书写线，而不是再画一个框。

## Shapes

形状语言是"纸张"：圆角一律 4px（小元素 2px），按钮、输入框、卡片、对话框共用同一个角值。没有胶囊形按钮——标签与徽章同样使用 2px 直角，因为它们模仿的是打印出来的小方块，不是现在流行的圆角 chip。

唯一使用全圆角（999px）的地方是滑杆轨道、滚动条滑块与状态圆点，因为它们本身就是圆形的物理对象。

**The Paper-Corner Rule.** 角是纸切出来的，只允许 4px 与 2px 两个值；出现第三个圆角值就说明引入了不属于这个世界的形状。

## Components

**卡片**：白底 + 1px 描边 + 4px 圆角，头部为 12px 24px 内边距加一条底部细线，正文 24px 内边距。卡片没有阴影。

**按钮**：主按钮是冰川蓝实底 + 白字，悬停加深到深冰蓝 `#12607f`；次按钮是白底 + 描边。两者高度 32px、圆角 4px、字重 500。禁用态统一退成纸灰底 + 灰边 + 灰字，不做降透明度处理。

**字段**：输入框、下拉、文本域都是白底 + 1px 描边，聚焦时描边变冰川蓝并外扩 2px 的浅蓝描边（`outline`），不使用 Element 默认的柔光晕。

**标签 / 印章**：通用标签是纸灰底 + 描边 + 2px 圆角的 20px 小方块；需求编号使用"印章"样式——冰蓝浅底（`#e2f1f8`）、深冰蓝字（`#12607f`）、半透明蓝边、等宽字体，代表它是一条可追溯的来源。

**优先级标记**：形状与文字同时编码，绝不只靠颜色——P0 是实心红方块 + 文字（阻断），P1 是实心赭方块（严重），P2 是空心灰框（一般），P3 是虚线灰框（轻微）。最高优先级用**危险红**而不是品牌蓝，避免"品牌色"与"严重程度"互相污染。

**导轨**：深墨蓝底、浅色文字，选中项用纸面色块"探进"内容区，右侧不留边距，形成一个从抽屉里抽出来的标签。它承担全部顶层导航，不做折叠成图标。

**追溯卡（招牌动作）**：展开一条用例行时，从行里抽出一张索引卡——顶端是 1px 装订线（不是色条），把 `requirement_ids` 展开成来源需求原文，再依次给出执行步骤、测试数据、前置条件、交叉索引（同源用例）与备注。入场是唯一被编排的动效：6px 上移 + 淡入，220ms。它演示的是产品的可追溯机制本身，不是装饰。

**覆盖率 extent bar**：3px 高的细轨道，冰川蓝填充，用 `transform: scaleX()` 从左侧展开（不是动画 `width`），保证滚动与重排不产生抖动。

## Do's and Don'ts

- Do 让纸面保持冷调蓝白，靠 1px 描边而不是阴影区分卡片。
- Do 把冰川蓝留给"面"（填充 / 描边 / 焦点 / 选中），蓝色文字一律用深冰蓝。
- Do 把优先级与状态交给语义色，让品牌蓝只表达"可交互"。
- Do 用等宽字体标记所有编号与字段取值，让它们可以逐字符核对。
- Do 让密度开关同时改变行高、内边距、字号与导轨宽度，保持整站节奏一致。
- Do 在优先级等关键信息上同时给出形状/文字与颜色两种编码。
- Don't 在纸面 `#eef2f5` 上直接使用 `--stamp` 作为文字颜色（只有 4.01:1）。
- Don't 使用装饰性色条、渐变文字、发光阴影或 emoji 图标。
- Don't 在卡片里再嵌一张带描边的卡片；需要分组时用细线。
- Don't 为"好看"给控件换形状或加动效——动效只服务于追溯卡抽出这一个瞬间。
- Don't 用颜色作为优先级或状态的唯一区分手段。
- Don't 把"流畅"理解为更多动画；本产品的流畅来自更少的重排、更快的首屏与更稳的滚动。
