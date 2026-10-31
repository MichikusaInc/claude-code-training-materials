---
name: generate-image
description: Generate an image with OpenAI GPT Image from Claude Code. Use whenever the user asks to create or generate an image using OpenAI/Codex image generation, and save the resulting image in the requested project or location.
argument-hint: [image prompt]
---

# Generate an image with OpenAI

Use the bundled `scripts/generate_image.py` script to create a PNG through the OpenAI Images API. The API key must already be available as `OPENAI_API_KEY`; never ask the user to paste a key into chat, print it, or write it into a file.

## Workflow

1. Turn the user's request into a concise, specific image prompt. Preserve requested language, dimensions, style, subject, and composition. Ask only if a missing detail materially affects the result.
2. Choose an output path in the current project when the user did not specify one. Use a descriptive filename ending in `.png` and do not overwrite an existing file without the user's request.
3. Run the bundled script with the prompt as one quoted argument and the chosen output path. Use `gpt-image-2.5-flare` by default; select `gpt-image-2.5-sunburst` when precise visual detail is the priority.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/generate_image.py" \
  --output "<project-path>/generated-image.png" \
  --model gpt-image-2.5-flare \
  --prompt "<image prompt>"
```

If a prompt contains quotes or shell punctuation, escape it safely or write it to a temporary prompt file outside the project and pass that file with `--prompt-file`.

4. Confirm the saved file exists and report its absolute path. If the API rejects the request, relay the error without exposing environment variables or credentials. Do not silently switch to another provider.

## Limits

- This uses the OpenAI API, not a private Codex desktop image-generation interface.
- OpenAI API billing and ChatGPT/Codex subscription usage are separate. Do not claim that ChatGPT plan usage covers this request.
- API image generation may require an enabled API billing account and organization verification.
