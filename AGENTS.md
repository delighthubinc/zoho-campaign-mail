# AI / Codex 実務ルール

- セミナー告知メールは既存テンプレートを原則使用し、毎回ゼロからHTMLデザインを作らない。
- 用途に応じて `standard_seminar` / `large_seminar` から `template_type` を選び、イベント固有部分はcampaignデータと可変ブロックで表現する。`standard_seminar` は現時点では未実装である。
- ChatGPTで承認済みの原稿・画像・ブロック構成・デザインをCodexが勝手に再設計しない。
- テンプレート変更が必要な場合、既存テンプレートを破壊せず、ユーザー確認対象の変更案として扱う。
- メール生成の正式ルールは `docs/MAIL_GENERATION_RULES.md`、デザインの正本は `templates/` を参照する。ChatGPT用とCodex用の別テンプレートを作らない。
- Zoho Campaignsへの送信・テスト送信・予約送信は実装も実行もしない。Zoho Draft作成はHTMLのGitHub Pages公開・確認後に限り、最終送信判断は必ずユーザーが行う。
- OAuthのClient ID、Client Secret、Refresh Token、Access Tokenをコード、設定JSON、生成物、ログへ出さない。
- 本番HTMLに仮のCTA URLを残さない。CTA URLが不明な場合は推測せず、ユーザーへ確認する。
- CTAとUTMの正式ルールは `docs/MAIL_GENERATION_RULES.md` に従い、ChatGPTのHTMLプレビュー時点から本番と同じCTA URLを使用する。
- 全セミナーメールは `templates/base/email.html` を共通基盤とし、`assets/common/` のDelight Hubロゴ、Zoho宛名差し込みタグ、配信対象注意書き、天野晴香のプロフィール画像を含む共通署名を必ず表示する。
- セミナーバナーは `build_cta_url()` で生成したCTAと同じ本番URLへのリンクにし、直下にイベントページへ遷移する旨の注意書きを表示する。
- ロゴとプロフィール画像をcampaign単位で複製せず、会社・担当者・宛名・注意書き等の公開共通情報をcampaign JSONへコピーしない。共通値は `config/email_defaults.json` で管理する。

## Ver.2 自動化フロー

- ChatGPTで原稿・本番CTA・HTMLが承認された通常のcampaign反映は、1つの `campaigns/<slug>/` 配下の `campaign.json`、`mail.html`、`images/*` だけを変更する。
- campaign JSONにはディレクトリ名と同じ `campaign_slug`、メール件名 `subject`、本文へ表示しない一意な管理名 `zoho_campaign_name` を必須で保持する。
- PR検証成功後の自動マージは上記campaign限定PRだけに許可する。template、workflow、script、config、docsその他を含むPRは必ずユーザーレビュー待ちとし、自動マージしない。
- main反映後は、同一commitのGitHub Pages deployment成功と公開HTML・画像・CTAの検証が完了するまでZoho Draftを作らない。
- 自動化の終点はZoho Campaigns Draft作成である。`sendcampaign`、テストメール、予約、本番送信、contact listへの配信をコード・workflowへ追加してはならない。
- OAuth値はRepository Secretsからのみ渡し、ログ、artifact、JSON、HTML、commitへ保存しない。
- auto-mergeには専用GitHub App installation tokenを使い、後段のmain push workflowを`GITHUB_TOKEN`のイベント抑止から分離する。
- fail-closed停止時の `EMERGENCY - Recover Zoho Draft Only` は管理者専用のDraft復旧口とし、Zoho UIとledgerを確認した障害時以外は使用しない。
