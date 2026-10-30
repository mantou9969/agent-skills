# Agent Skills Cloud Library

这是用户在 Windows 上通过 Skills Manager 维护的中央 Skill 库的 Git 备份。

## 结构

- 每个顶层目录是一个可直接识别的 Skill，目录内包含 `SKILL.md`。
- `.skills-manager/` 保存 Skills Manager 使用的来源、Preset 和 Skill 元数据。
- `MANIFEST.csv` 保存本次云端快照中的 Skill 清单和文件数量。
- `snapshot-212-20261030` 标签保留旧版 212 个 Skill 的去重快照。

## 使用方式

Skills Manager 平时读取本机中央库，不依赖每次联网。Git 云端仓库用于备份、跨设备恢复和版本历史。修改 Skill 后，应通过 Skills Manager 的“Git 同步”提交并推送。

## 安全与许可

发布前已排除运行时缓存、虚拟环境、依赖目录和疑似密钥文件。`media-use` 的云端副本不包含硬编码遥测凭据；如确实需要遥测，请在运行环境设置 `MEDIA_USE_POSTHOG_API_KEY`，未设置时不会发送遥测。第三方 Skill 的许可与署名归各自作者所有；本仓库不对第三方内容重新授权。使用前请查看各 Skill 自带的 `LICENSE`、来源和使用说明。
