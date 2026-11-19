---
name: xhs-douyin-crosspost
description: 一条链接进，YouTube Shorts / Instagram Reels 成品出。抓取小红书·抖音链接（或本地成片）→ 转 1080x1920 竖版 → 写英文标题简介话题 → 每天定点备好三条待审 → 人点头后发布，发布前自动卡版权、时长、文案。Use when 用户说「把这条小红书/抖音搬到 YouTube/Ins」「贴个链接发到油管」「每天固定发三条视频」「一键盘点发布」，或要把自己作品同步到海外平台。
metadata:
  trigger: 小红书/抖音 → YouTube/Instagram 搬运与每日三条
  data_home: "%USERPROFILE%\\crosspost"
---

# 小红书/抖音 → YouTube/Instagram 搬运线

一条链接进来，出去的是能直接上传的竖版成片 + 英文文案 + 当天三条的待审单。
**发布这一步永远要人点头**；下载要来源站的登录态；这两件都不是 agent 能替的。

## 三条不能破的规矩

1. **只搬本人的作品，或本人明确说已授权的。** 别人的笔记/视频（比如素材库里当参考的博主）只做参考，不进发布队列。`publish.json` 的 `rights.is_own_work` 不为 `true`，`publish` 会直接拦下。
2. **不代替人登录、不替人点头。** cookies.txt 由本人导出；`approve --by` 只写本人。agent 自己跑 `approve` 等于伪造同意，禁止。
3. **不编造。** 英文文案里的事实只能来自 `source.json`（原标题、简介、作者）；产地、材质、价格、功效、认证没写就不写。

## 先体检，再决定能做到哪一步

```powershell
python scripts/xp.py doctor
```

体检会逐项说清：工具、四个站的网络、cookies、两个平台的授权。对照着看：

| 结果 | 含义 | 还能做什么 |
|---|---|---|
| 抖音/小红书 网络不通 | 抓不了链接 | 只处理本地成片（`ingest <文件路径>`） |
| 登录 cookie 不行 | 抓链接会被来源站挡 | 让本人导出 cookies.txt（见下） |
| YouTube/Ins 网络不通 | 发不出去 | 成片、文案、待审单照做；通网后再发 |
| 平台授权没配 | 不能代发 | 出成品，本人手动上传 |

**这些是"要本人处理"的阻塞，不要重试硬闯，也不要换别的路子绕。**

### 本人一次性要做的事

- **cookies**：浏览器装「Get cookies.txt LOCALLY」这类扩展 → 登录抖音/小红书 → 导出 `cookies.txt` → 放到 `%USERPROFILE%\crosspost\secrets\cookies.txt`，把路径填进 `config.json` 的 `cookies_file`。
- **网络**：这台机器直连不到 YouTube/Instagram，得本人开代理（agent 不配置、不接管代理）。
- **授权**：YouTube 要 OAuth 的 client_id/secret/refresh_token；Instagram 要长期 token + 公网可访问的成片地址。没配就只能手动上传。

## 每天怎么跑

```powershell
# 0. 体能（每次新环境先跑一次）
python scripts/xp.py doctor

# 1. 收料：链接或本地成片都行，重复的不再抓
python scripts/xp.py ingest "https://v.douyin.com/xxxx/"
python scripts/xp.py ingest "D:\导出\今天这条.mp4"

# 2. 转成片：1080x1920 / h264 / aac / faststart，横屏自动模糊铺底，出封面和待审单
python scripts/xp.py prepare douyin-7xxxxxxxxxxxxxx

# 3. 写英文文案（agent 的活，见下一节），写进 publish.json 的 copy
# 4. 定今天三条（同一天重跑结果一样，不会重复）
python scripts/xp.py daily --count 3

# 5. 人看 batches/<日期>.md → 点头 → 记录 → 发（默认只演练）
python scripts/xp.py approve 2026-11-20 --by 本人
python scripts/xp.py publish 2026-11-20 --target youtube            # 演练
python scripts/xp.py publish 2026-11-20 --target youtube --do-upload  # 真发
```

### 第 3 步：agent 怎么写文案

打开 `items/<id>/publish.json`，填 `copy`：

- `title_en`：≤ 90 字符，说清"是什么 + 给谁看"，别堆形容词。
- `description_en`：3 句内。第一句是什么、第二句卖点/工艺、第三句可放中文原名方便本人对号。结尾可放话题。
- `hashtags`：3–8 个英文标签，和内容对得上，不加无关热标签。
- `title_zh` / `description_zh` 保留原文，不要覆盖。

写不出事实就别写满：留空比编造好，`publish` 会因为有空格子拦下来。

## 数据结构（都在 `%USERPROFILE%\crosspost`）

```
items/<平台>-<id>/
  source.json     原标题、简介、作者、原链接、原始文件
  media/          原片
  out/            youtube.mp4 / instagram.mp4 / cover.jpg
  publish.json    成片清单 + 文案槽 + 版权标记
  review.md       给人看的待审单
  state.json      ingested → prepared → queued → approved → published
batches/<日期>.json|.md   当天三条 + 凭证
config.json       本机配置（cookies 路径、平台授权、每日条数）
```

## 每天定点备料

```powershell
pwsh -File scripts/register-daily-task.ps1 -Time 20:00 -Count 3 -DryRun   # 先看
pwsh -File scripts/register-daily-task.ps1 -Time 20:00 -Count 3           # 注册
pwsh -File scripts/register-daily-task.ps1 -Remove                        # 取消
```

计划任务**只备料**（转码 + 出待审单），不发。要每天固定发三条，路径是：定时备好 → 本人一次点头 → 批量发；或本人给 YouTube 授权后改成 `--do-upload` 的流水线，仍然每条过版权与文案检查。

## 卡住时看这里

| 现象 | 原因 | 怎么办 |
|---|---|---|
| `Fresh cookies … needed` | 来源站要登录态 | 本人导出 cookies.txt，别反复重试 |
| `Could not copy/decrypt cookie database` | 浏览器正开着锁了库，或系统加密换了密钥 | 别去破解；让本人导出 cookies.txt |
| `连不上 youtube` | 没有到该站的网络 | 本人开代理；成片和文案都已备好，通网重跑同一条命令 |
| `超长 8.0s > 上限 5s` | 超过平台时长上限 | 改 `config.json` 的 `limits`，或先裁再重新 `prepare` |
| `版权没确认是本人作品` | `rights.is_own_work` 不是 true | 本人确认后改成 `true`；不是本人作品就别发 |
| `这批还没点头` | 没 `approve` 或重排了批次 | 让本人看 `batches/<日期>.md` 再点头 |
| `凭证对不上` | 批次在点头后被改过 | 重新 `daily --force` 核对，再点头 |

## 和素材库的关系

飞书素材库（`LNx5bioGCaksAYsQvFKcDQYkndf` / `tblUsFxFA8I2nGc5`）里收的是**参考**：别人的博主、别人的笔记、淘宝店。
那批东西的任务是"看完能抄什么"，不是"搬去发"。搬运线只吃本人作品或已授权内容——两边不要混。
从素材里真正做出来的自己那条，才 `ingest` 进这条线。
