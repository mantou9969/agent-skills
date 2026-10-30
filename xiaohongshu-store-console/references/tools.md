# 工具与职责

## 核心控制台

- 路径：`C:\Users\21878\Desktop\每天进度\codex`
- 启动：`npm start`
- 地址：`http://127.0.0.1:4173`
- 数据：`workspace/state.json`
- 商品目录：`workspace/jobs/<商品ID>/`

## 1688 采集

首选 1688-Smart-Scraper：

`C:\Users\21878\Desktop\qoder推荐工作流\1688-Smart-Scraper`

它的定位是人工浏览、筛选、改价和导出，不绕过平台风控。XLSX 中的商品图是嵌入图，
Markdown 导出保留图片链接。控制台接入时优先增加 XLSX 导入器，从工作簿读取行和
`xl/media` 图片，不再重复请求 1688。

## 生成与视觉理解

- Antigravity：通过 OpenCLI 发送任务，自动识别其调试端口。适合直接生成和修图。
- ComfyUI-QwenVL：已安装到
  `D:\ComfyUI-AMD\custom_nodes\ComfyUI-QwenVL`，服务地址
  `http://127.0.0.1:8188`。启动脚本为
  `C:\Users\21878\Desktop\每天进度\codex\scripts\start-comfyui.ps1`。
- Comfy 本地 MCP：隔离环境为
  `C:\Users\21878\Desktop\每天进度\codex\tools\comfy-mcp-venv`，Codex 服务名
  `comfy-local`，comfy-cli workspace 固定为 `D:\ComfyUI-AMD`。
- ComfyUI_QwenVL_PromptCaption：源码已安装到
  `C:\Users\21878\Desktop\每天进度\codex\integrations\ComfyUI_QwenVL_PromptCaption`，
  适合文件夹批量图片反推。
- Comfy-Org/workflow_templates：已安装到
  `C:\Users\21878\Desktop\每天进度\codex\integrations\workflow_templates_code`，
  提供 Qwen Image Edit、Nano Banana 和 Flux 的可导入模板。

本机是 Windows 11 + AMD RX 6800 XT。ComfyUI 已使用 Python 3.13、
PyTorch 2.13 ROCm 10 安装到 `D:\ComfyUI-AMD`，已识别 16368 MB VRAM，
`AILab_QwenVL`、`AILab_QwenVL_Advanced` 和 GGUF 节点已加载。
首批没有下载大型模型，模型必须由用户按需选择。

## ComfyUI 主画布

- 启动：`scripts\start-comfy-workspace.ps1`
- 默认布局：左侧 ComfyUI，右侧 Codex；工作台后台继续运行。
- 主工作流：`后现代马铃薯-QwenVL视觉审核`
- 实验输出：`workspace/jobs/<商品ID>/05_ComfyUI实验`
- 采用规则：一次恰好 4 张，统一 1080×1440，旧成品归档并从 Qwen 审核重新开始。
- 本地 MCP 只开放查询、验证、运行、等待和收图；安装、更新、下载模型和云生成不开放。

## 可选发布工具

- CreatorHub：功能完整，适合多平台下载、监控和发布，但会独占一个浏览器 Profile。
- xhs_ai_publisher：适合小红书稿件、封面模板和发布，但与 CreatorHub 功能重叠。

两者不要同时启动，也不要让它们和工作台共用同一个登录 Profile。

CreatorHub 已安装到
`C:\Users\21878\Desktop\每天进度\codex\integrations\creatorhub`，Python
依赖、Node 依赖、Patchright Chromium 和自检均已完成。

xhs_ai_publisher 已安装到
`C:\Users\21878\Desktop\每天进度\codex\integrations\xhs_ai_publisher`，Web
依赖和 Playwright Chromium 已完成，Web 应用可以导入。

CreatorHub 启动：

```powershell
cmd /c start.cmd --no-open --port 8200
```

xhs_ai_publisher Web 启动：

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.web.app:app --host 127.0.0.1 --port 8100
```

两个服务不要同时占用同一账号的浏览器登录态。

## 长任务运行

长任务由本地 Node 服务中的队列执行，不依赖 Codex 聊天窗口。Agents SDK 可以替换
队列内部的模型调度，但必须由同一个常驻服务启动；只安装 SDK 本身不会产生后台进程。

## DAG 与模型

- 工作流文件：`workspace/workflows/<jobId>.json`
- 画风卡缓存：`workspace/cache/style-cards`
- 模型默认：Gemini `gemini-3.1-pro-preview`，Qwen `qwen3-vl-plus`
- API Key：Windows DPAPI CurrentUser 加密，文件为 `workspace/settings/secrets.json`
- 单商品外部 API 成本上限：1 元；Antigravity 订阅不计入
