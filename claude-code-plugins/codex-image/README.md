# codex-image

Claude Code 用の画像生成プラグインです。OpenAI GPT Image モデルを OpenAI Images API 経由で呼び出し、PNG 画像を保存します。

## インストール

この研修素材リポジトリのルートで Claude Code を起動し、次を順番に実行します。

```text
/plugin marketplace add ./claude-code-plugins
/plugin install codex-image@michikusa-course-plugins
```

プラグインはユーザー共通スコープで入れると、他のプロジェクトでも利用できます。インストール後は `/codex-image:generate-image 画像の説明` で呼び出します。

## 利用条件

- Python 3 が必要です。追加の Python パッケージは使いません。
- `OPENAI_API_KEY` を Claude Code のローカル環境に設定してください。キーを会話やプロンプトに貼り付けないでください。
- OpenAI API の利用設定が必要です。API の料金は ChatGPT / Codex のサブスクリプションや利用枠とは別です。GPT Image の利用に組織確認が必要な場合があります。
- 生成プロンプトは画像生成のため OpenAI API に送られます。機密情報を含めないでください。

## 実装

- 既定モデル: `gpt-image-2.5-flare`
- 使用モデルは必要に応じて Skill の手順内で変更できます。
- 出力先はプロジェクト内の PNG ファイルです。既存ファイルの上書きは明示指定しない限り行いません。
