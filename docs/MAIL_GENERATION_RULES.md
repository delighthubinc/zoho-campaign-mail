# メール生成 正式運用ルール

本書は、セミナー告知メール制作に関して人間・ChatGPT・Codexが共通で参照する正式仕様です。GitHub上の本書を運用仕様の正本とします。

`templates/` は初期HTMLと標準デザインの参照元、ユーザーFIX後の `campaigns/<slug>/mail.html` はそのcampaignの最終表示の正本です。`campaign.json` は管理・Validation・automation用であり、HTML生成元ではありません。

## 基本原則

- 制作はChatGPT Chatから開始し、件名・本文・HTMLプレビューまでユーザー確認を行う。
- ChatGPTはGitHubの標準block / fragmentを実際に参照し、ユーザーが変更を指示していない箇所を独自再設計しない。
- campaign固有画像は、過去campaign画像との突合・再利用を通常フローで行わず、原則として毎campaign Google Driveの元画像から `campaigns/<slug>/images/` へ取り込む。
- FIX後のHTMLはファイル添付や巨大コピペでCodexへ渡さない。ChatGPTがGitHubの作業branchへ `mail.html` として直接保存する。
- Codexは同じ作業branchを引き継ぎ、FIX済み `mail.html` を絶対に変更せず、`campaign.json` の整備・Validation・テストを担当する。
- PR作成は意図的な人間の承認ゲート。最終PRのbaseは必ず `main` とする。
- GitHub Pages上の公開HTML検証が成功した場合だけZoho Campaigns Draftを自動作成する。
- Test Email、予約送信、本番送信は自動化しない。

## 制作開始

ユーザーがセミナーメルマガ制作を依頼したら、最初の返答までに以下を確認する。

### GitHub：仕様・標準デザイン

- `docs/MAIL_GENERATION_RULES.md`
- `AGENTS.md`
- `templates/base/email.html`
- `templates/seminar/blocks/`
- `templates/seminar/fragments/`
- 必要に応じて既存campaign・関連テンプレート

### Google Drive：今回の情報・素材

セミナー概要、開催情報、登壇者、CTA、今回使用する画像候補を確認する。過去メールを参照できる場合は参考にしてよいが、過去配信確認のためだけに制作を止めない。

### 最初のユーザー確認

最初の返答で、以下を一度に提示する。

- 推奨preset：`standard` / `large`
- CTA本体URL
- UTM案（最低限 `utm_source` / `utm_medium` / `utm_campaign`。`utm_content` は必要時のみ）
- 今回使用するDrive画像のファイル名＋用途
- 必要に応じてblock構成の大枠

最後に「この制作条件で進めてよいですか？」と1回だけ確認する。preset、UTM、画像を項目ごとに細切れ承認しない。CTA本体URLなど誤誘導につながる重要情報は推測しない。

## 訴求決定

制作条件が承認されたら、HTML制作前に今回の主訴求を3〜5案程度提示し、ユーザーに選んでもらう。

例：
- イベント全体の豪華さ・大型感
- 基調講演
- 市場動向・最新情報
- 1日でまとめて学べるメリット
- 限定感・定員・申込期限

過去配信の訴求が把握できる場合は「前回は○○だったため今回は△△もおすすめ」のように提案してよい。

訴求が決まったら、追加の細かな承認を挟まず、件名、preheader、本文、CTA、画像、レイアウト、HTMLプレビューまで一気に作成する。

## 標準デザイン

- `templates/base/email.html`：メール全体の固定シェル
- `standard` / `large`：初稿構成のpreset
- `templates/seminar/blocks/*.html`：block外側の標準レイアウト
- `templates/seminar/fragments/*.html`：block内部の標準部品
- `campaigns/<slug>/mail.html`：FIX後、そのcampaignの最終表示の正本

既存blockに該当する表現を使う場合、対応するblock / fragmentのHTML/CSSを原則そのまま使用する。block名や概念だけを参考に同用途のデザインを独自に作り直さない。

例：
- 開催概要：`event_info.html` + `section_heading.html` + `event_info_row.html`
- 基調講演：`keynote_speakers.html` + speaker関連fragment
- セッション：`session_cards.html` + `session_card.html` 等
- CTA：`cta.html`

