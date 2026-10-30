# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = ["faster-whisper>=1.1", "av<16", "budoux>=0.6"]
# ///
"""ショート動画の字幕づくり。

  uv run caption.py transcribe <動画>            文字起こし → <日付>_<名前>_transcript.json
  uv run caption.py build <transcript.json>      校正済みの JSON → SRT (12文字区切り・隙間なし) と検証
  uv run caption.py burn <動画> <字幕.srt>        字幕を焼き込んだ MP4 (ffmpeg が必要)
"""
import argparse
import datetime
import difflib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PUNCT = "、。，．,.！？!?"


def out_path(video, suffix):
    stem = Path(video).stem
    return Path(video).with_name(f"{datetime.date.today():%Y%m%d}_{stem}_{suffix}")


def media_info(path):
    import av

    with av.open(str(path)) as c:
        dur = float(c.duration / 1_000_000) if c.duration else 0.0
        v = next((s for s in c.streams if s.type == "video"), None)
        size = (v.codec_context.width, v.codec_context.height) if v else None
    return dur, size


def transcribe(args):
    from faster_whisper import WhisperModel

    duration, _ = media_info(args.video)
    print(f"モデル {args.model} を読み込み中 (初回はダウンロードに数分かかります)…", file=sys.stderr)
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(
        str(args.video),
        language="ja",
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=200),
    )
    data = {"source": str(Path(args.video).resolve()), "duration": duration, "model": args.model, "segments": []}
    for s in segments:
        words = [{"start": round(w.start, 3), "end": round(w.end, 3), "word": w.word} for w in (s.words or [])]
        text = s.text.strip()
        data["segments"].append({
            "start": round(words[0]["start"] if words else s.start, 3),
            "end": round(words[-1]["end"] if words else s.end, 3),
            "raw_text": text,
            "text": text,
            "words": words,
        })
        print(f"[{s.start:6.2f}] {text}", file=sys.stderr)
    out = Path(args.out) if args.out else out_path(args.video, "transcript.json")
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out.resolve())


def width(s):
    return sum(0.5 if ord(ch) < 128 else 1 for ch in s)


def hard_split(phrase, limit):
    # 文節が長すぎるときだけ文字で切る。英単語の途中では切らない
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9._\-+]*|\s+|.", phrase)
    parts, cur = [], ""
    for t in tokens:
        if cur and width(cur + t) > limit:
            parts.append(cur)
            cur = t.lstrip()
        else:
            cur += t
    return parts + ([cur] if cur else [])


def split_caption(text, limit):
    import budoux

    parser = budoux.load_default_japanese_parser()
    lines = []
    for sentence in re.split(f"(?<=[{PUNCT}])", text):
        sentence = sentence.strip()
        if not sentence:
            continue
        cur = ""
        for ph in parser.parse(sentence):
            for piece in ([ph] if width(ph) <= limit else hard_split(ph, limit)):
                if cur and width(cur + piece) > limit:
                    lines.append(cur)
                    cur = piece
                else:
                    cur += piece
        if cur:
            lines.append(cur)
    lines = [l.strip().rstrip("、。，．,.") for l in lines]
    lines = [l for l in lines if l]
    merged = []
    for l in lines:
        if merged and width(l) <= 2 and width(merged[-1] + l) <= limit:
            merged[-1] += l
        else:
            merged.append(l)
    if len(merged) > 1 and width(merged[0]) <= 2 and width(merged[0] + merged[1]) <= limit:
        merged[:2] = [merged[0] + merged[1]]
    return merged


def ts(sec):
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def time_at(seg, idx):
    # 校正後の idx 文字目を元の文字起こしの位置に対応づけ、その単語の時刻を使う
    text = seg["text"]
    words = [w for w in seg.get("words", []) if w["word"].strip()]
    if not words:
        return seg["start"] + (seg["end"] - seg["start"]) * idx / max(len(text), 1)
    raw = "".join(w["word"].strip() for w in words)
    pos = len(raw)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, raw, text, autojunk=False).get_opcodes():
        if j1 <= idx < j2 or (j1 == j2 == idx):
            pos = i1 + (idx - j1) * (i2 - i1) // max(j2 - j1, 1) if tag != "insert" else i1
            break
    for w in words:
        n = len(w["word"].strip())
        if pos < n:
            return w["start"] + (w["end"] - w["start"]) * pos / n
        pos -= n
    return words[-1]["end"]


