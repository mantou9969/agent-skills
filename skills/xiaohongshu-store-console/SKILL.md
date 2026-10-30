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
→ 本地画风照片或小红书参考图
→ Gemini 结构化画风卡
→ 提示词确认门
→ Antigravity 商品一致性与修图
→ CDP 成品收集
→ Qwen 事实审核 + 本地一致性硬检查
→ 文案生成
→ 发布确认门
→ 千帆资料填写
→ 人工确认发布
```

每一步必须有磁盘证据。状态不能代替产物：`stage=1` 不代表 Antigravity 已送达，
必须存在发送时间；`stage=2` 必须有成品图片和 `done.flag`。

## 工作规则

- 用户是个人店，不声称商品 API 可以授权自建应用；上架使用正常网页操作或受支持的搬家工具。
- 优先使用用户已安装的 1688 Smart Scraper，不重复抓取；插件导出的 XLSX/Markdown 是输入契约。
- 小红书参考图只用于抽象构图、光线、颜色、镜头、道具和氛围，不复制专属文案、其他商品或品牌标识。
- 一个博主只提取一次画风卡并缓存。生成时让同一个模型同时读取商品图和画风卡。
- 默认只给生成模型 2～4 张 1688 证据图，减少处理时间；完整原图保留在源目录。
- `done.flag` 只能由工作台在验证 4 张成品后写入，不能把模型声称完成当作完成。
- 生成图必须存在磁盘文件、有效尺寸和 `manifest.json`；旧成品只能移到 `history/`，不能与新运行混用。
- 千问或规则审核未通过时停止下游，保留问题和修改意见，不自动发布。
- 最终商品发布和笔记发布必须由用户确认。
- 遇到登录、验证码、账号风控、事实冲突、商品图严重失真或平台警告时暂停该商品，继续处理队列中其他可处理商品。
- API 边际成本默认硬上限 1 元/商品，Antigravity 固定订阅不计入；超限必须暂停。
- Gemini/Qwen Key 使用 Windows DPAPI CurrentUser 加密，禁止写入日志、商品 JSON 或前端状态。
- 节点画布由 React Flow 呈现，执行顺序必须来自磁盘 DAG；第一版不开放任意拖线改生产顺序。
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
