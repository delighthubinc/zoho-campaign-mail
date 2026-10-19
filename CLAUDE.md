# Claude 向け入口

このリポジトリでセミナー告知メールを制作・配信準備するClaudeは、作業前に次を読む。

1. [`docs/MAIL_GENERATION_RULES.md`](docs/MAIL_GENERATION_RULES.md)：運用仕様の正本
2. [`docs/CLAUDE_OPERATIONS.md`](docs/CLAUDE_OPERATIONS.md)：Claudeの実務手順（画像取込、branch、PR、確認方法、停止条件）
3. [`AGENTS.md`](AGENTS.md)：AIエージェント共通の実務ルール
4. [`docs/preview-qa-checklist.md`](docs/preview-qa-checklist.md)：HTMLプレビュー前QA

特に守ること：

- 重要情報（日時、CTA本体URL、UTM、配信日、配信回数）は推測しない。
- campaign画像は `Import Drive Images` の `workflow_dispatch` で毎campaign取り込み、Pages正式URL確認前にHTMLプレビューを出さない。
- HTMLは正式なbase・block・fragmentで生成し、FIX後の `mail.html` は変更しない（hashで確認する）。
- `main` へ直接pushしない。PR作成はユーザーのFIXとPR作成許可の確認後に行い、auto-merge有効化・手動mergeはしない。
- Test Email、予約送信、本番送信はユーザーだけが行う。
