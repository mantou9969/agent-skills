#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xp.py — 一张链接进，YouTube / Instagram 成品出。

子命令：
  doctor            体检：工具、网络、登录/cookie、授权，逐项说清能不能跑
  ingest  <链接|文件> 抓取（或收下本地文件）到 items/<id>/，去重
  prepare <item>    转成平台规格（1080x1920 / h264 / aac / faststart）+ 封面 + 待填文案槽
  status            列出队列里每条素材到哪一步了
  daily             选出今天要发的 N 条（默认 3），生成待审包和当天凭证
  approve <batch>   记录"人已点头"（只有本人同意后才执行）
  publish <batch>   发布。默认只演练；真发要 --do-upload 且已 approve

退出码：0 成功 / 2 用法错 / 3 要本人处理（登录、cookie、网络）/ 4 未配置授权
数据目录：$env:CROSSPOST_HOME，默认 %USERPROFILE%\\crosspost
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import urllib.parse
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

EXIT_OK, EXIT_USAGE, EXIT_PERSON, EXIT_CONFIG = 0, 2, 3, 4

PLATFORMS = {
    "douyin": ("抖音", ("douyin.com", "iesdouyin.com")),
    "xiaohongshu": ("小红书", ("xiaohongshu.com", "xhslink.com")),
    "youtube": ("YouTube", ("youtube.com", "youtu.be")),
    "instagram": ("Instagram", ("instagram.com", "instagr.am")),
}

DEFAULT_CONFIG = {
    "cookies_file": "",
    "cookies_from_browser": "",
    "encoding": {"width": 1080, "height": 1920, "fps": 30, "video_bitrate": "8M", "audio_bitrate": "128k"},
    "limits": {"youtube": 180, "instagram": 180},
    "daily": {"count": 3, "time": "20:00", "approval": "review_first"},
    "targets": {"youtube": {"channel": "", "privacy": "private"}, "instagram": {"username": ""}},
    "youtube_api": {"client_id": "", "client_secret": "", "refresh_token": ""},
    "instagram_api": {"access_token": "", "ig_user_id": "", "video_url": ""},
}


# ---------------------------------------------------------------- 基础设施
def home() -> Path:
    root = Path(os.environ.get("CROSSPOST_HOME") or (Path.home() / "crosspost"))
    for sub in ("items", "batches", "logs", "secrets"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


def load_config() -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    path = home() / "config.json"
    if path.exists():
        user = json.loads(path.read_text(encoding="utf-8-sig"))
        for k, v in user.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    return cfg


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run(cmd: list[str], timeout: int = 900) -> tuple[int, str]:
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout, env=env)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def which(name: str) -> str | None:
    return shutil.which(name)


def probe(path: Path) -> dict:
    ffprobe = which("ffprobe") or "ffprobe"
    code, out = run([ffprobe, "-v", "error", "-print_format", "json",
                     "-show_format", "-show_streams", str(path)], timeout=60)
    if code != 0:
        raise RuntimeError(f"ffprobe 读不了 {path.name}：{out.strip()[:300]}")
    data = json.loads(out[out.index("{"):])
    v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    dur = float(data.get("format", {}).get("duration") or v.get("duration") or 0)
    return {
        "duration": round(dur, 3),
        "width": int(v.get("width") or 0),
        "height": int(v.get("height") or 0),
        "vcodec": v.get("codec_name"),
        "acodec": (a or {}).get("codec_name"),
        "has_audio": bool(a),
        "size": int(data.get("format", {}).get("size") or path.stat().st_size),
    }


def detect_platform(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    for key, (_, hosts) in PLATFORMS.items():
        if any(h in host for h in hosts):
            return key
    return "local"


def slug(text: str) -> str:
    keep = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text.strip())
    return keep.strip("-")[:60] or "item"


