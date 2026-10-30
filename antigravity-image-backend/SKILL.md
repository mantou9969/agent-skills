---
name: antigravity-image-backend
description: Render image prompts through the user's existing Google Antigravity subscription, including reference images and deterministic output collection. Use as the first image backend on this machine whenever an ecommerce or product-image skill is ready to generate, instead of paid image APIs.
---

# Antigravity Image Backend

Use Antigravity before GPT Image, OmniMaaS or any other paid image API on this
machine. The user pays for a Google AI plan that already grants Antigravity
usage; do not create per-image API cost unless the user explicitly asks for a
fallback.

## When to Use

- An ecommerce or product-image skill has finished planning and prompt writing.
- The user wants to reuse their existing Google AI/Antigravity quota.
- Images need reference photos from local disk.
- Generated images must be collected without asking the user to save them by hand.

Do not use this skill for prompt research alone; use the relevant design skill
first and invoke this backend only when the prompt is ready.

## Execution

1. Keep the product identity lock and approved prompt from the calling skill.
2. Pass every relevant product/reference image with `--reference`.
3. Request the intended count and dimensions.
4. Run the backend once. Do not send duplicate requests while it waits.
5. Treat `done.flag` and `manifest.json` as the completion evidence.

Read [references/operations.md](references/operations.md) for the command and
failure behavior.

## Cost Rule

- Antigravity is the first backend because its usage is part of the existing plan.
- Do not silently fall back to a paid API.
- If Antigravity login, quota or CDP fails, stop and report the exact issue.
- Do not send repeated prompts to work around quota or anti-abuse limits.
