# メール生成 正式運用ルール

本書はセミナー告知メール制作の正式仕様です。GitHub上の本書を運用仕様の正本とします。

`templates/` は初期HTMLと標準デザインの参照元、ユーザーFIX後の `campaigns/<slug>/mail.html` はそのcampaignの最終表示の正本です。`campaign.json` は管理・Validation・automation用であり、HTML生成元ではありません。

## 基本原則

- 制作はChatGPT Chatから開始し、件名・本文・HTMLプレビューまでユーザー確認を行う。
- ChatGPTはGitHubの標準block / fragmentを実際に参照し、ユーザーが変更を指示していない箇所を独自再設計しない。
- campaign固有画像は過去campaign画像との突合・再利用を通常フローで行わず、原則として毎campaign Google Driveの元画像から `campaigns/<slug>/images/` へ取り込む。
- FIX後のHTMLはCodexへ添付・巨大コピペせず、ChatGPTがGitHub作業branchへ `mail.html` として直接保存する。
- Codexは同じ作業branchを引き継ぎ、FIX済み `mail.html` を絶対に変更せず、`campaign.json` 整備・Validation・テストを担当する。
- PR作成は人間の承認ゲート。ChatGPTレビュー後にユーザーがCodex画面からPRを作成し、その後GitHub画面でbaseが `main` か必ず確認する。
- GitHub Pages上の公開HTML検証成功時だけZoho Campaigns Draftを自動作成する。Test Email、予約送信、本番送信は自動化しない。

## 制作開始

最初の返答までに以下を確認する。

### GitHub
- `docs/MAIL_GENERATION_RULES.md`
- `AGENTS.md`
- `templates/base/email.html`
- `templates/seminar/blocks/`
- `templates/seminar/fragments/`
- 必要に応じて既存campaign・関連テンプレート

### Google Drive
セミナー概要、開催情報、登壇者、CTA、今回使用する画像候補を確認する。過去メールは参考にしてよいが、過去配信確認のためだけに制作を止めない。

### 最初のユーザー確認
以下を一度に提示する。
- 推奨preset：`standard` / `large`
- CTA本体URL
- UTM案（最低限 `utm_source` / `utm_medium` / `utm_campaign`。`utm_content` は必要時のみ）
- 今回使用するDrive画像のファイル名＋用途
- 必要に応じてblock構成の大枠

最後に「この制作条件で進めてよいですか？」と1回だけ確認する。CTA本体URLなど誤誘導につながる重要情報は推測しない。

## 訴求決定とHTML制作

制作条件承認後、今回の主訴求を3〜5案程度提示してユーザーに選んでもらう。訴求決定後は、件名、preheader、本文、CTA、画像、レイアウト、HTMLプレビューまで一気に作成する。

標準デザインの役割：
- `templates/base/email.html`：メール全体の固定シェル
- `standard` / `large`：初稿構成のpreset
- `templates/seminar/blocks/*.html`：block外側の標準レイアウト
- `templates/seminar/fragments/*.html`：block内部の標準部品
- `campaigns/<slug>/mail.html`：FIX後の最終表示の正本

既存block相当の表現は対応するblock / fragmentのHTML/CSSを原則そのまま使用する。ユーザーから明示的な変更指示がある箇所だけcampaign固有に変更し、他blockまで連鎖的に変更しない。

## 共通シェル・共通署名

ロゴ、宛名、配信対象注意書き、フッター署名は手入力・記憶・過去の別担当者情報から再構成してはいけない。

`templates/base/email.html` と `config/email_defaults.json` の現在値をそのまま使用する。特に `email_defaults.json` の以下を唯一の正本とする。

- `company_name`
- `department`
- `contact_name`
- `postal_code`
- `address`
- `email`
- `corporate_site_url`
- `logo_url`
- `contact_image_url`
- `zoho_recipient`
- `recipient_notice`
- `banner_notice`

担当者名、部署、住所、メール、プロフィール画像等をcampaign都合で変更しない。Validationは共通画像だけでなく共通署名の主要文字列も `email_defaults.json` と一致することを検査する。

## 画像取込

campaign固有のバナー、登壇者画像、セッション画像、イベント固有ロゴ等は原則 `campaigns/<slug>/images/` に置く。

- 過去campaignに同じ画像があっても通常は再利用しない。
- 同一セミナーの2通目・3通目でもcampaignごとに取り込む。
- 同一campaignの専用 `images/` に今回使用する同一画像が正常に存在する場合のみ再取込不要。
- 配信済みcampaign画像は後続campaignの都合で上書き・削除・リネームしない。
- Delight Hubロゴ、共通署名画像等の固定素材のみ `assets/common/` を再利用する。

ChatGPTは取込前にDrive画像のファイル名と用途をユーザーへ明示する。未取込なら原則 `[automation:image-import]` Issueを作成しActionsで取り込み、Issue結果、repository file、GitHub Pages URLを確認する。Codexは画像binaryを追加・変更・コピーしない。

## HTML FIX → GitHub作業branch

ユーザーが「これでFIX」等の意思表示をした時点のHTMLを表示内容の正本とする。

ChatGPTが `main` からcampaign用作業branchを作成し、FIX済みHTMLを `campaigns/<slug>/mail.html` へ直接保存する。`main` は直接変更しない。保存後、HTMLがそのまま反映され、意図しない他ファイル変更がないことを確認する。

## 成果物

