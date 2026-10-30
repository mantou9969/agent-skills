---
name: xiaohongshu-store-console
description: 运营“后现代马铃薯”的本地小红书商品搬运控制台，处理 1688 选品导入、小红书画风反推、Antigravity 商品图生成、千问审核与千帆提交。用于批量选品、生成商品图、长任务恢复、审核和发布前检查。
---

# 小红书店铺搬运控制台

目标是把一个商品从 1688 资料推进到小红书可发布资产。默认控制台位于
`C:\Users\21878\Desktop\每天进度\codex`，店铺名为“后现代马铃薯”。

## 开始或恢复

1. 检查 `http://127.0.0.1:4173` 是否可访问。
2. 如果服务未运行，执行：

   ```powershell
   powershell -ExecutionPolicy Bypass -File "C:\Users\21878\.codex\skills\xiaohongshu-store-console\scripts\start_workbench.ps1"
   ```

3. 读取 `/api/state` 和 `/api/workflows/<jobId>`，先恢复现有 DAG，不重新创建已完成任务，不重复向 Antigravity 发送请求。
4. 用户需要整晚运行或想确认队列是否仍在执行时，读取
   [references/operations.md](references/operations.md)。

前端默认打开“商品生产台”，按商品、素材、阶段和下一步操作展示；需要诊断或微调节点依赖时切换到“节点执行图”。不要只根据节点页推断业务进度。
顶部“使用指南”用于说明商品流程、电商 skill、ComfyUI 和 Comfy Cloud 登录的区别。ComfyUI 本地运行不需要账户。

## 固定数据流

```text
1688 商品链接
→ 商品资料与图片
→ 保本 ROI 定价
→ 文案生成
→ 价格与文案确认
→ 本地画风照片或小红书参考图
→ Gemini / Antigravity 结构化画风卡并保存为可复用风格预设
→ 提示词确认门
→ Antigravity 只生成不含商品的无商品背景板
→ 本地从当前 1688 原图抠出真实商品并合成四张成品
→ 本地合成哈希守卫 + Qwen/MiMo 事实审核
→ 千帆专用 Edge 自动填写
→ 最终发布确认门
→ 人工确认发布
```

每一步必须有磁盘证据。状态不能代替产物：`stage=1` 不代表 Antigravity 已送达，
必须存在发送时间；`stage=2` 必须有成品图片和 `done.flag`。

## 工作规则

- 用户是个人店，不声称商品 API 可以授权自建应用；上架使用正常网页操作或受支持的搬家工具。
- 优先使用用户已安装的 1688 Smart Scraper，不重复抓取；插件导出的 XLSX/Markdown 是输入契约。
- 小红书参考图只用于抽象构图、光线、颜色、镜头、道具和氛围，不复制专属文案、其他商品或品牌标识。
- 一个博主只提取一次画风卡并缓存。生成时让同一个模型同时读取商品图和画风卡。
- 正式生产禁止让生图模型重新绘制商品主体。Antigravity 只接收画风参考并输出无商品背景板；商品必须来自当前 1688 原图的真实抠图，再由本地合成器放到背景上。
- 画风参考板只允许包含抽象摄影语言。禁止把参考博主的商品、人物身份、品牌、logo、包装或文字作为生成素材复制。
- 默认只给生成模型 2～4 张 1688 证据图，减少处理时间；完整原图保留在源目录。
- `done.flag` 只能由工作台在验证 4 张成品后写入，不能把模型声称完成当作完成。
- 正式成品必须存在 `manifest.json`，其中记录 `provider: LocalProductComposite`、商品抠图哈希、四张成品路径与哈希；任何文件被替换后必须停止。
- 旧成品只能移到 `history/`，不能与新运行混用。
- 审核模型未配置时，只有本地真实合成守卫完全通过才可继续；普通 AI 生图不得回退为自动通过。
- 最终商品发布和笔记发布必须由用户确认。
- v2 新任务在定价和文案生成后停在“价格与文案确认”；售价写入
  `04_千帆填写清单/定价.json` 和 `listing.json`，不自动写进正文。
