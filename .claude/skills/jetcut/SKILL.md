---
name: jetcut
description: 動画の無音とフィラー（えー、あのー等）を取り除き、カット後の時間軸に合わせた字幕を付けて MP4 を作る。「ジェットカット」「無音カット」「フィラーを取って字幕を付けて」「/jetcut」で使う。
---

# ジェットカット (jetcut)

動画からフィラーと無音をカットし、校正済みの字幕を付けた MP4 を作る。
**カット後の時間軸に字幕を合わせること**を最優先にする（ずれると字幕が使えない）。

Apple Silicon の Mac 向け（文字起こしに mlx-whisper を使うため）。

## 使い方

```
/jetcut <動画ファイルパス>
```

出力は入力動画と同じフォルダに作る。

## 手順

必ずこの順番で進める。省略しない。

### 1. 音声を16kHz・モノラルのWAVに変換する

元の音声をそのまま文字起こしに渡さない。変換だけで文字起こしが2〜3倍速くなる。

```bash
ffmpeg -i input.mp4 -ac 1 -ar 16000 -c:a pcm_s16le audio_16k.wav -y
```

### 2. mlx-whisper で文字起こしする

単語ごとのタイムスタンプ付き JSON で出力する。

```bash
mlx_whisper --model mlx-community/whisper-large-v3-turbo --language ja --output-format json --word-timestamps True --output-dir <出力フォルダ> "<audio_16k.wav>"
```

出力 JSON の各セグメントには `words`（各単語の start / end）が入っている。

### 3. Silero VAD で発話区間を求める

```python
import torch, wave, numpy as np

model, utils = torch.hub.load('snakers4/silero-vad', model='silero_vad', trust_repo=True)
(get_speech_timestamps, _, _, _, _) = utils

# torchaudio は使わない（wave で直接読む）
with wave.open("audio_16k.wav", 'rb') as wf:
    frames = wf.readframes(wf.getnframes())
    audio_np = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
wav_tensor = torch.from_numpy(audio_np)

speech_timestamps = get_speech_timestamps(wav_tensor, model, sampling_rate=16000,
    min_silence_duration_ms=500,  # 0.5秒以上の無音でカット
    speech_pad_ms=30,
    min_speech_duration_ms=100,
)
segments = [{"start": ts['start']/16000, "end": ts['end']/16000} for ts in speech_timestamps]
```

- 0.3秒未満のギャップはセグメントに結合する
- フィラーは字幕から外す（フィラー辞書: えーと / えっと / えー / あのー / あの / あー / うーん / んー / そのー。句読点を除いて、最大3語連結の貪欲マッチで判定する）。動画の映像・音声は残す（カットの基準は VAD のまま）
- ハルシネーション除去: `no_speech_prob > 0.5` のセグメントは捨てる
- 単語のタイムスタンプは VAD の境界から±0.3秒はみ出すことがあるので、許容してセグメント境界に丸める

結果は `segments.json`（残す区間の start / end 秒のリスト）に保存する。

### 4. ffmpeg でカットして結合する

セグメントごとに切り出し、concat で1本にする。

```bash
ffmpeg -y -ss {start} -i input.mp4 -t {duration} \
  -c:v libx264 -preset ultrafast -crf 18 \
  -c:a aac -b:a 128k \
  -avoid_negative_ts make_zero \
  seg_XXXXX.mp4

ffmpeg -y -f concat -safe 0 -i concat_list.txt -c copy output_jetcut.mp4
```

セグメントが多いときは20本ずつ `&` で並列化し、`wait` でまとめる。

### 5. SRT を作る（ずれ防止が最重要）

**字幕の時刻はカット後の時間軸で直接計算する。** 元の時刻からの変換はしない。

```
編集後の時刻 = それまでのセグメントの累積長 + (単語の元の start - セグメントの start)
```

文字起こしの区切りルール:
- 字幕は常に1行（改行しない）
- 1エントリ最大22文字程度
- 「。」で文をまとめ、22文字を超えたら「、」で分割、それでも超えたら文節で分割する
- 1〜3文字だけの孤立エントリ（「です。」など）は前のエントリに結合する

**ズレ補正（必須）**: キーフレームの誤差がカットのたびに溜まるので、最後に補正する。

```python
scale = actual_video_duration / srt_last_timestamp  # ffprobe で取得した実長 / SRT 最終時刻
for entry in srt_entries:
    entry["start"] *= scale
    entry["end"] *= scale
```

補正後、誤差が1秒以内に収まっていることを確認する。

### 6. 校正する（Claude がこの会話の中で直す）

API は使わない。`subtitles.srt` の本文を Claude が読んで直す。

- 誤字脱字
- 専門用語の表記（例: チャットGPT→ChatGPT、クロード→Claude）
- 音声認識の誤変換を文脈から直す（例: iTool→AIツール）
- 英語の技術用語は英語表記（API、LLM、GitHub など）

直したら、タイミングは変えずに SRT を書き直す。校正のあと、ステップ5の補正と検証をもう一度行う。

### 7. 検証してから納品する

```bash
ffprobe -v quiet -show_entries format=duration -of csv=p=0 output_jetcut.mp4
tail -5 subtitles.srt
```

- 動画の長さと SRT 最後の終了時刻が1秒以内で一致すること
- 数か所フレームを抜き出し、字幕が正しく出ているか目で確かめる

### 8. 字幕を焼き込む

ffmpeg の brew 版には字幕フィルタが入っていないことがあるため、MoviePy と Pillow で焼き込む。

```python
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, ColorClip

video = VideoFileClip("output_jetcut.mp4")
clips = [video]
FONT = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"  # macOS 標準
FONT_SIZE = 38
PADDING_X = 20
PADDING_Y = 10

for sub in srt_entries:  # start / end / text を持つ
    txt = TextClip(
        text=sub["text"].replace("\n", " ").strip(),
        font=FONT,
        font_size=FONT_SIZE,
        color="white",
        stroke_color="black",
        stroke_width=2,
        method="label",
    )
    bg = ColorClip(
        size=(txt.size[0] + PADDING_X * 2, txt.size[1] + PADDING_Y * 2),
        color=(0, 0, 0)
    ).with_opacity(0.6)

    bg_y = video.size[1] - 100
    txt_y = bg_y + PADDING_Y

    clips.append(bg.with_start(sub["start"]).with_end(sub["end"]).with_position(("center", bg_y)))
    clips.append(txt.with_start(sub["start"]).with_end(sub["end"]).with_position(("center", txt_y)))

final = CompositeVideoClip(clips)
final.write_videofile("output_jetcut_subtitled.mp4",
    codec="libx264", preset="medium",
    audio_codec="aac", bitrate="5000k")
```

字幕の見た目: ヒラギノ角ゴシック W6・38px・白文字・黒の縁取り2px・半透明の黒背景（不透明度0.6）・画面下部中央。常に1行。

### 9. 納品物

- `output_jetcut_subtitled.mp4` … カット済み＋字幕焼き込み（メインの納品物）
- `output_jetcut.mp4` … カット済み（字幕なし）
- `subtitles.srt` … 校正済みの字幕（外部字幕として使える）
- `transcript.json` … 文字起こしの生データ

全ファイルのフルパスを一覧にし、処理時間も添える。

## 注意

- 文字起こしの結果が残っていれば、ステップ2をスキップして再利用する
- 必要なもの: `pip3 install mlx-whisper torch moviepy pillow`（torchaudio は不要）
- ffmpeg は Homebrew で入れる（`brew install ffmpeg`）
