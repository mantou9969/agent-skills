# DSH 瘦身记录（2026-11-19）

依据：`C:\Users\21878\.dsh\sessions` 下 170 个会话（2026-10-16 → 2026-11-19）的真实调用统计。
用户工作重心：`pwsh` 10717 次（占 60%+），围绕飞书桥、微信 chatlog、ADB 手机、小红书素材与图片识别。
技能加载共 34 次、只命中 13 个技能 —— 其余 40 个零加载。

## 一、关闭的技能（26 个）

### A. 官方 CLI undeploy（15 个，可一键装回）
| 技能 | 30 天加载 | 关闭理由 |
|---|---|---|
| anything2explainer | 0 | 代码动画科普视频，描述 188 tokens |
| beatra-ai-video-studio | 0 | 144 tokens，视频生成平台 |
| book-sales-video | 0 | 图书带货视频，与业务无关 |
| huashu-art-motion | 0 | 61 tokens，艺术动画 |
| lemo-opuscar | 0 | 266 tokens，风格化短片 |
| make-a-video | 0 | 114 tokens，HyperFrames 入门 |
| manim-video | 0 | 114 tokens，数学动画 |
| video-shotcraft | 0 | 187 tokens，分镜产品视频 |
| video-use | 0 | 82 tokens，对话式剪辑 |
| wtt-code-animation-studio | 0 | 114 tokens，前端代码动画 |
| xilo-opus-video | 0 | 294 tokens（全库最贵），代码生成视频 |
| xhs-douyin-crosspost | 0 | 103 tokens，小红书→YouTube 搬运 |
| personal-brand | 0 | 127 tokens，个人 IP 顾问，非账号运营 |
| guizang-social-card-skill | 0 | 154 tokens，社交卡片图 |
| ecommerce-listing-suite | 0 | 99 tokens，多平台套图编排 |

### B. 从 `C:\Users\21878\.agents\skills` 物理移出（11 个）
该目录是 DSH 的 skill 加载根之一（`skill-filesystem` 的 agentsHome），但其中多为 claude_code / gemini_cli 的部署，CLI 管不到，只能移走。全部存放在 `C:\Users\21878\.dsh\backups\skills-disabled\<时间戳>\agents\`，未删除。

| 技能 | 加载 | 说明 |
|---|---|---|
| figma | 0 | 74 tokens，HyperFrames 取 Figma 设计 |
| archify | 0 | 188 tokens，架构图 |
| shopify | 0 | 256 tokens，Shopify 全栈 |
| linkpix-ad-film | 0 | 85 tokens，广告片 |
| linkpix-ecom-video | 0 | 114 tokens，电商视频 |
| linkpix-sales-video | 0 | 83 tokens，带货视频 |
| linkpix-douyin-viral-video | 0 | 236 tokens，抖音爆款视频 |
| slideshow | 0 | 70 tokens，演示 deck |
| remotion-to-hyperframes | 0 | 80 tokens，Remotion 迁移 |
| agent-reach | 16（保留 .dsh 副本） | 与 `~/.dsh/skills/agent-reach` 重复，双份计费 |
| android-sms | 1（保留 .dsh 副本） | 与 `~/.dsh/skills/android-sms` 重复 |

## 二、关闭的插件（5 行，20 个工具定义）

写入 profile 层 `C:\Users\21878\.dsh\profiles\desktop\cordis.patch.yml`，需重启 DSH 生效。

| 行 id | 工具 | 30 天调用 | 理由 |
|---|---|---|---|
| dsh-mineru | 6 个 `mineru_*` | 0 | 文档解析从未使用，`office` / `read` 已覆盖 |
| dsh-time-machine | 6 个 `time_machine_*` | 0 | 工作区快照未用，已有 git + 本机备份习惯 |
| dsh-ops-bundle | 7 个 `dsh_ops_sandbox_*` | 2 | 7 个工具描述只换来 2 次调用 |
| tool-workflow | `workflow`（超大 schema） | 0 | 并行度需求 ≤4，`subagent` / `agent-team` 够用 |
| workflow-ptc | 同上运行时 | 0 | 与 workflow 同源，一并禁用 |

## 三、明确保留（防误关）

| 能力 | 30 天用量 | 理由 |
|---|---|---|
| dsh-computer-use-win | ≈850 | 主力操作面（截图/点击/键位/UIA） |
| dsh-nuphus-mcp | ≈300 | 浏览器自动化 |
| billion-context (acp) | ≈330 | 上下文压缩，本次瘦身靠它 |
| agent-team / subagent | 37 | 多 agent 协作在用 |
| schedule | 6 次 + 23KB 排程 | 飞书守夜自动化 |
| cordis_inspect | 30 | 插件/UI 排查 |
| purge | 身份与权限框架 | 不动 |
| modlens | 13 | 子代理 free-model 路由依赖 |
| office 全家（7 个） | 139 tokens | 真出过 docx/pptx，成本极低 |
| screenshot | 19 | 56 tokens |
| xiaohongshu-* / xhs-visual-director | 主业 | 不关 |
| hyperframes + registry + cli | 1 | 唯一跑通的视频链 |
| video-to-note | 1 | 视频转笔记 |

## 四、成本变化

- 技能清单：≈5,410 → ≈1,820 tokens/请求（省 ≈3,590，已热生效）。
- 插件工具定义：20 个 ≈3,500 tokens/请求（重启后生效）。
- 合计 ≈7,000 tokens/请求。

## 五、恢复方式

```powershell
# 装回被 undeploy 的技能
& C:\Users\21878\.skills-manager\bin\skills-manager-cli.exe skills deploy <技能名> --agent deepseek_harness

# 搬回 .agents 下的 11 个目录（实际备份路径）
Copy-Item "C:\Users\21878\.dsh\backups\skills-disabled\20261119-193308\agents\*" "C:\Users\21878\.agents\skills\" -Recurse

# 撤销插件禁用
Copy-Item "C:\Users\21878\.dsh\profiles\desktop\cordis.patch.yml.bak-tokenslim-20261119-193252" `
          "C:\Users\21878\.dsh\profiles\desktop\cordis.patch.yml" -Force
```