- 千帆使用独立 Edge Profile 和端口 `9333`，只自动填写到最终提交前，禁止自动点发布。
- 推广笔记草稿默认关闭；启用后也只使用 `auto_publish=false`，不阻塞商品流程。
- 遇到登录、验证码、账号风控、事实冲突、商品图严重失真或平台警告时暂停该商品，继续处理队列中其他可处理商品。
- API 边际成本默认硬上限 1 元/商品，Antigravity 固定订阅不计入；超限必须暂停。
- Gemini/Qwen Key 使用 Windows DPAPI CurrentUser 加密，禁止写入日志、商品 JSON 或前端状态。
- 模块工作流采用“模块库 + 工作流模板 + 商品运行快照”三层结构；模板可自由改线，
  但循环、端口不匹配、缺少输入和绕过发布审核会被拒绝。
- 修改只影响下一轮。已经开始的商品使用不可变模板快照，避免半途更换执行器。
- 独立站调研只保存来源 URL 和提炼后的摄影语言，不下载或复用对方商品图。
- 电商出图优先复用已安装的 `xiaohongshu-cover`、`lifestyle-scene`、`multi-angle-set`、`selling-point-infographic`、`batch-background-swap` 和 `product-shots-*`；提示词灵感可查 `awesome-ai-image-prompts`。
- 第三方电商 skill 只负责策划、商品锁定和提示词；本机实际渲染优先使用 `$antigravity-image-backend` 或工作台现有 Antigravity 节点，禁止静默切换到按张付费的图片 API。
- Google AI Pro/Ultra 是 Antigravity 平台额度，不是 Gemini API Key 额度，不能把两者混称为同一份 API 余额。

## 项目复用

- `ahao-doudian-pro` 仅复制定价算术、SKU 分层、标题信息密度和通用运营红线；不要把它里面的抖音后台路径套到小红书。
- CreatorHub 和 xhs_ai_publisher 只作为可选发布适配器，不能同时运行并争用同一个浏览器 Profile。
- `xhs_ai_publisher` 用于图文笔记草稿和人工确认发布，不用于千帆商品资料上架。发布器未登录时，先连接已开启 USB 调试的 Android 手机，再按需使用 `android-sms` skill 获取验证码。
- ComfyUI-QwenVL 适合图片反推提示词和视觉审核；只有用户明确需要本地批量生成时才启用。
- ComfyUI 已安装在 `D:\ComfyUI-AMD`，Python 3.13 + AMD ROCm 10，端口 8188。启动脚本位于 `scripts/start-comfyui.ps1`。

## ComfyUI 主画布与本地 MCP

- 默认工作界面是“左侧 ComfyUI、右侧 Codex”。控制台仍在后台管理队列、审批和发布，不能因为接入 ComfyUI 就删除业务控制面。
- ComfyUI 自带 Agent 的本地版尚未正式发布；当前 Codex 使用名为 `comfy-local` 的本地 stdio MCP 调用 ComfyUI。
- MCP 的隔离环境位于工作台 `tools/comfy-mcp-venv`，工作区固定为 `D:\ComfyUI-AMD`，服务地址为 `http://127.0.0.1:8188`。
- 只允许调用状态查询、验证/运行工作流、查看任务、上传输入、等待和收集输出。不得通过 MCP 安装节点、更新或切换 ComfyUI、下载/删除模型、连接 Comfy Cloud 或调用付费 partner 生成。
- 标准顺序是 `server_info → validate_workflow → run_workflow → job(wait) → fetch_outputs`。失败时报告缺失节点或模型；不要自行下载补齐。
- ComfyUI 主审核画布预选 `Qwen3VL-8B-Instruct-Q4_K_M`，`max_tokens=2048`；正式工作台审核仍用远程 `qwen3-vl-plus`。首次运行本地模型需要用户明确同意下载。
- ComfyUI 输出统一写入 `workspace/jobs/<商品编号>/05_ComfyUI实验`，不能直接覆盖 `02_Antigravity成品`。
- 正式成品默认仍由 Antigravity 生成。用户一次选中 4 张 ComfyUI 实验图后，工作台统一转为 1080×1440，旧成品归档到 `history`，然后从 Qwen 审核重新推进。
- 左右窗口启动脚本：`scripts/start-comfy-workspace.ps1`。

详细工具位置、端口和启用顺序见 [references/tools.md](references/tools.md)。
