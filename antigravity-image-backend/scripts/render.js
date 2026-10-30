const fs = require("node:fs");
const path = require("node:path");

const workbenchRoot =
  process.env.CODE_WORKBENCH_ROOT ||
  "C:\\Users\\21878\\Desktop\\每天进度\\codex";
const { sendToAntigravity } = require(path.join(workbenchRoot, "lib", "pipeline"));
const {
  collectAntigravityOutputs,
  snapshotConversationImages,
} = require(path.join(workbenchRoot, "lib", "antigravity"));

function parseArgs(argv) {
  const result = {
    references: [],
    count: 4,
    width: 1080,
    height: 1440,
    timeoutMinutes: 20,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    const value = argv[index + 1];
    if (key === "--help" || key === "-h") {
      result.help = true;
      continue;
    }
    if (key === "--dry-run") {
      result.dryRun = true;
      continue;
    }
    if (!key.startsWith("--")) throw new Error(`无法识别参数：${key}`);
    if (value == null || value.startsWith("--")) {
      throw new Error(`参数缺少值：${key}`);
    }
    index += 1;

    if (key === "--reference") result.references.push(path.resolve(value));
    else if (key === "--prompt-file") result.promptFile = path.resolve(value);
    else if (key === "--prompt") result.prompt = value;
    else if (key === "--output-dir") result.outputDir = path.resolve(value);
    else if (key === "--count") result.count = Number(value);
    else if (key === "--width") result.width = Number(value);
    else if (key === "--height") result.height = Number(value);
    else if (key === "--timeout-minutes") {
      result.timeoutMinutes = Number(value);
    } else {
      throw new Error(`未知参数：${key}`);
    }
  }

  return result;
}

function usage() {
  return `Usage:
  node render.js --prompt-file prompt.md --output-dir output [options]

Options:
  --prompt <text>              Prompt text instead of a prompt file
  --reference <image>          Repeatable reference image path
  --count <1-12>               Expected image count; default 4
  --width <px>                 Output width; default 1080
  --height <px>                Output height; default 1440
  --timeout-minutes <number>   Collection timeout; default 20
  --dry-run                    Build and save the prompt without sending`;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(usage());
    return;
  }
  if (!args.outputDir) throw new Error("缺少 --output-dir");
  if (!args.promptFile && !args.prompt) {
    throw new Error("缺少 --prompt-file 或 --prompt");
  }
  if (!Number.isInteger(args.count) || args.count < 1 || args.count > 12) {
    throw new Error("--count 必须是 1～12");
  }

  const prompt = args.promptFile
    ? fs.readFileSync(args.promptFile, "utf8")
    : String(args.prompt);
  const missingReferences = args.references.filter(
    (file) => !fs.existsSync(file),
  );
  if (missingReferences.length) {
    throw new Error(`参考图不存在：${missingReferences.join(", ")}`);
  }

  fs.mkdirSync(args.outputDir, { recursive: true });
  const finalPrompt = `${prompt}

## Render contract
- Use the image-generation capability included with the current Google Antigravity plan.
- Generate exactly ${args.count} usable images.
- Output target: ${args.width} × ${args.height}.
- Reference images:
${args.references.map((file) => `  - ${file}`).join("\n") || "  - none"}
- Keep the real product's shape, colour, material, count, printed text and logos unchanged.
- Do not invent product facts, accessories or packaging.
- Show the generated images directly in this conversation.
- Do not claim that files were written to disk; the workbench collects them.
`;

  fs.writeFileSync(
    path.join(args.outputDir, "prompt.md"),
    finalPrompt,
    "utf8",
  );
  if (args.dryRun) {
    console.log(
      JSON.stringify(
        {
          ok: true,
          dryRun: true,
          provider: "Antigravity",
          outputDir: args.outputDir,
          promptFile: path.join(args.outputDir, "prompt.md"),
        },
        null,
        2,
      ),
    );
    return;
  }

  let baseline = { signatures: [] };
  try {
    baseline = await snapshotConversationImages();
  } catch {
    // A fresh conversation can legitimately contain no images.
  }

  await sendToAntigravity(finalPrompt, args.references, {
    freshConversation: true,
  });
  const deadline = Date.now() + args.timeoutMinutes * 60_000;
  let lastFound = 0;

  while (Date.now() < deadline) {
    await sleep(8000);
    const result = await collectAntigravityOutputs({
      outputFolder: args.outputDir,
      baseline,
      sourceMeta: {},
      promptCard: { prompt: finalPrompt },
      requiredImages: args.count,
      width: args.width,
      height: args.height,
    });
    lastFound = result.found;
    if (result.complete) {
      console.log(
        JSON.stringify(
          {
            ok: true,
            provider: "Antigravity",
            outputDir: args.outputDir,
            images: result.images,
          },
          null,
          2,
        ),
      );
      return;
    }
  }

  throw new Error(
    `等待 Antigravity 成图超时，目前找到 ${lastFound}/${args.count} 张`,
  );
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
