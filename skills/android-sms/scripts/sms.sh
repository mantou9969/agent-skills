#!/usr/bin/env bash
# android-sms — SMS access over adb. Read-only unless you explicitly use `send`.
set -uo pipefail
export MSYS_NO_PATHCONV=1

usage() {
  cat <<'EOF'
用法: bash scripts/sms.sh <命令> [参数]

  check              自检：adb 路径 / 设备 / 短信条数 / 最新一条
  list [N]           最近 N 条（默认 20）
  latest             最新 1 条
  code [关键词]       从最新短信提取验证码（可限定发件方关键词，如 阿里巴巴）
  wait [秒]          等新短信（默认 120 秒）
  export [文件]      导出全部收件箱为 TSV（默认当前目录）
  send 号码 正文      发一条短信（会占用手机、需要解锁；发前先让用户确认）
  send 号码 -f 文件   正文从文件读，适合长文本

输出格式: 时间 <TAB> 号码 <TAB> 内容
环境变量: ADB_SMS_ADB  指定 adb 可执行文件路径
EOF
}

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
info() { printf '%s\n' "$*" >&2; }

find_adb() {
  if [ -n "${ADB_SMS_ADB:-}" ] && [ -x "${ADB_SMS_ADB}" ]; then printf '%s' "$ADB_SMS_ADB"; return 0; fi
  if command -v adb >/dev/null 2>&1; then command -v adb; return 0; fi
  local c
  for c in "$HOME"/Downloads/platform-tools*/platform-tools/adb.exe \
           "$HOME"/Downloads/platform-tools*/adb.exe \
           "$HOME"/Desktop/platform-tools*/platform-tools/adb.exe \
           "/c/platform-tools/adb.exe" \
           "C:/Android/platform-tools/adb.exe" \
           "${LOCALAPPDATA:-/nonexistent}/Android/Sdk/platform-tools/adb.exe"; do
    [ -x "$c" ] && { printf '%s' "$c"; return 0; }
  done
  return 1
}

ADB="$(find_adb)" || fail "没找到 adb。装 Platform-Tools: https://developer.android.com/tools/releases/platform-tools ；或设 ADB_SMS_ADB=/路径/adb.exe"

device_serial() {
  "$ADB" devices 2>/dev/null | awk 'NR>1 && $2=="device" {print $1; exit}'
}

require_device() {
  local s
  s="$(device_serial)"
  [ -n "$s" ] || fail "手机没连上。USB 线插好 → 设置里打开开发者选项和 USB 调试 → 手机上点“允许” → 再跑 sms.sh check"
}

# ms \t address \t body
raw_rows() {
  "$ADB" shell content query --uri content://sms/inbox --projection address:date:body 2>/dev/null \
    | tr -d '\r\000' \
    | awk '/^Row: /{if(p!="")print p; p=$0; next} {if(p!="")p=p" "$0} END{if(p!="")print p}' \
    | sed -nE 's/^Row: [0-9]+ address=([^,]*), date=([0-9]+), body=(.*)$/\2\t\1\t\3/p'
}

fmt_rows() {
  awk -F'\t' '{
    if ($1 == "") next
    body = $0
    sub(/^[^\t]*\t[^\t]*\t/, "", body)
    printf "%s\t%s\t%s\n", strftime("%Y-%m-%d %H:%M:%S", int($1/1000)), $2, body
  }'
}

cmd_check() {
  printf 'adb: %s\n' "$ADB"
  local s model n last
  s="$(device_serial)"
  if [ -z "$s" ]; then
    printf 'device: 未连接\n'
    printf '处理: USB 线插好 → 开发者选项 → USB 调试 → 手机点“允许”\n'
    exit 1
  fi
  model="$("$ADB" -s "$s" shell getprop ro.product.model 2>/dev/null | tr -d '\r')"
  printf 'device: %s (%s)\n' "$s" "$model"
  n="$(raw_rows | wc -l | tr -d ' ')"
  printf 'sms: %s 条\n' "$n"
  last="$(raw_rows | sort -t$'\t' -k1,1nr | head -n 1)"
  [ -n "$last" ] && printf '最新: %s\n' "$(printf '%s\n' "$last" | fmt_rows)"
  return 0
}

cmd_list() {
  local n="${1:-20}" rows
  case "$n" in ''|*[!0-9]*) fail "N 必须是数字" ;; esac
  rows="$(raw_rows)"
  [ -n "$rows" ] || fail "没读到短信。先跑 sms.sh check 看设备和权限"
  printf '%s\n' "$rows" | sort -t$'\t' -k1,1nr | awk -F'\t' -v n="$n" 'NR<=n' | fmt_rows
}

cmd_latest() { cmd_list 1; }

cmd_code() {
  local kw="${1:-}" rows hit body c
  rows="$(raw_rows)"
  [ -n "$rows" ] || fail "没读到短信。先跑 sms.sh check"
  if [ -n "$kw" ]; then
    hit="$(printf '%s\n' "$rows" | sort -t$'\t' -k1,1nr | awk -F'\t' -v k="$kw" 'index($3,k)>0' | awk 'NR==1')"
    [ -n "$hit" ] || fail "最近短信里没有包含「$kw」的"
  else
    hit="$(printf '%s\n' "$rows" | sort -t$'\t' -k1,1nr | awk 'NR==1')"
  fi
  body="$(printf '%s' "$hit" | cut -f3-)"
  c="$(printf '%s' "$body" | sed -nE 's/.*(验证码|校验码|动态码|动态密码|安全码|code)[^0-9]{0,10}([0-9]{4,8}).*/\2/Ip' | awk 'NR==1')"
  [ -n "$c" ] || c="$(printf '%s' "$body" | grep -oE '[0-9]{4,8}' | awk 'NR==1')"
  [ -n "$c" ] || fail "这条短信里没有 4-8 位数字：$body"
  printf '%s\n' "$c"
}

