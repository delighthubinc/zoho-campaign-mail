# メール生成 正式運用ルール

本書はセミナー告知メール制作の正式仕様です。GitHub上の本書を運用仕様の正本とします。

`templates/` は初期HTMLと標準デザインの参照元、ユーザーFIX後の `campaigns/<slug>/mail.html` はそのcampaignの最終表示の正本です。`campaign.json` は管理・Validation・automation用であり、HTML生成元ではありません。

## 基本原則

- 制作はChatGPT Chatから開始し、件名・本文・画像込みHTMLプレビューまでユーザー確認を行う。
- ChatGPTはGitHubの標準block / fragmentを実際に参照し、ユーザーが変更を指示していない箇所を独自再設計しない。
- campaign固有画像は原則として毎campaign Google Driveの元画像から `campaigns/<slug>/images/` へ取り込む。
- campaign固有画像を使用する場合、GitHub取込とGitHub Pages正式URL確認をHTMLプレビューより先に完了する。
- FIX後のHTMLはCodexへ添付・巨大コピペせず、ChatGPTがGitHub作業branchへ `mail.html` として直接保存する。
- Codexは同じ作業branchを引き継ぎ、FIX済み `mail.html` を絶対に変更せず、`campaign.json` 整備・Validation・テストを担当する。
- PR作成は人間の承認ゲート。ChatGPTレビュー後にユーザーがCodex画面からPRを作成し、その後GitHub画面でbaseが `main` か必ず確認する。
- 最新のPR Validationが成功完了する前にauto-mergeを有効化しない。
- GitHub Pages上の公開HTML検証成功時だけZoho Campaigns Draftを自動作成する。Test Email、予約送信、本番送信は自動化しない。

## 制作開始

最初の返答までにGitHubの `AGENTS.md`、本書、base / block / fragment、`config/email_defaults.json` と、Google Driveのセミナー概要・開催情報・登壇者・CTA・今回使用する画像候補を確認する。

最初のユーザー確認では以下を一度に提示する。

- 推奨preset：`standard` / `large`
- CTA本体URL
- UTM案（最低限 `utm_source` / `utm_medium` / `utm_campaign`。`utm_content` は必要時のみ）
- 今回使用するDrive画像のファイル名＋用途
- 必要に応じてblock構成の大枠

最後に「この制作条件で進めてよいですか？」と1回だけ確認する。CTA本体URLなど誤誘導につながる重要情報は推測しない。

制作条件承認後はcampaign画像取込を開始し、並行して今回の主訴求を3〜5案程度提示してユーザーに選んでもらう。

## 画像取込

campaign固有のバナー、登壇者画像、セッション画像、イベント固有ロゴ等は原則 `campaigns/<slug>/images/` に置く。

- 過去campaignに同じ画像があっても通常は再利用しない。
- 同一セミナーの2通目・3通目でもcampaignごとに取り込む。
- 同一campaignの専用 `images/` に今回使用する同一画像が正常に存在する場合のみ再取込不要。
- 配信済みcampaign画像は後続campaignの都合で上書き・削除・リネームしない。
- Delight Hubロゴ、共通署名画像等の固定素材のみ `assets/common/` を再利用する。

Google Drive素材はImage Import Actionsから取得可能な共有状態であることを前提とする。取得できない場合、ChatGPTはHTMLプレビューへ進まずユーザーへ共有設定の確認を依頼する。

ChatGPTは取込前にDrive画像のファイル名と用途をユーザーへ明示する。未取込なら原則として自動取込Issueを作成する。

### Image Import Issueの厳格形式

- Issueタイトルは完全一致で `[automation:image-import]` とする。slugや説明をタイトルへ追記しない。
- Issue本文は既存workflowが要求するJSONのみとし、説明文形式にしない。
- JSONには `campaign_slug` と `images` を含め、各画像に `drive_file_id` と `filename` を指定する。

