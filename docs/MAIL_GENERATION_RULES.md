# メール生成 正式運用ルール

本書は、セミナー告知メール制作に関して人間・ChatGPT・Codexが共通で参照する正式仕様です。GitHub上の本書と `templates/` を正本とし、ChatGPT用と本番生成用に別々のテンプレートを作りません。

## 基本原則

- 通常のChatGPT Chatから制作を開始し、原稿だけでなくHTMLプレビューまでユーザー承認を得ます。
- 既存テンプレートを再利用し、イベント固有情報はcampaignデータと可変ブロックで差し替えます。
- ChatGPTはGitHubにある最新テンプレートでプレビューを作ります。Codexは承認済みの原稿・画像・ブロック構成・デザインを同じテンプレートで本番反映し、再解釈や再設計をしません。
- テンプレート自体の変更が必要な場合は既存版を無断で破壊せず、影響範囲を示した変更案としてユーザーの確認を受けます。
- GitHub Pages上のHTML確認が終わるまでZoho Draftを作成しません。送信・テスト送信・予約送信はこのリポジトリの対象外で、最終送信判断は必ずユーザーが行います。

## 正式フロー

1. ユーザーがChatGPTへセミナーとGoogle Driveフォルダを提示する。
2. ChatGPTが本書とGitHubの最新テンプレートを確認する。
3. ChatGPTがDrive内の概要、過去原稿、公開用画像素材を確認する。
4. ChatGPTが `template_type` を選択し、campaignデータ相当の情報とメール原稿を整理する。
5. ChatGPTがGitHubと同一のテンプレートでHTMLプレビューを作り、ユーザーと文章・画像・レイアウトを調整する。
6. ユーザーが文章とデザインをFIXする。
7. Codexが承認済み内容をcampaignデータと画像へ反映し、既存テンプレートでHTMLを生成してテスト・PRを行う。
8. GitHub Pagesへ公開し、ユーザーが表示を確認する。
9. HTML確認後に限りGitHub ActionsからZoho Campaigns Draftを作成する。
10. ユーザーがZoho Draftを最終確認し、リポジトリ外で実際の送信を判断する。

## 担当範囲

### ChatGPT

- Google Driveの対象セミナーフォルダ、セミナー概要、過去メルマガ、公開用画像素材の確認
- `template_type` の選択とメール原稿の作成
- campaignデータ相当の情報整理
- GitHub上の最新テンプレートを使用したHTMLプレビューの作成
- ユーザーとの文章・画像・デザイン調整と、承認内容の確定

### Codex / GitHub

- 承認済み内容のcampaignデータへの反映
- 必要画像のGitHub配置
- 既存の正式テンプレートによる本番HTML生成
- HTML要件・リンク・原稿・既存機能のテスト
- コミット、PR、GitHub Pages公開

Codexは承認済みデザインを独自に改善・再設計しません。差異や実装上の制約がある場合は、変更前に確認対象として明示します。

### GitHub Actions

- ユーザーが指定した公開Google Drive画像の取り込み
- GitHub PagesへのHTML公開後、確認済みHTMLを参照するZoho Draftの作成

Actionsはメール送信、テスト送信、予約送信を行いません。

### ユーザー

- ChatGPT上で原稿とHTMLデザインを確認し、FIXを判断
- 必要に応じたPRとGitHub Pages表示の確認
- Zoho Draftの最終確認
- 実際にメールを送信するかどうかの最終判断

## `template_type` の正式ルール

### `standard_seminar`

通常の単発セミナー向けです。正式な種別名として予約されていますが、現時点では未実装です。実装されるまでは別種別へ読み替えず、必要性をユーザーへ報告します。

### `large_seminar`

フォーラム、大型イベント、複数登壇者・複数コンテンツを持つイベント向けです。`campaigns/forum-20260910` の「不動産未来フォーラム2026」をVer.1とします。

## テンプレートとcampaignデータ

- `templates/base/email.html`: メール幅、基本フォント、背景、フッター、レスポンシブ対応などの共通基盤
- `templates/seminar/large_seminar.html`: `large_seminar` のブロック順、余白、配色、情報階層
- `templates/email_template.html`: `template_type` を持たない従来形式との後方互換用

ChatGPTのプレビューとCodexの本番生成は、いずれも上記GitHubテンプレートを参照します。

campaign JSONはHTMLではなく、イベント固有の `template_type`、`subject`、`preheader`、`banner`、`intro`、`speakers`、`benefits`、`event_info`、`cta`、`footer` 等を保持します。確定済みcampaignデータから `scripts/build_email.py` で `mail.html` を生成します。

## セキュリティと公開ゲート

- OAuthのClient ID、Client Secret、Refresh Token、Access Tokenをコード、設定JSON、campaignデータ、HTML、ログへ保存・出力しません。
- 画像は公開を許可された素材だけをGitHub Pagesへ配置します。
- Zoho Draft作成前に、GitHub PagesのHTML、画像、CTA、件名、本文、レスポンシブ表示を確認します。
- Draft作成は送信承認ではありません。送信操作はユーザーのみが判断します。