def build(args):
    data = json.loads(Path(args.transcript).read_text(encoding="utf-8"))
    duration = data["duration"]
    caps = []
    for seg in data["segments"]:
        parts = split_caption(seg["text"], args.max)
        if not parts:
            continue
        cursor = 0
        for p in parts:
            idx = seg["text"].find(p, cursor)
            idx = cursor if idx < 0 else idx
            caps.append({"start": time_at(seg, idx), "text": p})
            cursor = idx + len(p)
    if not caps:
        sys.exit("字幕にする発話がありません")
    for c in caps:
        c["start"] = round(c["start"], 3)
    for a, b in zip(caps, caps[1:]):
        a["end"] = b["start"]
    caps[-1]["end"] = round(duration, 3)

    srt = Path(args.out) if args.out else Path(args.transcript).with_name(
        Path(args.transcript).name.replace("_transcript.json", "_subtitles.srt"))
    if srt.suffix != ".srt":
        srt = srt.with_suffix(".srt")
    srt.write_text("".join(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{c['text']}\n\n"
                           for i, c in enumerate(caps, 1)), encoding="utf-8")

    over = [c for c in caps if width(c["text"]) > args.max]
    gaps = sum(1 for a, b in zip(caps, caps[1:]) if abs(a["end"] - b["start"]) > 0.001)
    overlaps = sum(1 for a, b in zip(caps, caps[1:]) if a["end"] > b["start"] + 0.001)
    bad = [c for c in caps if c["start"] >= c["end"]]
    ok = not (over or gaps or overlaps or bad) and abs(caps[-1]["end"] - duration) <= 0.001
    print("=== キャプション検証結果 ===")
    print(f"動画の長さ: {duration:.2f}秒")
    print(f"SRT終了: {caps[-1]['end']:.2f}秒")
    print(f"エントリ数: {len(caps)}")
    print(f"最大文字数: {max(width(c['text']) for c in caps):g}文字")
    print(f"{args.max}文字超過エントリ: " + ("なし" if not over else f"{len(over)}件（要修正）: " + " / ".join(c["text"] for c in over)))
    print(f"ギャップ: {'なし' if not gaps else f'{gaps}件'}")
    print(f"重複: {'なし' if not overlaps else f'{overlaps}件'}")
    if bad:
        print(f"長さ0のエントリ: {len(bad)}件")
    print(f"判定: {'✅ OK' if ok else '❌ 要修正'}")
    print(srt.resolve())
    if not ok:
        sys.exit(1)


def ass_ts(srt_ts):
    h, m, rest = srt_ts.strip().split(":")
    sec, ms = rest.split(",")
    cs = round(int(ms) / 10)
    total = (int(h) * 3600 + int(m) * 60 + int(sec)) * 100 + cs
    h, total = divmod(total, 360000)
    m, total = divmod(total, 6000)
    return f"{h}:{m:02}:{total // 100:02}.{total % 100:02}"


def default_font():
    return {"Darwin": "Hiragino Sans", "Windows": "Yu Gothic UI"}.get(platform.system(), "Noto Sans CJK JP")


def burn(args):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        sys.exit("ffmpeg が見つかりません。Mac は `brew install ffmpeg`、Windows は `winget install Gyan.FFmpeg` で入れてください")
    _, size = media_info(args.video)
    w, h = size
    fs = round(min(w, h) * 0.075)
    style = (f"Style: Default,{args.font or default_font()},{fs},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,"
             f"-1,0,0,0,100,100,0,0,1,{max(2, fs // 10)},0,2,40,40,{round(h * (0.22 if h > w else 0.08))},1")
    events = []
    for block in re.split(r"\n\s*\n", Path(args.srt).read_text(encoding="utf-8-sig").strip()):
        lines = block.splitlines()
        if len(lines) < 3:
            continue
        a, b = (ass_ts(x) for x in lines[1].split("-->"))
        events.append(f"Dialogue: 0,{a},{b},Default,,0,0,0,,{' '.join(lines[2:])}")
    ass = ("[Script Info]\nScriptType: v4.00+\n"
           f"PlayResX: {w}\nPlayResY: {h}\nWrapStyle: 2\n\n"
           "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
           "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
           "Alignment, MarginL, MarginR, MarginV, Encoding\n" + style + "\n\n"
           "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
           + "\n".join(events) + "\n")
    out = Path(args.out).resolve() if args.out else Path(args.srt).resolve().with_name(Path(args.srt).stem + "_captioned.mp4")
    with tempfile.TemporaryDirectory() as tmp:
        # subtitles フィルタはパスの「:」「\」でつまずくので、作業フォルダに置いて名前だけ渡す
        Path(tmp, "subs.ass").write_text(ass, encoding="utf-8")
        cmd = [ffmpeg, "-y", "-v", "error", "-i", str(Path(args.video).resolve()), "-vf", "subtitles=subs.ass",
               "-map", "0:v:0", "-map", "0:a:0?", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)]
        subprocess.run(cmd, cwd=tmp, check=True)
    print(out.resolve())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("transcribe")
    t.add_argument("video")
    t.add_argument("--model", default="large-v3-turbo")
    t.add_argument("--out")
    b = sub.add_parser("build")
    b.add_argument("transcript")
    b.add_argument("--max", type=float, default=12)
    b.add_argument("--out")
    u = sub.add_parser("burn")
    u.add_argument("video")
    u.add_argument("srt")
    u.add_argument("--font")
    u.add_argument("--out")
    args = ap.parse_args()
    if os.name == "nt":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    {"transcribe": transcribe, "build": build, "burn": burn}[args.cmd](args)


if __name__ == "__main__":
    main()
