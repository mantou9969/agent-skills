---
name: android-sms
description: Read and send SMS on a USB-connected Android phone through adb. Use when the user asks to read phone text messages, grab a login/verification code without forwarding anything to the cloud, wait for an incoming code, export the inbox, or send a text message from the phone. Works offline over USB; no app install required.
---

# 手机短信（adb 直连）

## 这是什么

用 USB 连着的安卓手机收发短信，不装 App、不过云、不需要局域网。读取默认只读；只有显式用 `send` 才会发出去。

## 前置条件

- Windows 用 Git Bash 跑脚本（macOS/Linux 直接 bash 即可）
- 手机：设置 → 关于手机 → 连点版本号开开发者选项 → 打开「USB 调试」→ 插线 → 手机上点「允许」
- adb：脚本会自动找 PATH、`~/Downloads/platform-tools*`、`C:/Android/platform-tools`；找不到就报错并给下载地址。也可以用 `ADB_SMS_ADB=/路径/adb` 指定

## 命令

在 skill 目录下执行 `bash scripts/sms.sh <命令>`：

| 命令 | 作用 | 示例输出 |
|---|---|---|
| `check` | 自检 adb / 设备 / 条数 / 最新一条 | `device: dcc157a1 (2211133C)` |
| `list [N]` | 最近 N 条（默认 20） | `2026-10-27 13:43:10  1068...  【阿里巴巴】...验证码323331` |
| `latest` | 最新 1 条 | 同上 |
| `code [关键词]` | 从最新短信提验证码，可限定发件方 | `323331` |
| `wait [秒]` | 等新短信（默认 120 秒） | 新短信全文 |
| `export [文件]` | 导出收件箱为 TSV | `.../sms-export-20261027-135000.tsv` |
| `send 号码 正文` | 发一条短信 | `SENT: 15397926659（96 字，界面上已送达）` |
| `send 号码 -f 文件` | 正文从文件读 | 同上 |

输出统一是 `时间 <TAB> 号码 <TAB> 内容`，方便直接切列。

## 典型用法

用户说「看下手机收到的验证码」：

```bash
bash scripts/sms.sh code 阿里巴巴
```

用户说「等下有个码，你盯着」：

```bash
bash scripts/sms.sh wait 180
```

用户说「把这周收到的验证码都列出来」：

```bash
bash scripts/sms.sh list 50
```

## 发短信：先问一句，再写人话

1. **发之前必须让用户确认**收件人和内容，尤其是发给陌生人或商家。
2. 手机要解锁才能点发送；锁屏时脚本会报「找不到发送按钮」，提示用户解锁即可。
3. 写正文要像人：

| 别这样 | 这样 |
|---|---|
| `您好，兹就有以下五点向贵司咨询：1.…2.…3.…` | `老板你好，我在合肥做抖店，看到你家这款想拿几只测一下。想问下代发多少钱、能不能走抖音面单，运费到合肥怎么算？` |
| 一次问 8 个问题 | 一次问 2–3 个，其他的等对方回了再补 |
| 满屏书面语 | 短句、口语、有称呼，像微信里打出来的话 |

示例：

```bash
bash scripts/sms.sh send 15397926659 "老板你好，我在合肥做抖店的，刷到你家那款脆皮捏捏，想先拿五六只自己拍视频测一下。想问下一件代发多少钱、能不能走抖音面单，还有发到合肥运费怎么算？破损的话你们怎么补呀。方便回我一下，谢谢。"
```

## 常见故障

| 现象 | 原因 | 处理 |
|---|---|---|
| `没找到 adb` | PATH 里没有 | 装 Platform-Tools，或 `ADB_SMS_ADB=...` |
| `手机没连上` | 没开 USB 调试 / 没点允许 / 线只充电 | 重新插线，手机上确认弹窗 |
| `找不到发送按钮` | 锁屏、或权限弹窗挡住 | 解锁手机后再跑 |
| 显示已送达但 `content://sms/sent` 里没有 | 小米等机型把短信走 5G 消息（RCS），不写短信库 | 正常，脚本以界面「送达」为准 |
| 中文乱码 | 终端不是 UTF-8 | Git Bash 默认正常；PowerShell 先 `chcp 65001` |
| 读不到短信 | 系统限制或没有短信应用数据 | 兜底：`adb shell dumpsys notification --noredact` 看通知内容 |

## 注意

- 短信里有验证码、银行通知、私人对话。只在用户自己的机器上用，不要贴到公开的地方。
- 脚本不联网、不上传、不删除任何短信。
