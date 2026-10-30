---
name: short-caption
description: ショート動画に字幕を付ける。文字起こし → Claude が校正 → 12文字以内の文節で区切った隙間のない SRT → 検証 → 字幕を焼き込んだ MP4 と投稿文まで作る。「字幕を付けて」「キャプションを付けて」「short-caption」で使う。
---

# ショート動画の字幕 (short-caption)

動画の音声を文字起こしし、校正済みの字幕 (SRT) と、字幕を焼き込んだ MP4 を作る。
無音カットなどの編集はしない。**話しているタイミングと字幕の文字がずれないこと**を最優先にする。

処理は同じフォルダの `caption.py` が行う (以下 `<skill>` はこの SKILL.md があるフォルダのパス)。
Mac / Windows どちらでも同じ手順で動く。API キーやアカウント登録は要らない。

## 0. 準備 (初回だけ)

必要なのは 2 つ。入っていなければ、ユーザーに確認してから入れる。

| ツール | 用途 | 確認 | 入れ方 |
|---|---|---|---|
| uv | Python と必要なライブラリを自動で用意する | `uv --version` | Mac: `curl -LsSf https://astral.sh/uv/install.sh \| sh`<br>Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| ffmpeg | 字幕の焼き込み (手順 4) だけで使う | `ffmpeg -version` | Mac: `brew install ffmpeg`<br>Windows: `winget install Gyan.FFmpeg` |

入れた直後はターミナルを開き直さないとコマンドが見つからないことがある。
`pip install` や `--break-system-packages` は使わない (uv がこのスクリプト専用の環境を作る)。

## 1. 文字起こし

```bash
uv run "<skill>/caption.py" transcribe "<動画のパス>"
```

- 初回は Whisper のモデル (約1.6GB) をダウンロードするので数分かかる。2 回目からは速い
- 動画と同じフォルダに `<日付>_<動画名>_transcript.json` ができる (単語ごとの時刻つき)
- 精度をさらに上げたいときは `--model large-v3` (遅くなる)

## 2. 校正 (Claude がやる)

transcript.json を開き、各セグメントの **`text` だけ**を直す。
`raw_text` / `words` / `start` / `end` は触らない (字幕の時刻は `words` から自動で合わせる)。

直すもの:
- サービス名・専門用語の表記 (クロードコード → Claude Code、チャットGPT → ChatGPT、ジーピーティー → GPT など)
- 英語の技術用語は英語表記 (API、LLM、GitHub、Python など)
- 明らかな聞き間違い・誤字、意味が通らない箇所

守ること:
- 話した内容を足したり削ったり、言い換えたりしない
- 自信のない固有名詞は推測で直さず、最後にユーザーへ「〇〇で合っていますか」と確認する

## 3. SRT を作って検証

```bash
uv run "<skill>/caption.py" build "<transcript.json のパス>"
```

`<日付>_<動画名>_subtitles.srt` ができ、次の検証結果が出る。

```
=== キャプション検証結果 ===
動画の長さ: 11.49秒
SRT終了: 11.49秒
エントリ数: 4
最大文字数: 9.5文字
12文字超過エントリ: なし
ギャップ: なし
重複: なし
判定: ✅ OK
```

字幕のルール (スクリプトが自動で守る):
- 1 枚 12 文字まで (半角英数は 0.5 文字で数える)。句読点で必ず区切り、それ以外は文節 (BudouX) の切れ目で区切る
- 英単語の途中では切らない。1〜2 文字だけの字幕は前後とつなげる。末尾の「、」「。」は表示しない
- 各字幕は次の字幕が出るまで残す (隙間ゼロ・重複ゼロ)。最後の字幕は動画の終わりまで出す

`❌ 要修正` のときは、出ている字幕を見て transcript.json の `text` を直し (長すぎる文に「、」を入れるなど)、build をやり直す。
文字数の上限を変えたいときは `--max 14` のように指定する。

## 4. 字幕を焼き込む

```bash
uv run "<skill>/caption.py" burn "<動画のパス>" "<subtitles.srt のパス>"
```

- `<日付>_<動画名>_subtitles_captioned.mp4` ができる。白文字・黒フチで、縦長動画なら下から 22% の高さ (SNS のボタンに被らない位置)
- フォントは Mac はヒラギノ、Windows は Yu Gothic UI。変えるときは `--font "Noto Sans JP"`
- できたら 2〜3 コマを画像で書き出して、字幕が切れていないか・はみ出していないかを目で確かめる

```bash
ffmpeg -v error -y -ss 3 -i "<captioned.mp4>" -frames:v 1 check.jpg
```

## 5. 投稿用の説明文

校正した全文から、SNS に貼る説明文をチャットに出す (ファイルにはしない)。
- 動画の要点を短い導入文で
- 紹介しているツールやサービスがあれば箇条書き
- 締めの言葉があれば最後に
- ハッシュタグと絵文字は、ユーザーが望んだときだけ

## 6. 報告

- 作ったファイル (transcript.json / subtitles.srt / captioned.mp4) をすべてフルパスで
- 検証結果 (手順 3 の表)
- 校正で直した箇所と、確認してほしい固有名詞