取込後はIssue結果、repository file、GitHub Pages正式画像URLを確認する。これらが確認できるまで画像取込完了とは扱わない。

### HTMLプレビューとの順序

campaign固有画像を使う通常HTMLプレビューは、画像取込成功・repository file確認・GitHub Pages正式URL確定後に作成する。

以下は禁止する。

- Google Drive直リンクを暫定画像URLとして通常プレビューへ入れる。
- Base64埋め込みを正式画像未確定時の代替プレビューとして使用する。
- 画像取込失敗・未完了のままユーザーへ「見た目確認用HTML」を提示し、FIX工程へ進める。

画像取込に失敗した場合は画像取込を解決してからHTMLプレビュー工程を再開する。

## 標準デザインとHTML制作

- `templates/base/email.html`：メール全体の固定シェル
- `standard` / `large`：初稿構成のpreset
- `templates/seminar/blocks/*.html`：block外側の標準レイアウト
- `templates/seminar/fragments/*.html`：block内部の標準部品
- `campaigns/<slug>/mail.html`：FIX後の最終表示の正本

既存block相当の表現は対応するblock / fragmentのHTML/CSSを原則そのまま使用する。ユーザーから明示的な変更指示がある箇所だけcampaign固有に変更し、他blockまで連鎖的に変更しない。

訴求決定かつ画像正式URL確定後、件名、preheader、本文、CTA、画像、レイアウト、HTMLプレビューまでまとめて作成する。

## HTMLプレビュー前QA

ChatGPTは初稿・修正版をユーザーへ提示する前に最低限以下を確認する。

1. campaign固有画像がすべてGitHub Pages正式URLから表示される。
2. 同一セクション、カード、本文が意図せず重複していない。
3. メール全体が標準シェル幅内に収まり、途中のblockから横幅が広がっていない。
4. 共通署名・ロゴ・宛名・配信対象注意書きが正式設定と一致する。
5. 件名、preheader、CTAラベル、CTA URL/UTMが制作条件と一致する。
6. スマホ幅で明らかな横スクロール、カード崩れ、意図しないレイアウト変更がない。

問題を検知した場合はユーザーへプレビューを出す前に修正する。

## 共通シェル・共通署名

ロゴ、宛名、配信対象注意書き、フッター署名は手入力・記憶・過去の別担当者情報から再構成してはいけない。

`templates/base/email.html` と `config/email_defaults.json` の現在値をそのまま使用する。特に `company_name`、`department`、`contact_name`、`postal_code`、`address`、`email`、`corporate_site_url`、`logo_url`、`contact_image_url`、`zoho_recipient`、`recipient_notice`、`banner_notice` を共通正本とする。

Validationは共通画像だけでなく共通署名の主要文字列も `email_defaults.json` と一致することを検査する。

## HTML FIX → GitHub作業branch

ユーザーが「これでFIX」等の意思表示をした時点のHTMLを表示内容の正本とする。

ChatGPTが `main` からcampaign用作業branchを作成し、FIX済みHTMLを `campaigns/<slug>/mail.html` へ直接保存する。`main` は直接変更しない。保存後、HTMLがそのまま反映され、意図しない他ファイル変更がないことを確認する。

## Codex

ユーザーはChatGPTが指定した同じ作業branchをCodexで選択する。Codexは以下を厳守する。

- `mail.html` はユーザーFIX済みの正本。絶対に変更しない。
- HTML/CSS/文面/レスポンシブ挙動を再設計・再生成しない。
- blocksへ逆変換せず、`build_email.py` から再生成しない。
- 通常変更するcampaign成果物は原則 `campaigns/<slug>/campaign.json` のみ。
- `campaign.json` を現行正式仕様と `mail.html` に合わせ、`content_source: "fixed_html"`、subject、preheader、CTA、UTM、images manifest等を整合させる。
- Validationと必要なテストを実行し、`mail.html` 未変更をhash/diffで確認する。
- 画像binary、template、fragment、script、workflow、config、docs等を通常campaignでは変更しない。
- push、PR作成、`gh pr create` は行わず、実装・テスト・ローカルcommitで停止する。