ユーザーから明示的な変更指示がある場合のみ、そのcampaignの完成HTML上でカスタマイズしてよい。変更指示を受けていない他block / fragmentまで連鎖的に変更しない。

「今後もこれを標準にしたい」とユーザーが明示した場合だけ、通常campaign制作とは分離したtemplate / system変更として扱う。

## 画像取込

### campaign固有画像

バナー、登壇者画像、セッション画像、イベント固有ロゴ等は原則 `campaigns/<slug>/images/` に置く。

- 過去campaignに同じ画像があっても通常は再利用しない。
- 同一セミナーの2通目・3通目でもcampaignごとに取り込む。
- 同一campaignの専用 `images/` に今回使用する同一画像が既に正常に存在する場合のみ再取込不要。
- 配信済みcampaignの画像は後続campaignの都合で上書き・削除・リネームしない。

### 共通画像

Delight Hubロゴ、共通署名プロフィール画像等、全campaign共通の固定素材のみ `assets/common/` を再利用する。会社情報、担当者、宛名、注意書き等は `config/email_defaults.json` で管理する。

### 取込方法

ChatGPTは取込前に、今回使用するDrive画像のファイル名と用途をユーザーへ明示する。

未取込の場合は原則ChatGPTが `[automation:image-import]` Issueを作成し、GitHub Actionsでcampaign専用ディレクトリへ取り込む。完了後はIssue結果、repository file、GitHub Pages URLを確認する。手動 `Import Drive Images` workflowは自動経路が技術的に失敗した場合のfallbackに限る。

Codexは画像binaryを追加・変更・コピーしない。正式画像URLが未確定ならfail-closedで停止する。

## HTML FIX → GitHub作業branch

ユーザーが「これでFIX」等の意思表示をした時点のHTMLを、そのcampaignの表示内容の正本とする。

FIX後はChatGPTが `main` からcampaign用作業branchを作成し、FIX済みHTMLを

`campaigns/<slug>/mail.html`

へ直接保存する。`main` は直接変更しない。

保存後、FIX済みHTMLがそのまま反映されていること、意図しない他ファイル変更がないことを確認する。

## 成果物の役割

- `mail.html`：メール本文、デザイン、CSS、レスポンシブ挙動を含む表示内容の唯一の正本。
- `campaign.json`：`campaign_slug`、`subject`、`zoho_campaign_name`、CTA/UTM、画像manifest等の管理・Validation・automation用。HTML生成元ではない。
- `content_source`：通常campaignは `fixed_html`。
- `scripts/build_email.py`：初期HTML生成、標準デザイン参照、開発・テスト用途。FIX済み `mail.html` の再生成一致は要求しない。

## Codex

ChatGPTはCodex用プロンプトを作成し、ユーザーはChatGPTが指定した同じ作業branchをCodexで選択して実行する。

Codexへの必須指示：

- `mail.html` はユーザーFIX済みの正本。絶対に変更しない。
- HTML/CSS/文面/レスポンシブ挙動を再設計・再生成しない。
- blocksへ逆変換しない。
- `build_email.py` から再生成しない。
- `campaign.json` を現行正式仕様と `mail.html` に合わせて整備する。
- `content_source: "fixed_html"` を維持する。
- subject / preheader / CTA / UTM / images等を `mail.html` と整合させる。
- Validationと必要なテストを実行する。
- 画像binary、template、fragment、script、workflow、docs等を通常campaignでは変更しない。
- push、PR作成、`gh pr create` は行わず、実装・テスト・ローカルcommitで停止する。
- 完了後、変更ファイル、主要設定、`mail.html` 未変更、Validation/テスト結果、commit ID、想定外変更の有無を報告する。

通常、Codexが変更するcampaign成果物は `campaigns/<slug>/campaign.json` のみ。`mail.html` はChatGPTがすでに作業branchへ保存済みであり、Codexの実装対象ではない。

## Codex後・PR

Codex完了後、ユーザーはCodex回答を元Chatへ貼る。ChatGPTは以下をレビューする。

- `mail.html` がFIX後から変更されていないこと
- `campaign.json`
- subject / preheader
- CTA / UTM
- images
- 不要な変更
- Validation / テスト

