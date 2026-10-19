# メール生成 正式運用ルール

本書はセミナー告知メール制作の正式仕様です。GitHub上の本書を運用仕様の正本とします。

`templates/` は初期HTMLと標準デザインの参照元、ユーザーFIX後の `campaigns/<slug>/mail.html` はそのcampaignの最終表示の正本です。`campaign.json` は管理・Validation・automation用であり、HTML生成元ではありません。

標準の制作担当は **Claude（Claude Chat／Cowork）** です。Claudeの具体的な操作手順は [Claude 実務指示書](CLAUDE_OPERATIONS.md) を参照してください。ChatGPT＋Codexによる従来フローは、[付録：ChatGPT＋Codex代替フロー](#付録chatgptcodex代替フロー) に代替手順として残します。

## 基本原則

- 制作はClaudeから開始し、件名・本文・画像込みHTMLプレビューまでユーザー確認を行う。
- ClaudeはGitHubの標準block / fragmentを実際に参照し、ユーザーが変更を指示していない箇所を独自再設計しない。
- campaign固有画像は原則として毎campaign Google Driveの元画像から `campaigns/<slug>/images/` へ取り込む。
- campaign固有画像を使用する場合、GitHub取込とGitHub Pages正式URL確認をHTMLプレビューより先に完了する。
- ユーザーがHTMLをFIXしたら、Claudeが最新 `main` からcampaign専用作業branchを作成し、FIX済みHTMLを `mail.html` として保存する。FIX後の `mail.html` は再生成・変更しない。
- Claudeが同じ作業branchで `campaign.json` を整備し、Validation・テスト・hash確認を行う。
- ClaudeはユーザーのHTML FIXとPR作成許可を確認してから、REST APIでPRを作成する。PRのbaseは必ず `main` とする。
- ユーザーによるGitHub画面操作やCodexへの受け渡しを、通常工程の必須条件にしない。
- 最新のPR Validationが成功完了する前にauto-mergeを有効化しない。
- GitHub Pages上の公開HTML検証成功時だけZoho Campaigns Draftを自動作成する。Test Email、予約送信、本番送信は自動化しない。

## 制作開始

最初の返答までにGitHubの `AGENTS.md`、本書、[Claude 実務指示書](CLAUDE_OPERATIONS.md)、base / block / fragment、`config/email_defaults.json` と、Google Driveのセミナー概要・開催情報・登壇者・CTA・今回使用する画像候補を確認する。同一セミナーの既存campaignがある場合は、前回の件名・訴求・preset・block構成・CTA/UTM・画像も確認する。

最初のユーザー確認では以下を一度に提示する。

- 推奨preset：`standard` / `large`
- CTA本体URL
- UTM案（最低限 `utm_source` / `utm_medium` / `utm_campaign`。`utm_content` は必要時のみ）
- 今回使用するDrive画像のファイル名＋用途
- campaign slugと `zoho_campaign_name`（[命名規則](#zoho-campaigns管理名称の命名規則)）
- 必要に応じてblock構成の大枠、前回配信との違い

最後に「この制作条件で進めてよいですか？」と1回だけ確認する。CTA本体URLやUTMなど誤誘導につながる重要情報は推測しない。主催企業等から指定されたCTA/UTMはそのまま使用する。

制作条件承認後はcampaign画像取込を開始し、今回の主訴求を3〜5案程度提示してユーザーに選んでもらう。

## 画像取込

campaign固有のバナー、登壇者画像、セッション画像、イベント固有ロゴ等は原則 `campaigns/<slug>/images/` に置く。

- 過去campaignに同じ画像があっても通常は再利用しない。
- 同一セミナーの2通目・3通目でもcampaignごとに取り込む。
- 同一campaignの専用 `images/` に今回使用する同一画像が正常に存在する場合のみ再取込不要。
- 配信済みcampaign画像は後続campaignの都合で上書き・削除・リネームしない。
- Delight Hubロゴ、共通署名画像等の固定素材のみ `assets/common/` を再利用する。

Google Drive素材はImage Import Actionsから取得可能な共有状態であることを前提とする。取得できない場合、ClaudeはHTMLプレビューへ進まずユーザーへ共有設定の確認を依頼する。

Claudeは取込前にDrive画像のファイル名と用途をユーザーへ明示する。

### 標準：Import Drive Images の workflow_dispatch

Claude経由で作成・更新したIssue本文には通信経路による自動署名が付加され、本文をJSONのみにできない。このため、Claude運用の標準は既存の **Import Drive Images**（`.github/workflows/import-drive-images.yml`）を `workflow_dispatch`（ref=`main`）で実行する方式とする。

- 実行前に最新mainのworkflow定義を確認し、入力が `campaign_slug` と `images_json`（各要素 `drive_file_id` / `filename`、1〜20件）であること、commit対象が `campaigns/<slug>/images/` のみであることを確認する。
- 同じ入力で `scripts/import_drive_images.py` のローカル入力検証を通してから実行する。
- workflowはDrive画像を取得・検証し、既存ファイルを置換せず、`github-actions[bot]` としてmainへ画像だけをcommitする。

### 代替：Issue方式（ChatGPT運用時）

- Issueタイトルは完全一致で `[automation:image-import]` とする。slugや説明をタイトルへ追記しない。
- Issue本文は既存workflowが要求するJSONのみとし、説明文形式にしない。JSONには `campaign_slug` と `images` を含め、各画像に `drive_file_id` と `filename` を指定する。
- Issue作成者はrepository admin権限を持つ必要がある。
- Claude経由のIssueは本文に自動署名が付くため、この方式を使わない。

### 取込完了の確認

取込後はActions実行結果、repository file、GitHub Pages deployment、正式画像URLでの表示を確認する。これらが確認できるまで画像取込完了とは扱わない。

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

既存block相当の表現は対応するblock / fragmentのHTML/CSSを原則そのまま使用する。Claudeは `scripts/build_email.py` の正式描画関数で初稿HTMLを生成し、base / block / fragmentを手で書き換えない。ユーザーから明示的な変更指示がある箇所だけcampaign固有に変更し、他blockまで連鎖的に変更しない。

訴求決定かつ画像正式URL確定後、件名、preheader、本文、CTA、画像、レイアウト、HTMLプレビューまでまとめて作成する。

## HTMLプレビュー前QA

Claudeは初稿・修正版をユーザーへ提示する前に `docs/preview-qa-checklist.md` に従い、最低限以下を確認する。

1. campaign固有画像がすべてGitHub Pages正式URLから表示される。
2. 同一セクション、カード、本文が意図せず重複していない。
3. メール全体が標準シェル幅内に収まり、途中のblockから横幅が広がっていない。
4. 共通署名・ロゴ・宛名・配信対象注意書きが正式設定と一致する。
5. 件名、preheader、CTAラベル、CTA URL/UTMが制作条件と一致する。
6. PC幅とスマホ幅で描画し、明らかな横スクロール、カード崩れ、意図しないレイアウト変更がない。

問題を検知した場合はユーザーへプレビューを出す前に修正する。

## 共通シェル・共通署名

ロゴ、宛名、配信対象注意書き、フッター署名は手入力・記憶・過去の別担当者情報から再構成してはいけない。

`templates/base/email.html` と `config/email_defaults.json` の現在値をそのまま使用する。特に `company_name`、`department`、`contact_name`、`postal_code`、`address`、`email`、`corporate_site_url`、`logo_url`、`contact_image_url`、`zoho_recipient`、`recipient_notice`、`banner_notice` を共通正本とする。

Validationは共通画像だけでなく共通署名の主要文字列も `email_defaults.json` と一致することを検査する。

## HTML FIX → 作業branch → campaign.json

ユーザーが「FIX」等の意思表示をした時点のHTMLを表示内容の正本とする。

1. ClaudeはFIX済みHTMLのSHA-256を記録する。
2. 最新 `main` からcampaign専用作業branch（`campaign/<slug>`）を作成する。作業branchのupstreamを `main` にしない。
3. FIX済みHTMLを `campaigns/<slug>/mail.html` へそのまま保存する。HTML/CSS/文面/レスポンシブ挙動を再設計・再生成せず、blocksへ逆変換しない。
4. `campaigns/<slug>/campaign.json` を現行正式仕様と `mail.html` に合わせて整備し、`content_source: "fixed_html"`、`zoho_campaign_name`、subject、preheader、CTA、UTM、images manifest等を整合させる。
5. Validation、unit tests、Python compile、`git diff --check`、`check_pr_scope.py` を実行し、`mail.html` のhashがFIX時と一致することを確認する。
6. 変更が `campaigns/<slug>/mail.html` と `campaigns/<slug>/campaign.json` のみであることを確認し、作業branchへpushする。`main` へは直接pushしない。

画像binary、template、fragment、script、workflow、config、docs等を通常campaignでは変更しない。

## PR作成

- ClaudeはユーザーのHTML FIXとPR作成許可を確認してから、REST APIでPRを作成する。
- 作成前に最新 `main` との差分が上記2ファイルのみであることを確認する。
- 作成後にPR情報を再取得し、baseが `main`、headが作業branchであることを確認する。
- 通常campaignの最終PRのbaseは必ず `main` とする。作業branchをbaseにしたPRを最終PRとして使わない。
- ClaudeはPR作成後にbaseを変更せず、auto-mergeの有効化・手動mergeを行わない。

## PR Validation / auto-merge

`PR Campaign Validation` はunit tests、Python compile、`git diff --check`、placeholder、仮URL、Zoho差し込みタグ、CTA/UTM、campaign画像、共通画像、共通署名、JavaScript、Secretらしき値等を検査する。

pull requestの `edited` イベントもValidation起動対象とする。baseを `main` へ変更した場合、変更後のbase SHAで新しいValidationを実行する。

### auto-merge安全ゲート

- auto-merge有効化は `validate-campaign` jobの成功完了後にのみ実行する。
- Validation job内でauto-mergeを有効化してはいけない。
- auto-mergeは別jobとし、`needs: validate-campaign` で成功完了を待つ。
- auto-merge jobはPRのbaseが `main` の場合のみ実行する。
- base変更後は、変更後baseに対する最新Validation成功を待ってからauto-mergeを有効化する。
- auto-mergeの対象は、`scripts/check_pr_scope.py` が `eligible=true` と判定した単一campaignの `campaign.json` / `mail.html` 変更だけとする。
- template、workflow、script、config、docs等を含むシステム変更PRは自動マージせず、ユーザーレビュー後に手動mergeする。

## Pages検証とZoho Draft

main反映後、`Verify Pages and Create Zoho Draft` は同一commitのGitHub Pages deployment成功を待ち、公開HTML、画像、CTA、件名、campaign識別情報等を検証する。公開検証成功時だけZoho Campaigns Draftを作成する。

自動化の終点はDraft作成。Test Email、予約送信、本番送信、`sendCampaign`系APIは自動化しない。

Claudeは最終報告で、Validation・auto-merge・Pages・Draft作成の結果と、作成されたDraftの `zoho_campaign_name` を報告する。

## Zoho Campaigns管理名称の命名規則

新規campaignの `zoho_campaign_name` は次の形式に統一する。

```text
YYYYMMDD配信_YYYYMMDD開催N回目_セミナータイトル
```

例：

```text
20261019配信_20261020開催2回目_空室税時代の到来_売却案件を利益に変える4つのヒント
```

- 配信日：そのメルマガの予定配信日。
- 開催日：セミナー本番の開催日。
- N回目：同一セミナーに対する告知メルマガの通算配信回数。
- セミナータイトル：正式な管理用タイトル。
- 配信日・開催日・回数・タイトルが不明な場合は推測せず確認する。
- メール件名（`subject`）とZoho管理名称（`zoho_campaign_name`）は別項目として扱う。
- 過去campaignの管理名称は変更しない。本規則は本書の反映後に作成する新規campaignから適用する。

## 正式フロー

1. ClaudeがGitHub仕様とDrive素材を確認し、preset・CTA・UTM・使用画像・管理名称等をまとめて提示。ユーザーが制作条件を承認。
2. Claudeが `Import Drive Images` を `workflow_dispatch` で実行し、Actions結果・repository file・Pages正式URLを確認。
3. Claudeが主訴求3〜5案を提示し、ユーザーが選択。
4. Claudeが正式なbase・block・fragmentでHTMLを生成し、PC/SPのプレビュー前QA後にプレビューを提示。
5. ユーザーがHTMLをFIX。
6. Claudeが最新 `main` からcampaign専用branchを作成し、FIX済み `mail.html` を保存。
7. Claudeが `campaign.json` を整備し、Validation・テスト・hash確認を実行して作業branchへpush。
8. ClaudeがユーザーのPR作成許可を確認し、REST APIでPRを作成してbase=`main` を確認。
9. GitHub Actionsが最新Validation成功後にauto-mergeし、GitHub Pages公開・公開HTML検証・Zoho Campaigns Draft作成。Claudeが結果を確認・報告。
10. ユーザーがZoho CampaignsでTest Email・配信設定・本番送信を手動実行。

## セキュリティ

- OAuthのClient ID、Client Secret、Refresh Token、Access Tokenをコード、設定JSON、campaignデータ、HTML、ログへ保存・出力しない。
- 画像は公開を許可された素材だけをGitHub Pagesへ配置する。
- 本番HTMLに仮CTA URL、placeholder、TODO等を残さない。
- Draft作成は送信承認ではない。送信操作はユーザーのみが判断する。
- `EMERGENCY - Recover Zoho Draft Only` は管理者専用のDraft復旧口とする。

## 付録：ChatGPT＋Codex代替フロー

Claudeを使用できない場合に限り、従来のChatGPT＋Codexフローを代替手順として使用できる。上記の画像・HTML・共通署名・Validation・auto-merge・Draft・命名規則はそのまま適用する。

- ChatGPTが制作条件確認、画像取込（Issue方式は本文JSONのみで起票できる場合に限る。できない場合はworkflow_dispatch方式）、訴求決定、HTMLプレビュー、FIX後の作業branchへの `mail.html` 保存を担当する。
- ユーザーは同じ作業branchをCodexで選択する。Codexは `mail.html` を絶対に変更せず、`campaign.json` 整備・Validation・テスト・ローカルcommitまでで停止する（push、PR作成、`gh pr create` は行わない）。
- Codex結果をChatGPTがレビューし、ユーザーOK後にユーザーがCodex画面からPRを作成する。PR作成後、GitHub画面でbaseが `main` か確認し、違えば `main` に変更する。
- `main` 向けPRには `mail.html` と `campaign.json` の両方が差分として含まれる状態にする。