## Codex後・PR

Codex結果を元Chatへ戻し、ChatGPTは `mail.html` 未変更、`campaign.json`、subject/preheader、CTA/UTM、images、共通署名、Validation、テスト、想定外変更をレビューする。

問題なければChatGPTは「Codex画面からPRを作成してください」と案内する。PR作成後は毎回必ず、GitHub画面でbase branchが `main` になっているか確認し、違えば `main` に変更するよう案内する。

通常campaignの最終PRのbaseは必ず `main` とする。`main` 向けPRには `mail.html` と `campaign.json` の両方が差分として含まれる状態にする。

## PR Validation / auto-merge

`PR Campaign Validation` はunit tests、Python compile、`git diff --check`、placeholder、仮URL、Zoho差し込みタグ、CTA/UTM、campaign画像、共通画像、共通署名、JavaScript、Secretらしき値等を検査する。

pull requestの `edited` イベントもValidation起動対象とする。baseを `main` へ変更した場合、変更後のbase SHAで新しいValidationを実行する。

### auto-merge安全ゲート

- auto-merge有効化は `validate-campaign` jobの成功完了後にのみ実行する。
- Validation job内でauto-mergeを有効化してはいけない。
- auto-mergeは別jobとし、`needs: validate-campaign` で成功完了を待つ。
- auto-merge jobはPRのbaseが `main` の場合のみ実行する。
- base変更後は、変更後baseに対する最新Validation成功を待ってからauto-mergeを有効化する。
- template、workflow、script、config、docs等を含むシステム変更PRは自動マージせず、ユーザーレビューを必須とする。

## Pages検証とZoho Draft

main反映後、`Verify Pages and Create Zoho Draft` は同一commitのGitHub Pages deployment成功を待ち、公開HTML、画像、CTA、件名、campaign識別情報等を検証する。公開検証成功時だけZoho Campaigns Draftを作成する。

自動化の終点はDraft作成。Test Email、予約送信、本番送信、`sendCampaign`系APIは自動化しない。

## 正式フロー

1. ChatGPTがGitHub仕様とDrive素材を確認し、preset・CTA・UTM・使用画像をまとめて提示。
2. ユーザーが制作条件を承認。
3. ChatGPTがcampaign画像取込を開始。
4. 並行してChatGPTが訴求候補を提示し、ユーザーが主訴求を選択。
5. 画像取込成功、repository file、GitHub Pages正式URLを確認。
6. ChatGPTが件名・preheader・本文・HTMLを制作し、内部QA後にプレビュー提示。
7. ユーザーと調整しHTMLをFIX。
8. ChatGPTが作業branchへFIX済み `mail.html` を保存。
9. ユーザーがCodexで同じ作業branchを選択して実行。
10. Codexは `mail.html` を変更せず `campaign.json` 整備・Validation・テスト・commit。
11. Codex結果をChatGPTへ戻しレビュー。
12. ユーザーがCodex画面からPRを作成。
13. GitHubでbaseが `main` か確認し、違えば変更。
14. 変更後baseに対する最新Validation成功。
15. auto-merge。
16. GitHub Pages deployment・公開HTML検証。
17. Zoho Campaigns Draft自動作成。
18. ユーザーがTest Email・本番送信を手動実行。

## セキュリティ

- OAuthのClient ID、Client Secret、Refresh Token、Access Tokenをコード、設定JSON、campaignデータ、HTML、ログへ保存・出力しない。
- 画像は公開を許可された素材だけをGitHub Pagesへ配置する。
- 本番HTMLに仮CTA URL、placeholder、TODO等を残さない。
- Draft作成は送信承認ではない。送信操作はユーザーのみが判断する。
- `EMERGENCY - Recover Zoho Draft Only` は管理者専用のDraft復旧口とする。