- `mail.html`：本文、デザイン、CSS、レスポンシブ挙動を含む表示内容の唯一の正本。
- `campaign.json`：`campaign_slug`、`subject`、`preheader`、`zoho_campaign_name`、CTA/UTM、画像manifest等の管理・Validation・automation用。HTML生成元ではない。
- `content_source`：通常campaignは `fixed_html`。
- `scripts/build_email.py`：初期HTML生成、標準デザイン参照、開発・テスト用途。FIX済みHTMLの再生成一致は要求しない。

## Codex

ユーザーはChatGPTが指定した同じ作業branchをCodexで選択して実行する。Codexへの必須指示：

- `mail.html` はユーザーFIX済みの正本。絶対に変更しない。
- HTML/CSS/文面/レスポンシブ挙動を再設計・再生成しない。
- blocksへ逆変換せず、`build_email.py` から再生成しない。
- `campaign.json` を現行正式仕様と `mail.html` に合わせて整備する。
- `content_source: "fixed_html"` を維持し、subject / preheader / CTA / UTM / images等を整合させる。
- Validationと必要なテストを実行する。
- 画像binary、template、fragment、script、workflow、docs等を通常campaignでは変更しない。
- push、PR作成、`gh pr create` は行わず、実装・テスト・ローカルcommitで停止する。
- 完了後、変更ファイル、主要設定、`mail.html` 未変更、Validation/テスト結果、commit ID、想定外変更の有無を報告する。

通常、Codexが変更するcampaign成果物は `campaigns/<slug>/campaign.json` のみ。

## Codex後・PR

Codex結果を元Chatへ戻し、ChatGPTは `mail.html` 未変更、`campaign.json`、subject/preheader、CTA/UTM、images、共通署名、Validation、テスト、想定外変更をレビューする。

問題なければChatGPTは「Codex画面からPRを作成してください」と案内する。

PR作成後、ChatGPTは毎回必ず次を案内する。

**「GitHub画面でbase branchが `main` になっているか確認してください。`main` でなければ `main` に変更してください。」**

通常campaignの最終PRのbaseは必ず `main` とする。作業branchをbaseにしたPRを最終PRとして使わない。`main` 向けPRには `mail.html` と `campaign.json` の両方が差分として含まれる状態にする。

## PR Validation / auto-merge

`PR Campaign Validation` はunit tests、Python compile、`git diff --check`、placeholder、仮URL、Zoho差し込みタグ、CTA/UTM、campaign画像、共通画像、共通署名、JavaScript、Secretらしき値等を検査する。

pull requestの `edited` イベントもValidation起動対象とする。baseを `main` へ変更した場合、Close→Reopenや古いrunの再実行ではなく、変更後のbase SHAで新しいValidationを実行する。

通常campaign限定PRはrequired checks成功後にGitHub Appがauto-mergeする。template、workflow、script、config、docs、複数campaign、対象外path等を含むシステム変更PRは自動マージせず、ユーザーレビューを必須とする。

## Pages検証とZoho Draft

main反映後、`Verify Pages and Create Zoho Draft` は同一commitのGitHub Pages deployment成功を待ち、公開HTML、画像、CTA、件名、campaign識別情報等を検証する。公開検証成功時だけZoho Campaigns Draftを作成する。

OAuth値はRepository SecretsからDraft作成stepだけへ渡し、tokenやsecretをコード、JSON、HTML、ログ、artifactへ出さない。自動化の終点はDraft作成。Test Email、予約送信、本番送信、`sendCampaign`系APIは自動化しない。

## 正式フロー

1. ChatGPTがGitHub仕様とDrive素材を確認し、preset・CTA・UTM・使用画像をまとめて提示。
2. ユーザーが制作条件を承認。
3. ChatGPTが訴求候補を提示し、ユーザーが主訴求を選択。
4. ChatGPTが件名・preheader・本文・HTMLを制作・調整。共通シェル・署名は `email_defaults.json` をそのまま使用。
5. campaign固有画像を今回campaign専用 `images/` へ取込。
6. ユーザーがHTMLをFIX。
7. ChatGPTが作業branchへFIX済み `mail.html` を保存。
8. ChatGPTがCodex用プロンプトを作成。
9. ユーザーがCodexで同じ作業branchを選択して実行。
10. Codexは `mail.html` を変更せず `campaign.json` 整備・Validation・テスト・commit。
11. Codex結果をChatGPTへ戻しレビュー。
12. ChatGPTのレビューOK後、ユーザーがCodex画面からPRを作成。
13. ChatGPTが「GitHubでbaseが `main` か確認し、違えば `main` に変更」と必ず案内。
14. Validation成功後auto-merge。
15. GitHub Pages deployment・公開HTML検証。
16. Zoho Campaigns Draft自動作成。
17. ユーザーがTest Emailを手動実行。
18. 問題なければユーザーが本番送信を手動実行。

承認・自動化境界：

**ChatでHTML FIX → Chatが作業branchへ `mail.html` 保存 → Codexが同branchで `campaign.json` 整備・検証 → ChatGPTレビュー → ユーザーがCodex画面からPR作成 → base=`main` を確認・必要なら変更 → Validation → auto-merge → Pages → 公開検証 → Zoho Draft**

## セキュリティ

- OAuthのClient ID、Client Secret、Refresh Token、Access Tokenをコード、設定JSON、campaignデータ、HTML、ログへ保存・出力しない。
- 画像は公開を許可された素材だけをGitHub Pagesへ配置する。
- 本番HTMLに仮CTA URL、placeholder、TODO等を残さない。
- Draft作成は送信承認ではない。送信操作はユーザーのみが判断する。
- `EMERGENCY - Recover Zoho Draft Only` は管理者専用のDraft復旧口とし、Zoho UIとledgerを確認した障害時だけ使用する。