def tcp_ok(host: str, port: int = 443, timeout: float = 6.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def die(code: int, msg: str) -> None:
    print(msg)
    sys.exit(code)


# ---------------------------------------------------------------- doctor
def cmd_doctor(args) -> int:
    cfg = load_config()
    rows, blockers = [], []

    def add(name, ok, detail):
        rows.append((name, "能跑" if ok else "不行", detail))
        if not ok:
            blockers.append(f"{name}：{detail}")

    add("ffmpeg", bool(which("ffmpeg")), which("ffmpeg") or "没装 ffmpeg，转码做不了")
    add("ffprobe", bool(which("ffprobe")), which("ffprobe") or "没装 ffprobe，读不了视频参数")
    add("yt-dlp", bool(which("yt-dlp")), which("yt-dlp") or "没装 yt-dlp，链接抓不了")
    try:
        import PIL  # noqa: F401
        add("Pillow", True, f"版本 {PIL.__version__}")
    except Exception:
        add("Pillow", False, "没装 Pillow，封面做不了（pip install pillow）")

    cookie_note = "未配置"
    if cfg.get("cookies_file") and Path(cfg["cookies_file"]).exists():
        add("登录 cookie", True, f"cookies 文件在：{cfg['cookies_file']}")
        cookie_note = "cookies 文件"
    elif cfg.get("cookies_from_browser"):
        add("登录 cookie", True, f"读浏览器：{cfg['cookies_from_browser']}")
        cookie_note = "浏览器 cookie"
    else:
        add("登录 cookie", False,
            "抖音/小红书下载要登录态的 cookies（没配置）。用浏览器扩展导出 cookies.txt 后填进 config.json 的 cookies_file")

    net = {
        "抖音": tcp_ok("www.douyin.com"),
        "小红书": tcp_ok("www.xiaohongshu.com"),
        "YouTube": tcp_ok("www.youtube.com"),
        "Instagram": tcp_ok("www.instagram.com"),
    }
    for host, ok in net.items():
        add(f"网络·{host}", ok, "能连" if ok else "连不上（这台机器到不了，发布/下载都会卡）")

    yt_ready = all(cfg["youtube_api"].get(k) for k in ("client_id", "client_secret", "refresh_token"))
    ig_ready = all(cfg["instagram_api"].get(k) for k in ("access_token", "ig_user_id", "video_url"))
    add("YouTube 授权", yt_ready, "已配" if yt_ready else "没配 OAuth（client_id/secret/refresh_token），只能出成品不能代发")
    add("Instagram 授权", ig_ready, "已配" if ig_ready else "没配 Graph API token / 公网视频地址，只能出成品不能代发")

    print("体检：")
    for name, status, detail in rows:
        print(f"  [{status}] {name} — {detail}")
    print(f"\n数据目录：{home()}")
    print(f"每日条数：{cfg['daily']['count']} 条，时间 {cfg['daily']['time']}，方式 {cfg['daily']['approval']}")
    if blockers:
        print("\n还差这些：")
        for b in blockers:
            print(f"  - {b}")
    else:
        print("\n全绿，可以整条跑通。")
    print(f"\n(cookies 现状：{cookie_note})")
    return EXIT_OK if not blockers else EXIT_PERSON


# ---------------------------------------------------------------- ingest
def ytdlp_args(cfg: dict) -> list[str]:
    args = []
    if cfg.get("cookies_file") and Path(cfg["cookies_file"]).exists():
        args += ["--cookies", cfg["cookies_file"]]
    elif cfg.get("cookies_from_browser"):
        args += ["--cookies-from-browser", cfg["cookies_from_browser"]]
    return args


def explain_download_error(text: str) -> tuple[int, str]:
    low = text.lower()
    if "cookies" in low or "login" in low or "sign in" in low:
        return EXIT_PERSON, ("抖音/小红书要登录态才能读这条。请在浏览器里登录后导出 cookies.txt，"
                             "填进 config.json 的 cookies_file，再重跑。")
    if "unsupported url" in low:
        return EXIT_USAGE, "这个链接 yt-dlp 不认。复制完整的分享链接（带 http）再试。"
    if any(k in low for k in ("timed out", "connection", "resolve", "network")):
        return EXIT_PERSON, "网络连不上来源站。检查网络/代理后再试。"
    return EXIT_USAGE, "下载失败：" + text.strip().splitlines()[-1][:300] if text.strip() else "下载失败"


def cmd_ingest(args) -> int:
    cfg = load_config()
    target = args.source
    is_url = bool(re.match(r"^https?://", target, re.I))
    item_root = home() / "items"

    if not is_url:
        src = Path(target).expanduser()
        if not src.exists():
            die(EXIT_USAGE, f"找不到文件：{src}")
        digest = hashlib.sha256(src.read_bytes()).hexdigest()[:12]
        item_id = f"local-{digest}"
        folder = item_root / item_id
        if folder.exists() and not args.force:
            print(f"已经有了：{item_id}（{folder}）")
            return EXIT_OK
        folder.mkdir(parents=True, exist_ok=True)
        media_dir = folder / "media"
        media_dir.mkdir(exist_ok=True)
        dst = media_dir / ("source" + src.suffix.lower())
        shutil.copy2(src, dst)
        info = probe(dst)
        write_json(folder / "source.json", {
            "item_id": item_id, "platform": "local", "platform_label": "本地文件",
            "url": "", "title": src.stem, "description": "", "uploader": "",
            "duration": info["duration"], "media": str(dst),
            "ingested_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
        })
        print(f"收下了：{item_id}\n  文件：{dst}\n  时长：{info['duration']}s  {info['width']}x{info['height']}")
        return EXIT_OK

    platform = detect_platform(target)
    if platform == "local":
        die(EXIT_USAGE, "这个网址看着不是小红书/抖音/YouTube/Instagram。要么贴分享链接，要么给本地文件。")

    yt = which("yt-dlp")
    if not yt:
        die(EXIT_PERSON, "没装 yt-dlp，链接抓不了。")
    meta_args = [yt, "--no-warnings", "--no-playlist", "--socket-timeout", "30",
                 "--dump-single-json", target] + ytdlp_args(cfg)
    code, out = run(meta_args, timeout=180)
    if code != 0:
        c, m = explain_download_error(out)
        die(c, m)
    try:
        meta = json.loads(out[out.index("{"):])
    except Exception:
        die(EXIT_USAGE, "读不出这条的元数据：" + out.strip()[:300])

    ext_id = str(meta.get("id") or hashlib.sha1(target.encode()).hexdigest()[:11])
    item_id = f"{platform}-{slug(ext_id)}"
    folder = item_root / item_id
    if folder.exists() and not args.force:
        print(f"已经有了：{item_id}（{folder}）\n  想重新抓就加 --force")
        return EXIT_OK
    folder.mkdir(parents=True, exist_ok=True)
    media_dir = folder / "media"
    media_dir.mkdir(exist_ok=True)

    dl_args = [yt, "--no-warnings", "--no-playlist", "--socket-timeout", "30",
               "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
               "--merge-output-format", "mp4",
               "-o", str(media_dir / "source.%(ext)s"),
               "--write-info-json", target] + ytdlp_args(cfg)
    code, out = run(dl_args, timeout=1800)
    if code != 0:
        c, m = explain_download_error(out)
        die(c, m)

    candidates = [p for p in media_dir.glob("source.*") if p.suffix.lower() in (".mp4", ".mkv", ".webm", ".mov")]
    if not candidates:
        die(EXIT_USAGE, "下载完成但没找到视频文件，检查链接是不是图文笔记。")
    media = candidates[0]
    info = probe(media)
    write_json(folder / "source.json", {
        "item_id": item_id, "platform": platform,
        "platform_label": PLATFORMS[platform][0], "url": target,
        "title": meta.get("title") or "",
        "description": meta.get("description") or "",
        "uploader": meta.get("uploader") or meta.get("channel") or "",
        "duration": info["duration"], "media": str(media),
        "ingested_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "webpage_url": meta.get("webpage_url") or target,
    })
    print(f"抓到了：{item_id}\n  标题：{(meta.get('title') or '')[:60]}\n  时长：{info['duration']}s  {info['width']}x{info['height']}\n  文件：{media}")
    return EXIT_OK


# ---------------------------------------------------------------- prepare
def cmd_prepare(args) -> int:
    cfg = load_config()
    folder = home() / "items" / args.item
    src_json = read_json(folder / "source.json")
    if not src_json:
        die(EXIT_USAGE, f"没有这条素材：{args.item}（先 ingest）")
    media = Path(src_json["media"])
    if not media.exists():
        die(EXIT_USAGE, f"原始文件不见了：{media}")

    ffmpeg, ffprobe = which("ffmpeg"), which("ffprobe")
    if not (ffmpeg and ffprobe):
        die(EXIT_PERSON, "没装 ffmpeg/ffprobe，转码做不了。")

    info = probe(media)
    enc = cfg["encoding"]
    W, H, FPS = enc["width"], enc["height"], enc["fps"]
    out_dir = folder / "out"
    out_dir.mkdir(exist_ok=True)

    portrait = info["height"] >= info["width"] * 1.05
    targets = {}
    for target in ("youtube", "instagram"):
        dest = out_dir / f"{target}.mp4"
        if portrait:
            # 竖屏：铺满并居中裁切
            vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
            cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(media),
                   "-vf", vf, "-map", "0:v:0"]
        else:
            # 横屏/方形：模糊铺底 + 原画居中
            fc = (f"split=2[bg][fg];"
                  f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                  f"gblur=sigma=28,eq=brightness=-0.06[bg2];"
                  f"[fg]scale={W}:-2[fg2];"
                  f"[bg2][fg2]overlay=(W-w)/2:(H-h)/2[v]")
            cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(media),
                   "-filter_complex", fc, "-map", "[v]"]
        if info["has_audio"]:
            cmd += ["-map", "0:a:0", "-c:a", "aac", "-b:a", enc["audio_bitrate"], "-ar", "48000", "-ac", "2"]
        cmd += ["-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-b:v", enc["video_bitrate"],
                "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart", str(dest)]
        code, out = run(cmd, timeout=3600)
        if code != 0:
            die(EXIT_USAGE, f"{target} 转码失败：{out.strip()[:400]}")
        checked = probe(dest)
        limit = int(cfg["limits"].get(target, 180))
        over = checked["duration"] > limit + 0.05
        targets[target] = {
            "file": str(dest), "duration": checked["duration"],
            "width": checked["width"], "height": checked["height"],
            "vcodec": checked["vcodec"], "acodec": checked["acodec"],
            "size_mb": round(checked["size"] / 1048576, 2),
            "limit_s": limit, "over_limit": over,
            "status": "needs_trim" if over else "prepared",
        }

    cover = out_dir / "cover.jpg"
    shot_at = min(1.0, max(0.1, info["duration"] / 10))
    run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{shot_at:.2f}", "-i", str(media),
         "-frames:v", "1", "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
         "-q:v", "3", str(cover)], timeout=300)

    publish = {
        "item_id": src_json["item_id"],
        "source": {k: src_json.get(k) for k in ("platform", "platform_label", "url", "title", "description", "uploader", "webpage_url")},
        "cover": str(cover) if cover.exists() else "",
        "targets": targets,
        "copy": {
            "_note": "英文标题/简介/话题由 agent 按 source 里的事实写，别编造产地、功效、价格、认证；中文原文留档不丢",
            "title_en": "", "description_en": "", "hashtags": [],
            "title_zh": src_json.get("title") or "", "description_zh": src_json.get("description") or "",
        },
        "rights": {"is_own_work": None,
                   "_note": "只发本人的作品或已获授权的；别人的作品只进素材库参考，不搬运发布"},
        "prepared_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    write_json(folder / "publish.json", publish)

    review = [
        f"# 待审：{publish['source']['title'][:50] or args.item}",
        "",
        f"- 来源：{publish['source']['platform_label']} {publish['source'].get('uploader') or ''}",
        f"- 原链接：{publish['source'].get('url') or '（本地文件）'}",
        f"- 原时长：{info['duration']}s，原尺寸：{info['width']}x{info['height']}",
        f"- 封面：{publish['cover'] or '没取到'}",
        "",
        "## 成片",
    ]
    for name, t in targets.items():
        flag = "超长，不能直接发" if t["over_limit"] else "可以发"
        review += [f"- {name}：{t['width']}x{t['height']}，{t['duration']}s，"
                   f"{t['vcodec']}/{t['acodec'] or '无音轨'}，{t['size_mb']}MB —— {flag}（上限 {t['limit_s']}s）"]
    review += ["", "## 要 agent 补的（别留空就发）",
               "- 英文标题（≤ 90 字符，说清是什么、给谁看）",
               "- 英文简介（3 句内，写事实；可留原中文一句做识别）",
               "- 话题 3–8 个（平台能吃英文标签）",
               "- 版权：这条是不是本人的作品？不是就不要发，只留素材库",
               "", "## 发布前人工检查",
               "- 画面里有没有别人的水印/平台 logo/二维码",
               "- 有没有个人信息（手机号、地址、订单号）",
               "- 音乐版权：平台曲库里能不能用"]
    (folder / "review.md").write_text("\n".join(review), encoding="utf-8")

    state = read_json(folder / "state.json", {}) or {}
    over = any(t["over_limit"] for t in targets.values())
    state.update({"status": "needs_trim" if over else "prepared", "prepared_at": publish["prepared_at"]})
    write_json(folder / "state.json", state)

    print(f"做好了：{args.item}")
    for name, t in targets.items():
        print(f"  {name}: {t['width']}x{t['height']} {t['duration']}s {t['size_mb']}MB "
              f"{'（超长，需先裁）' if t['over_limit'] else '（可发）'}")
    print(f"  封面：{publish['cover']}")
    print(f"  待审单：{folder / 'review.md'}")
    if any(t["over_limit"] for t in targets.values()):
        return EXIT_OK
    return EXIT_OK


# ---------------------------------------------------------------- status / daily
def all_items() -> list[dict]:
    rows = []
    for folder in sorted((home() / "items").glob("*")):
        src = read_json(folder / "source.json")
        if not src:
            continue
        state = read_json(folder / "state.json", {}) or {}
        pub = read_json(folder / "publish.json", {}) or {}
        rows.append({"item_id": src["item_id"], "platform": src.get("platform_label", ""),
                     "title": (src.get("title") or "")[:44], "duration": src.get("duration"),
                     "status": state.get("status", "ingested"),
                     "batch": state.get("batch"),
                     "copy_ready": bool((pub.get("copy") or {}).get("title_en")),
                     "rights": (pub.get("rights") or {}).get("is_own_work")})
    return rows


def cmd_status(args) -> int:
    rows = all_items()
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return EXIT_OK
    if not rows:
        print("队列是空的。先 ingest 一条链接或文件。")
        return EXIT_OK
    print(f"{'素材':30} {'来源':10} {'时长':>7} {'状态':10} {'文案':6} 标题")
    for r in rows:
        dur = f"{r['duration']:.0f}s" if r["duration"] else "-"
        copy = "有" if r["copy_ready"] else "缺"
        print(f"{r['item_id']:30} {r['platform']:10} {dur:>7} {r['status']:10} {copy:6} {r['title']}")
    return EXIT_OK


def batch_token(date: str, item_ids: list[str]) -> str:
    return hashlib.sha256((date + "|" + ",".join(sorted(item_ids))).encode()).hexdigest()[:12]


def cmd_daily(args) -> int:
    cfg = load_config()
    date = args.date or dt.date.today().isoformat()
    count = args.count or int(cfg["daily"]["count"])
    batch_path = home() / "batches" / f"{date}.json"
    existing = read_json(batch_path)
    if existing and not args.force:
        print(f"{date} 的批次已经定好了（{len(existing['items'])} 条），凭证 {existing['token']}")
        for it in existing["items"]:
            print(f"  - {it}")
        print(f"待审单：{home() / 'batches' / (date + '.md')}")
        return EXIT_OK

    rows = all_items()
    # 可入选：做完成片、还没发出去；且没被别的日期占住（免得同一条跨天重复发）
    usable = [r for r in rows
              if r["status"] in ("prepared", "queued", "approved")
              and r["rights"] is not False
              and (not r["batch"] or r["batch"] == date)]
    stale = [r for r in rows
             if r["status"] in ("queued", "approved") and r["batch"] and r["batch"] != date]
    eligible = usable
    ready = [r for r in eligible if r["copy_ready"]]
    pending_copy = [r for r in eligible if not r["copy_ready"]]

    picked = [r["item_id"] for r in ready][:count]
    if len(picked) < count:
        picked += [r["item_id"] for r in pending_copy][:count - len(picked)]

    if not picked:
        print("没有可发的：要么队列空，要么都还没 prepare，要么版权没过。")
        if stale:
            print(f"另有 {len(stale)} 条之前批过但没发出去（日期不是今天），要用就先确认它们还该发。")
        print("下一步：xp.py ingest <链接> → xp.py prepare <item> → 补英文文案 → xp.py daily")
        return EXIT_OK

    token = batch_token(date, picked)
    batch = {"date": date, "token": token, "created_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
             "items": picked, "approved": False}
    write_json(batch_path, batch)
    for item_id in picked:
        state = read_json(home() / "items" / item_id / "state.json", {}) or {}
        state.update({"status": "queued", "batch": date})
        write_json(home() / "items" / item_id / "state.json", state)

    lines = [f"# {date} 今天这三条", ""]
    for i, item_id in enumerate(picked, 1):
        pub = read_json(home() / "items" / item_id / "publish.json", {}) or {}
        src = pub.get("source", {})
        copy = pub.get("copy", {})
        lines += [f"## {i}. {item_id}",
                  f"- 原标题：{copy.get('title_zh') or src.get('title') or '（空）'}",
                  f"- 英文标题：{copy.get('title_en') or '【还没写】'}",
                  f"- 英文简介：{(copy.get('description_en') or '【还没写】')}",
                  f"- 话题：{' '.join(copy.get('hashtags') or []) or '【还没写】'}",
                  f"- 封面：{pub.get('cover') or '无'}",
                  ""]
    lines += ["## 要人点头的事", "- 这三条是不是你的作品 / 有没有授权（不是就别发）",
              "- 文案有没有说错（产地、工艺、价格）",
              f"- 点头后执行：xp.py approve {date} --by 本人 然后 xp.py publish {date} --target youtube",
              "", f"凭证：{token}"]
    (home() / "batches" / f"{date}.md").write_text("\n".join(lines), encoding="utf-8")

    missing = sum(1 for i in picked if not (read_json(home() / "items" / i / "publish.json", {}) or {}).get("copy", {}).get("title_en"))
    print(f"{date} 定了 {len(picked)} 条（凭证 {token}）")
    for item_id in picked:
        print(f"  - {item_id}")
    print(f"待审单：{home() / 'batches' / (date + '.md')}")
    if missing:
        print(f"注意：{missing} 条还没写英文文案，别直接发。")
    return EXIT_OK


def cmd_approve(args) -> int:
    date = args.batch
    batch = read_json(home() / "batches" / f"{date}.json")
    if not batch:
        die(EXIT_USAGE, f"没有 {date} 的批次，先 daily。")
    if not args.by or args.by.strip() in ("", "agent", "auto"):
        die(EXIT_USAGE, "要写清是谁点的头：--by 本人（agent 不能替人点头）")
    batch.update({"approved": True, "approved_by": args.by,
                  "approved_at": dt.datetime.now().astimezone().isoformat(timespec="seconds")})
    write_json(home() / "batches" / f"{date}.json", batch)
    for item_id in batch["items"]:
        state = read_json(home() / "items" / item_id / "state.json", {}) or {}
        state.update({"status": "approved"})
        write_json(home() / "items" / item_id / "state.json", state)
    print(f"{date} 已记为 {args.by} 点头，可以发布（仍可 --dry-run 预演）。")
    return EXIT_OK


# ---------------------------------------------------------------- publish
def youtube_upload(cfg, file_path: Path, title: str, desc: str, tags: list[str], privacy: str) -> str:
    import urllib.request
    api = cfg["youtube_api"]
    data = urllib.parse.urlencode({
        "client_id": api["client_id"], "client_secret": api["client_secret"],
        "refresh_token": api["refresh_token"], "grant_type": "refresh_token"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    with urllib.request.urlopen(req, timeout=60) as r:
        token = json.load(r)["access_token"]
    size = file_path.stat().st_size
    meta = {"snippet": {"title": title[:100], "description": desc[:4900], "tags": tags[:30],
                        "categoryId": "22"},
            "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}}
    init = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=json.dumps(meta).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Length": str(size), "X-Upload-Content-Type": "video/mp4"})
    with urllib.request.urlopen(init, timeout=60) as r:
        session = r.headers["Location"]
    body = file_path.read_bytes()
    put = urllib.request.Request(session, data=body, method="PUT",
                                 headers={"Content-Type": "video/mp4", "Content-Length": str(size)})
    with urllib.request.urlopen(put, timeout=1800) as r:
        return json.load(r)["id"]


def cmd_publish(args) -> int:
    cfg = load_config()
    date = args.batch
    batch = read_json(home() / "batches" / f"{date}.json")
    if not batch:
        die(EXIT_USAGE, f"没有 {date} 的批次，先 daily。")
    if not batch.get("approved"):
        die(EXIT_USAGE, "这批还没点头，不能发。先让本人确认，再 xp.py approve。")
    if args.token and args.token != batch["token"]:
        die(EXIT_USAGE, "凭证对不上，可能批次被改过。重新 daily 核对。")

    target = args.target
    if target not in ("youtube", "instagram"):
        die(EXIT_USAGE, "--target 只能是 youtube 或 instagram")

    plan = []
    for item_id in batch["items"]:
        pub = read_json(home() / "items" / item_id / "publish.json", {})
        if not pub:
            die(EXIT_USAGE, f"{item_id} 没 prepare 过。")
        t = pub["targets"].get(target) or {}
        copy = pub.get("copy") or {}
        problems = []
        if not Path(t.get("file", "")).exists():
            problems.append("成片文件不在")
        if t.get("over_limit"):
            problems.append(f"超长 {t.get('duration')}s > 上限 {t.get('limit_s')}s")
        if not copy.get("title_en"):
            problems.append("英文标题没写")
        if pub.get("rights", {}).get("is_own_work") is not True:
            problems.append("版权没确认是本人作品")
        plan.append({"item_id": item_id, "file": t.get("file"), "title": copy.get("title_en") or "",
                     "desc": copy.get("description_en") or "", "tags": copy.get("hashtags") or [],
                     "problems": problems})

    print(f"{date} → {target}，{len(plan)} 条")
    blocked = False
    for p in plan:
        print(f"  - {p['item_id']}  {p['title'] or '（无标题）'}")
        for prob in p["problems"]:
            print(f"      卡住：{prob}")
        if p["problems"]:
            blocked = True
    if blocked:
        print("\n先补上面的问题再发。")
        return EXIT_USAGE

    reachable = tcp_ok("www.youtube.com") if target == "youtube" else tcp_ok("www.instagram.com")
    if not reachable:
        die(EXIT_PERSON, f"连不上 {target}：这台机器到不了该站（代理/网络都没通），"
                         f"成片和文案都已备好，通网后重跑这一条命令即可。")

    if not args.do_upload:
        print("\n只是演练，没有上传。确认无误后加 --do-upload 真发。")
        return EXIT_OK

    api = cfg["youtube_api"] if target == "youtube" else cfg["instagram_api"]
    if target == "youtube":
        if not all(api.get(k) for k in ("client_id", "client_secret", "refresh_token")):
            die(EXIT_CONFIG, "YouTube 还没授权（client_id/secret/refresh_token 都空着）。")
        for p in plan:
            vid = youtube_upload(cfg, Path(p["file"]), p["title"], p["desc"], p["tags"],
                                 cfg["targets"]["youtube"].get("privacy", "private"))
            state = read_json(home() / "items" / p["item_id"] / "state.json", {}) or {}
            state.update({"status": "published", "youtube_id": vid,
                          "published_at": dt.datetime.now().astimezone().isoformat(timespec="seconds")})
            write_json(home() / "items" / p["item_id"] / "state.json", state)
            print(f"  已发：https://youtube.com/shorts/{vid}")
        return EXIT_OK

    # Instagram：Graph API 需要公网可访问的视频地址
    if not all(api.get(k) for k in ("access_token", "ig_user_id", "video_url")):
        die(EXIT_CONFIG, "Instagram 还没授权：需要长期 access_token、ig_user_id，以及每个成片的公网地址（video_url）。"
                         "没配之前只能手动上传成品。")
    die(EXIT_CONFIG, "Instagram 的自动发布需要把成片放到公网可访问的地址；当前没配对象存储，走人工上传。")


# ---------------------------------------------------------------- 入口
def main() -> int:
    ap = argparse.ArgumentParser(prog="xp.py", description="小红书/抖音 → YouTube/Instagram 搬运工具链")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="体检").set_defaults(func=cmd_doctor)

    p = sub.add_parser("ingest", help="抓一条链接或收一个本地文件")
    p.add_argument("source")
    p.add_argument("--force", action="store_true", help="已存在也重新抓")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("prepare", help="转成平台规格并出待审单")
    p.add_argument("item")
    p.set_defaults(func=cmd_prepare)

    p = sub.add_parser("status", help="看队列")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("daily", help="定今天要发的几条")
    p.add_argument("--date")
    p.add_argument("--count", type=int)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_daily)

    p = sub.add_parser("approve", help="记录本人点头")
    p.add_argument("batch")
    p.add_argument("--by", required=True)
    p.set_defaults(func=cmd_approve)

    p = sub.add_parser("publish", help="发布（默认演练）")
    p.add_argument("batch")
    p.add_argument("--target", required=True, choices=["youtube", "instagram"])
    p.add_argument("--token")
    p.add_argument("--do-upload", action="store_true")
    p.set_defaults(func=cmd_publish)

    args = ap.parse_args()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
