---
name: xiaohongshu-copywriter
description: Write product-led Xiaohongshu / RedNote titles, captions and tags from verified product facts and approved images. Use for product seeding, recommendation cards, image-post captions, shopping notes and copy review; do not invent personal experience, efficacy, certifications, prices or specs.
---

# Xiaohongshu Copywriter

## Goal

Produce natural, publishable Xiaohongshu copy that preserves the product's
verified facts and matches the approved visual direction. The output must be
usable by the workbench publisher and readable as a real person's note.

## Required Inputs

- Product name, category and verified selling points.
- Price only when confirmed.
- Audience and intended use scene.
- Approved product images or a factual description of them.
- Optional reference style: borrow rhythm and visual language, never wording,
  personal stories, product claims or brand identity.

If a required factual input is missing, leave it out or ask. Never fill a gap
with a plausible number, material, certification, discount or experience.

## Workflow

1. Build a fact lock: product name, visible attributes, confirmed price,
   included items and forbidden claims.
2. Choose one practical angle from the approved images:
   detail, styling, use scene, selection tips or honest product introduction.
3. Draft three titles. Prefer a concrete benefit or scene; avoid forced emoji,
   clickbait, absolute claims and competitor put-downs.
4. Write the body as short, natural paragraphs. Clearly distinguish verified
   facts from subjective style description.
5. Add 3-8 directly relevant tags. Do not stuff unrelated traffic tags.
6. Run the fact and compliance review below.

## Hard Rules

- Do not say “亲测”, “用了半年”, “回购”, “朋友推荐” or imply ownership unless the
  user supplied that real experience.
- Do not invent efficacy, safety, rarity, origin, certification or craftsmanship.
- Do not use “最、第一、绝对、全网最低、百分百” or unsupported superlatives.
- Do not include off-platform contact details, QR codes or purchase links.
- Preserve CJK punctuation and the author's natural cadence.
- Avoid AI-template phrases such as “首先其次最后”“综上所述”“在这个时代”
  and chains of identical short slogans.
- Every paragraph must be supported by product facts or the approved images.
- If the platform or current policy requires AIGC disclosure, remind the user;
  never help conceal AI generation.

## Output Contract

Return:

```json
{
  "titleAlternatives": ["方案1", "方案2", "方案3"],
  "title": "推荐标题",
  "body": "完整正文",
  "tags": ["标签1", "标签2"],
  "coverHeading": "封面短标题，最多22字",
  "factCheck": ["事实依据1", "事实依据2"],
  "riskNotes": ["需要人工确认的事项"]
}
```

For publisher integration, `title`, `body` and `tags` map directly to the
workbench copy artifact. Do not add Markdown fences inside those fields.

## Final Review

- Product identity stayed consistent with the approved images.
- No fabricated experience, specs, results or urgency.
- Title is easy to understand at feed size.
- Body matches the intended audience and use scene.
- Tags are relevant and not spammy.
- Final copy still reads naturally when spoken aloud.