cmd_wait() {
  local timeout="${1:-120}" start before now
  case "$timeout" in ''|*[!0-9]*) fail "秒数必须是数字" ;; esac
  before="$(raw_rows | sort -t$'\t' -k1,1nr | awk 'NR==1' | cut -f1)"
  start=$SECONDS
  info "WAIT: 等新短信，最多 ${timeout}s（现在去点发送验证码）"
  while [ $((SECONDS - start)) -lt "$timeout" ]; do
    sleep 2
    now="$(raw_rows | sort -t$'\t' -k1,1nr | awk 'NR==1' | cut -f1)"
    if [ -n "$now" ] && [ "$now" != "$before" ]; then
      raw_rows | sort -t$'\t' -k1,1nr | awk -F'\t' -v b="${before:-0}" '$1+0 > b+0' | fmt_rows
      return 0
    fi
  done
  fail "WAIT: ${timeout}s 内没等到新短信"
}

cmd_export() {
  local out="${1:-$PWD/sms-export-$(date +%Y%m%d-%H%M%S).tsv}" rows
  rows="$(raw_rows)"
  [ -n "$rows" ] || fail "没读到短信。先跑 sms.sh check"
  {
    printf '时间\t号码\t内容\n'
    printf '%s\n' "$rows" | sort -t$'\t' -k1,1nr | fmt_rows
  } > "$out" || fail "写文件失败: $out"
  printf '%s\n' "$out"
}

ui_xml() {
  "$ADB" shell uiautomator dump /sdcard/_sms_ui.xml >/dev/null 2>&1 || return 1
  "$ADB" shell cat /sdcard/_sms_ui.xml 2>/dev/null | tr -d '\r'
}

ui_bounds() {
  local pat="$1" xml
  xml="$(ui_xml)"
  printf '%s' "$xml" | tr '>' '\n' \
    | grep -E "content-desc=\"($pat)\"|text=\"($pat)\"|resource-id=\"[^\"]*($pat)[^\"]*\"" \
    | grep -F 'clickable="true"' | awk 'NR==1' \
    | sed -nE 's/.*bounds="\[([0-9]+),([0-9]+)\]\[([0-9]+),([0-9]+)\]".*/\1 \2 \3 \4/p'
}

tap_bounds() {
  local x1 y1 x2 y2
  set -- $1
  x1=$1; y1=$2; x2=$3; y2=$4
  "$ADB" shell input tap $(( (x1 + x2) / 2 )) $(( (y1 + y2) / 2 ))
}

cmd_send() {
  local num="${1:-}" body="" b confirm now_ms recent
  shift || true
  if [ "${1:-}" = "-f" ]; then
    [ -r "${2:-}" ] || fail "读不到文件: ${2:-}"
    body="$(cat "$2")"
  else
    body="$*"
  fi
  case "$num" in ''|*[!0-9]*) fail "号码只能是数字: $num" ;; esac
  [ ${#num} -ge 6 ] || fail "号码太短: $num"
  [ -n "${body//[[:space:]]/}" ] || fail "正文是空的"

  local esc="${body//\'/\'\\\'\'}"
  "$ADB" shell am force-stop com.android.mms >/dev/null 2>&1
  sleep 1
  "$ADB" shell "am start -a android.intent.action.SENDTO -d 'sms:$num' --es sms_body '$esc'" >/dev/null 2>&1 \
    || fail "打不开短信编辑页"
  sleep 2

  b="$(ui_bounds '发送短信|send_button|Send')"
  [ -n "$b" ] || fail "找不到发送按钮：手机可能锁屏了，或被弹窗挡住，先解锁再看一眼"
  tap_bounds "$b"
  sleep 2

  confirm="$(ui_bounds '确定|允许|同意|继续')"
  [ -n "$confirm" ] && { tap_bounds "$confirm"; sleep 1; }

  local sample="${body:0:12}" i xml
  for i in 1 2 3 4 5; do
    sleep 2
    xml="$(ui_xml)"
    if printf '%s' "$xml" | grep -qF "$sample" \
       && printf '%s' "$xml" | grep -qE '送达|已发送|发送成功'; then
      printf 'SENT: %s（%s 字，界面上已送达）\n' "$num" "${#body}"
      return 0
    fi
  done

  now_ms=$(( $(date +%s) * 1000 ))
  recent="$("$ADB" shell content query --uri content://sms/sent --projection address:date 2>/dev/null \
    | tr -d '\r\000' | grep -F "address=$num" | sed -nE 's/.*date=([0-9]+).*/\1/p' | sort -nr | awk 'NR==1')"
  if [ -n "$recent" ] && [ $(( now_ms - recent )) -lt 300000 ]; then
    printf 'SENT: %s（%s 字，已进“已发送”）\n' "$num" "${#body}"
    return 0
  fi
  fail "没确认发出去：界面没显示送达，短信库里也没有。看一眼手机，可能是 SIM 欠费或有弹窗"
}

[ $# -ge 1 ] || { usage; exit 1; }
CMD="$1"; shift

case "$CMD" in
  check)   require_device; cmd_check ;;
  list)    require_device; cmd_list "${1:-20}" ;;
  latest)  require_device; cmd_latest ;;
  code)    require_device; cmd_code "${1:-}" ;;
  wait)    require_device; cmd_wait "${1:-120}" ;;
  export)  require_device; cmd_export "${1:-}" ;;
  send)    require_device; cmd_send "$@" ;;
  -h|--help|help) usage ;;
  *) usage; fail "未知命令: $CMD" ;;
esac
