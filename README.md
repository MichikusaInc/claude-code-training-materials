# Claude Code 研修 素材集

Claude Code 研修の演習で使う素材です。**写っている会社名・人名・金額はすべて架空です。**

## ダウンロード

- まとめて: このページの **Code → Download ZIP**
- 動画だけ: [sample-talk.mp4 をダウンロード](https://github.com/MichikusaInc/claude-code-training-materials/raw/main/video/sample-talk.mp4)（11秒・約34MB）
- 会議の音声だけ: [sample-meeting.mp3 をダウンロード](https://github.com/MichikusaInc/claude-code-training-materials/raw/main/audio/sample-meeting.mp3)（5分22秒・約5MB）
- 関連リンク: [URL一覧.md](URL一覧.md)

## 中身

| フォルダ | 内容 | 演習の例 |
|---|---|---|
| `receipts/` | 領収書・レシートの写真 20枚 | 日付・宛名・金額・但し書きを読み取って Excel / CSV にまとめる |
| `cards/` | 名刺の写真 20枚 | 会社名・氏名・連絡先を読み取って名簿にする |
| `audio/` | 2人の打ち合わせの録音 (社内AI研修の企画会議・5分22秒・mp3) | 文字起こしして、決定事項と宿題 (担当・期限) を議事録にまとめる |
| `video/` | 縦長の自撮り動画 (1080×1920・11秒) | 文字起こし・字幕付け・無音カットなど、Claude Code での動画編集 |
| `.claude/skills/jetcut/` | 無音・フィラーをカットして字幕を付ける Skill | `video/` の動画から無音とフィラーを取り、字幕を付ける |
| `.claude/skills/pptx_michikusa/` | Michikusa の PowerPoint テンプレートと Skill | Skill を使ったスライド作成 |
| `.claude/skills/skill-creator/` | Skill を作る・直す・試すための Skill (Anthropic 公式) | さっきやった作業を Skill にする |
| `.claude/skills/grilling/` | 計画の穴を質問攻めで見つけてくれる Skill (Matt Pocock 作) | 作りたいものや計画を、着手前に詰める |
| `claude-code-plugins/codex-image/` | OpenAI GPT Image で画像を生成する Claude Code プラグイン | Claude Code から画像を生成して PNG で保存する |

会議の音声は ElevenLabs の音声合成で作った架空の打ち合わせです (臼井と、架空の担当者「佐藤」の2人)。

動画は iPhone で撮った `.MOV` を、画質を落とさずに `.mp4` に詰め替えたものです (Windows でもそのまま再生できます)。

## Skill とプラグインの使い方

ZIP を展開したこのフォルダを Claude Code の作業フォルダに選ぶと、`.claude/skills/` の Skill が自動で読み込まれます (`.claude` は隠しフォルダなので、Mac の Finder では `Command + Shift + .` で表示できます)。

| Skill | 呼び方の例 | 事前に入れるもの |
|---|---|---|
| jetcut | `/jetcut video/sample-talk.mp4` または「この動画の無音とフィラーを取って字幕を付けて」 | Apple Silicon の Mac、[ffmpeg](https://ffmpeg.org/)、`pip3 install mlx-whisper torch moviepy pillow` |
| pptx_michikusa | `/pptx_michikusa` または「Michikusa のテンプレートで 5 枚のスライドを作って」 | [uv](https://docs.astral.sh/uv/) |
| skill-creator | `/skill-creator` または「さっきの作業を Skill にして」 | なし (Skill を試す評価機能だけ Python を使う) |
| grilling | `/grilling` のあとに、詰めたい計画や作りたいものを書く | なし |

既存の Skills は API キー不要です。pptx_michikusa と skill-creator、grilling は Mac / Windows で動きます。jetcut は Apple Silicon の Mac 専用です (文字起こしに mlx-whisper を使うため)。uv や ffmpeg が入っていなければ、Claude Code が入れ方を案内します。
jetcut は初回に文字起こしのモデル (mlx-community/whisper-large-v3-turbo、約1.6GB) をダウンロードするので、講座の前に一度動かしておくと当日すぐ使えます。

### codex-image プラグイン

画像生成プラグインを使うときは、リポジトリのルートで Claude Code を起動し、次を実行します。

```text
/plugin marketplace add ./claude-code-plugins
/plugin install codex-image@michikusa-course-plugins
```

Claude Code のローカル環境に `OPENAI_API_KEY` を設定したあと、`/codex-image:generate-image` に続けて作りたい画像を入力します。API キーをチャットに貼らないでください。画像生成には OpenAI API の利用設定が必要です。ChatGPT / Codex の利用枠とは別に API 料金が発生し、生成プロンプトは OpenAI API に送信されます。機密情報は入力しないでください。

ほかのフォルダでも使いたいときは、Skill のフォルダごと `~/.claude/skills/` (Windows は `%USERPROFILE%\.claude\skills\`) にコピーしてください。

## 他の人が作った Skill の出典

次の Skill は、公開されているものを中身を変えずにそのまま入れています。ライセンスは各フォルダの LICENSE を見てください。

| Skill | 作者 | 出典 | ライセンス |
|---|---|---|---|
| skill-creator | Anthropic (Claude の開発元) | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/skill-creator) | Apache License 2.0 |
| grilling | Matt Pocock | [mattpocock/skills](https://github.com/mattpocock/skills/tree/main/skills/productivity) | MIT License |
