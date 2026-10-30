# Antigravity Render Backend

This local skill is the preferred image backend on the user's Windows machine.

## Requirements

- Antigravity desktop app is running.
- Its process exposes a CDP port, normally through `--remote-debugging-port`.
- OpenCLI can discover and send to that port.
- The current Antigravity plan includes image generation.

## Command

```powershell
node "C:\Users\21878\.codex\skills\antigravity-image-backend\scripts\render.js" `
  --prompt-file "C:\path\prompt.md" `
  --output-dir "C:\path\output" `
  --count 4 `
  --width 1080 `
  --height 1440 `
  --reference "C:\path\product-01.jpg" `
  --reference "C:\path\style-01.jpg"
```

The script snapshots the current conversation before sending, waits for new
images, removes duplicate images, saves deterministic JPEG outputs, writes
`manifest.json`, and only then writes `done.flag`.

## Failure behavior

- Missing debug port: stop and ask the user to launch Antigravity through the
  workbench helper.
- Fewer images than requested: keep waiting until the timeout; never mark done.
- Login expiry, CAPTCHA, quota exhaustion or account warnings: stop and report.
- Do not resend repeatedly. One send per render request avoids duplicate jobs.
