#!/usr/bin/env python3
"""Generate one PNG with the OpenAI Images API without third-party packages."""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    prompt_group = parser.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument("--prompt", help="Image prompt")
    prompt_group.add_argument("--prompt-file", type=Path, help="Read image prompt from a UTF-8 file")
    parser.add_argument("--output", required=True, type=Path, help="Output PNG path")
    parser.add_argument("--force", action="store_true", help="Allow replacing an existing output file")
    parser.add_argument("--model", default="gpt-image-2.5-flare", help="OpenAI GPT Image model")
    parser.add_argument("--size", default="1024x1024", help="Image size, for example 1024x1024")
    parser.add_argument("--quality", default="high", choices=("low", "medium", "high", "xhigh", "max", "auto"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY is not set. Configure it in the Claude Code local environment, then retry.", file=sys.stderr)
        return 2

    prompt = args.prompt if args.prompt is not None else args.prompt_file.read_text(encoding="utf-8")
    if not prompt.strip():
        print("The image prompt is empty.", file=sys.stderr)
        return 2
    if args.output.exists() and not args.force:
        print(f"Output already exists: {args.output}. Choose another path or pass --force to replace it.", file=sys.stderr)
        return 2

    payload = json.dumps({
        "model": args.model,
        "prompt": prompt,
        "size": args.size,
        "quality": args.quality,
        "n": 1,
        "output_format": "png",
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            result = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"OpenAI API returned HTTP {exc.code}: {detail}", file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"Could not reach the OpenAI API: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Could not read the OpenAI API response: {exc}", file=sys.stderr)
        return 1

    try:
        image_bytes = base64.b64decode(result["data"][0]["b64_json"], validate=True)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        print(f"The OpenAI API response did not contain a valid image: {exc}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(image_bytes)
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
