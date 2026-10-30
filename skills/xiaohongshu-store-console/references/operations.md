# 长任务操作

## 启动

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\21878\.codex\skills\xiaohongshu-store-console\scripts\start_workbench.ps1"
```

脚本会在端口 `4173` 未占用时后台启动控制台。`npm start` 会先构建 React Flow 前端，再启动 Node 服务。关闭聊天或浏览器不会停止服务。

需要防止 Node 进程意外退出时，再启动守护：

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\21878\.codex\skills\xiaohongshu-store-console\scripts\supervise-workbench.ps1"
```

停止守护：

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\21878\.codex\skills\xiaohongshu-store-console\scripts\stop-supervisor.ps1"
```

## 查看状态

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\21878\.codex\skills\xiaohongshu-store-console\scripts\status.ps1"
```

关注以下字段：

- `runner.enabled=true`：后台队列已启动。
- `runner.message`：当前正在发送、生成还是等待审核。
- `/api/workflows/<jobId>.status`：DAG 当前状态。
- `/api/workflows/<jobId>.currentGate`：等待人工确认的节点。
- 每个节点的 `status/startedAt/finishedAt/durationMs/costCny/artifacts`：执行证据。
- `02_Antigravity成品/done.flag`：Antigravity 的完成标记。

## 暂停与恢复

在网页顶部点击“后台运行中”可暂停；再次点击可恢复。暂停只影响后续队列，
不会删除已生成文件。

工作流操作：

- `continue`：继续 `waiting_user` 节点。
- `retry`：重试失败或配置缺失节点。
- `restart`：保留磁盘产物，建立一轮新的 DAG。
- `cancel`：取消本轮 DAG。
- `publish-complete`：人工确认发布准备完成。

## 夜间运行边界

可以连续处理多个商品，但以下情况应停在原任务，不应自动跳过：

- 登录态失效或出现验证码；
- 1688 价格、规格和页面商品不一致；
- Antigravity 超时或没有 `done.flag`；
- Antigravity CDP 没有找到 4 张有效成品；
- API 边际成本达到 1 元/商品；
- 商品主体、颜色或数量生成错误；
- 审核不通过；
- 千帆最终发布。

电脑必须保持供电且不休眠。需要时运行：

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\21878\.codex\skills\xiaohongshu-store-console\scripts\keep-awake.ps1"
```

该脚本只阻止系统因空闲休眠；关闭 PowerShell 窗口或按 `Ctrl+C` 即解除。

## ComfyUI 主画布

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\21878\Desktop\每天进度\codex\scripts\start-comfy-workspace.ps1"
```

左侧 ComfyUI、右侧 Codex。工作台在后台继续处理队列，只有提示词确认、审核退回、
发布确认和异常恢复需要打开。

Codex 使用 `comfy-local` MCP。输出先进入商品的 `05_ComfyUI实验`，不能直接覆盖正式
成品。工作台一次采用 4 张实验图后会归档旧成品，并从 Qwen 审核重新运行。