問題なければユーザーへPR作成可を案内する。ユーザーOK後、ユーザーがCodex画面からPRを作成する。

**最終PRのbaseは必ず `main`。**

作業branchをbaseにしたPRを通常campaignの最終PRとして使用しない。`PR Campaign Validation` は `main` との差分として `campaign.json` と `mail.html` の両方を検証する。

PR作成は本番自動フローへ流す前の意図的な人間の承認ゲートである。

## PR Validation / auto-merge

`PR Campaign Validation` は全unit test、Python compile、`git diff --check`、placeholder、仮URL、Zoho差し込みタグ、CTA/UTM、campaign画像、共通画像、JavaScript、Secretらしき値等を検査する。campaign.jsonからのHTML再生成一致は検証しない。

通常campaign限定PRはrequired checks成功後にGitHub Appがauto-mergeする。template、workflow、script、config、docs、複数campaign、対象外path等を含むシステム変更PRは自動マージせず、ユーザーレビューを必須とする。

## Pages検証とZoho Draft

main反映後、`Verify Pages and Create Zoho Draft` は同一commitのGitHub Pages deployment成功を待ち、公開HTML、画像、CTA、件名、campaign識別情報等を検証する。

公開検証成功時だけ、`campaign.json` と `config/zoho.json` を使ってZoho Campaigns Draftを作成する。二重作成防止はledger / markerとworkflow concurrencyでfail-closedに管理する。

OAuth値はRepository SecretsからDraft作成stepだけへ渡し、tokenやsecretをコード、JSON、HTML、ログ、artifactへ出さない。

自動化の終点はZoho Campaigns Draft作成。Test Email、予約送信、本番送信、`sendCampaign`系APIは自動化しない。

## 正式フロー

1. ChatGPTがGitHub仕様とDrive素材を確認し、preset・CTA・UTM・使用画像をまとめて提示する。
2. ユーザーが制作条件を承認する。
3. ChatGPTが訴求候補を提示し、ユーザーが主訴求を選ぶ。
4. ChatGPTが件名・preheader・本文・HTMLを一気に制作し、ユーザーと調整する。
5. campaign固有画像を今回campaign専用 `images/` へ取り込み、正式URLを使用する。
6. ユーザーがHTMLをFIXする。
7. ChatGPTが作業branchを作り、FIX済みHTMLを `mail.html` へ直接保存する。
8. ChatGPTがCodex用プロンプトを作る。
9. ユーザーがCodexで同じ作業branchを選び、プロンプトを実行する。
10. Codexは `mail.html` を変更せず、`campaign.json` 整備、Validation、テスト、commitまで行う。
11. Codex結果をChatGPTへ戻し、ChatGPTがレビューする。
12. ユーザーOK後、ユーザーがCodex画面から **main向けPR** を作成する。
13. `PR Campaign Validation` 成功後、GitHub Appがauto-mergeする。
14. main反映後、GitHub Pages deploymentと公開HTML検証を行う。
15. 公開検証成功時だけZoho Campaigns Draftを自動作成する。
16. ユーザーがZoho CampaignsでTest Emailを手動実行する。
17. 問題がなければユーザーが本番送信を手動実行する。

承認・自動化境界は次のとおり。

**ChatでHTML FIX → ChatがGitHub作業branchへ `mail.html` 保存 → Codexが同branchで `campaign.json` 整備・検証 → ChatGPTレビュー → ユーザーOK → Codex画面からmain向けPR → Validation → auto-merge → Pages → Verify Pages and Create Zoho Draft → Zoho Draft作成**

## セキュリティ

- OAuthのClient ID、Client Secret、Refresh Token、Access Tokenをコード、設定JSON、campaignデータ、HTML、ログへ保存・出力しない。
- 画像は公開を許可された素材だけをGitHub Pagesへ配置する。
- 本番HTMLに仮CTA URL、placeholder、TODO等を残さない。
- Draft作成は送信承認ではない。送信操作はユーザーのみが判断する。
- 障害時の `EMERGENCY - Recover Zoho Draft Only` は管理者専用のDraft復旧口とし、Zoho UIとledgerを確認した場合だけ使用する。
