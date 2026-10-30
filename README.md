# Claude Code 研修 素材集

Claude Code 研修の演習で使う素材です。**写っている会社名・人名・金額はすべて架空です。**

## ダウンロード

- まとめて: このページの **Code → Download ZIP**
- 動画だけ: [sample-talk.mp4 をダウンロード](https://github.com/MichikusaInc/claude-code-training-materials/raw/main/video/sample-talk.mp4)（11秒・約34MB）

## 中身

| フォルダ | 内容 | 演習の例 |
|---|---|---|
| `receipts/` | 領収書・レシートの写真 20枚 | 日付・宛名・金額・但し書きを読み取って Excel / CSV にまとめる |
| `cards/` | 名刺の写真 20枚 | 会社名・氏名・連絡先を読み取って名簿にする |
| `video/` | 縦長の自撮り動画 (1080×1920・11秒) | 文字起こし・字幕付け・無音カットなど、Claude Code での動画編集 |
| `.claude/skills/short-caption/` | 字幕付けの Skill | `video/` の動画に字幕を付ける |
| `.claude/skills/pptx_michikusa/` | Michikusa の PowerPoint テンプレートと Skill | Skill を使ったスライド作成 |

動画は iPhone で撮った `.MOV` を、画質を落とさずに `.mp4` に詰め替えたものです (Windows でもそのまま再生できます)。

## Skill の使い方

ZIP を展開したこのフォルダを Claude Code の作業フォルダに選ぶと、`.claude/skills/` の Skill が自動で読み込まれます (`.claude` は隠しフォルダなので、Mac の Finder では `Command + Shift + .` で表示できます)。

| Skill | 呼び方の例 | 事前に入れるもの |
|---|---|---|
| short-caption | `/short-caption video/sample-talk.mp4` または「この動画に字幕を付けて」 | [uv](https://docs.astral.sh/uv/)、焼き込みには ffmpeg |
| pptx_michikusa | `/pptx_michikusa` または「Michikusa のテンプレートで 5 枚のスライドを作って」 | [uv](https://docs.astral.sh/uv/) |

どちらも API キーやアカウント登録は不要で、Mac / Windows で動きます。uv や ffmpeg が入っていなければ、Claude Code が入れ方を案内します。
short-caption は初回に文字起こしのモデル (約1.6GB) をダウンロードするので、講座の前に一度動かしておくと当日すぐ使えます。

ほかのフォルダでも使いたいときは、Skill のフォルダごと `~/.claude/skills/` (Windows は `%USERPROFILE%\.claude\skills\`) にコピーしてください。
