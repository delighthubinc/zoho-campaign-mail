# AI エージェント実務ルール

メール生成の正式ルールは `docs/MAIL_GENERATION_RULES.md` を最優先で参照する。標準の制作担当はClaude（Claude Chat／Cowork）で、具体的な操作手順は `docs/CLAUDE_OPERATIONS.md` に従う。ChatGPT＋Codexは代替フローとして `docs/MAIL_GENERATION_RULES.md` の付録に従う。

## 基本

- セミナー告知メールは `templates/base/email.html`、`templates/seminar/blocks/*.html`、`templates/seminar/fragments/*.html` を標準部品として使い、毎回ゼロから独自デザインを作らない。
- 新規セミナーは `template_type: seminar`、presetは `standard` / `large` を初期構成案として使える。FIX後の表示正本は `campaigns/<slug>/mail.html`。
- `campaign.json` はcampaign識別、Zoho管理名、subject、preheader、CTA/UTM、画像manifest等の管理・Validation・automation用で、HTML生成元ではない。通常 `content_source` は `fixed_html`。
- `scripts/build_email.py` は初期HTML生成・標準デザイン参照・開発テスト用途。FIX済み `mail.html` を再生成しない。
- 開催日時、CTA本体URL、UTM、配信日、配信回数等の重要情報は推測しない。

## Claude制作（標準）

- 制作開始時にGitHubで正式仕様・標準デザイン、Google Driveで今回のセミナー情報・素材を確認する。
- 最初の返答でpreset、CTA、UTM、今回使用するDrive画像のファイル名＋用途、campaign slug、`zoho_campaign_name` をまとめて提示し、制作条件を1回で確認する。
- 制作条件承認後、既存の `Import Drive Images` workflowを `workflow_dispatch`（ref=`main`）で実行してcampaign固有画像を取り込み、主訴求を3〜5案程度提案してユーザーに選んでもらう。Claude経由のIssue本文には自動署名が付くため、Issue方式の画像取込は使わない。
- campaign固有画像を使うHTMLプレビューは、画像取込成功・repository file確認・GitHub Pages正式URL確定後に作成する。
- 訴求決定後は件名、preheader、本文、CTA、画像、HTMLプレビューまで一気に作成する。
- 既存block相当の表現は対応するblock / fragmentの実際のHTML/CSSを原則そのまま使用する。ユーザーから明示的な変更指示がない箇所を独自再設計しない。
- ユーザーがFIXしたら、Claudeが最新 `main` からcampaign専用作業branchを作成し、FIX済みHTMLを `campaigns/<slug>/mail.html` へ保存し、`campaign.json` 整備・Validation・テスト・hash確認を行ってpushする。
- ClaudeはユーザーのHTML FIXとPR作成許可を確認してからREST APIでPRを作成し、base=`main` を確認する。auto-merge有効化・手動merge・base変更は行わない。

## HTMLプレビューQA

ユーザーへ初稿・修正版HTMLプレビューを提示する前に、最低限以下を確認する。

- campaign固有画像がすべてGitHub Pages正式URLから表示されること。
- Google Drive直リンクやBase64埋め込みを通常プレビューの代替に使用していないこと。
- 同一セクション、カード、本文が意図せず重複していないこと。
- メール全体が標準シェル幅内に収まり、途中から横幅が広がっていないこと。
- 共通署名・ロゴ・宛名・注意書きが `config/email_defaults.json` / base template と一致すること。
- 件名、preheader、CTAラベル、CTA URL/UTMが今回の制作条件と一致すること。
- PC幅・スマホ幅で明らかな横スクロール、カード崩れ、意図しない縦並び等がないこと。

QAで問題を見つけた場合はユーザー確認へ進む前に修正する。

## 共通シェル・署名

- ロゴ、宛名、配信対象注意書き、フッター署名は手入力・記憶・過去の別担当者情報から再構成しない。
- `templates/base/email.html` と `config/email_defaults.json` の現在値をそのまま使用する。
- `company_name`、`department`、`contact_name`、`postal_code`、`address`、`email`、`corporate_site_url`、`logo_url`、`contact_image_url`、`zoho_recipient`、`recipient_notice`、`banner_notice` は共通正本として扱う。
- 担当者名、部署、住所、メール、プロフィール画像等をcampaign都合で変更しない。
- Validationは共通画像だけでなく共通署名の主要文字列も `email_defaults.json` と一致することを検査する。

## 画像

- Delight Hubロゴ、共通署名画像等の固定素材だけ `assets/common/` を再利用する。
- campaign固有画像は過去campaignとの再利用判定をせず、各campaignごとにGoogle Driveの元画像から `campaigns/<slug>/images/` へ取り込む。同一campaignに同一画像が正常に存在する場合のみ再取込不要。
- Google Drive素材はImage Import Actionsから取得可能な共有状態であることを前提とする。取得できない場合はHTMLプレビューへ進まず、ユーザーへ共有設定の確認を依頼する。
- 取込前または取込済み判断時に、対象Driveファイル名と用途を必ずユーザーへ明示する。
- 取込完了後はActions結果、repository file、GitHub Pages正式URLを確認する。
- campaign固有画像の正式GitHub Pages URLが確定する前に通常のHTMLプレビューを作成・FIXしない。
- Google Drive直リンクやBase64埋め込みを、画像未取込時の暫定HTMLプレビューとして使用しない。
- 通常campaignの作業branch・PRで画像binaryを追加・変更・コピーしない。正式画像URLが未確定ならfail-closedで停止する。

## 通常campaignの変更範囲

- `mail.html` はユーザーFIX済みの正本。FIX後は絶対に変更しない。
- HTML/CSS/文面/レスポンシブ挙動を再解釈・再設計・再生成しない。blocksへ逆変換せず、`build_email.py` から再生成しない。
- 通常変更するcampaign成果物は `campaigns/<slug>/mail.html` と `campaigns/<slug>/campaign.json` のみ。
- 画像binary、template、fragment、script、workflow、config、docs等を通常campaignでは変更しない。
- Validation、unit tests、Python compile、`git diff --check` 等を実行し、`mail.html` 未変更もhashで確認する。
- `main` へ直接pushしない。

## Zoho Campaigns管理名称

新規campaignの `zoho_campaign_name` は `YYYYMMDD配信_YYYYMMDD開催N回目_セミナータイトル` とする（例：`20261019配信_20261020開催2回目_空室税時代の到来_売却案件を利益に変える4つのヒント`）。定義と例外は `docs/MAIL_GENERATION_RULES.md` の命名規則に従う。過去campaignの管理名称は変更しない。

## 自動化

- `PR Campaign Validation` はpull requestの `edited` イベントでも新規実行する。base変更時にClose→Reopenや古いrunの再実行を必要としない。
- auto-merge有効化は `validate-campaign` jobが成功完了した後の別jobでのみ行う。Validation実行中にmergeを有効化しない。
- auto-merge jobはPRのbaseが `main` の場合だけ実行する。base変更後は変更後のbase SHAに対する最新Validation成功を待ってからauto-mergeを有効化する。
- 通常campaign限定PRは上記Validation成功後、GitHub Appがauto-mergeする。
- template、workflow、script、config、docs等を含むシステム変更PRは自動マージせずユーザーレビュー待ちとする。
- main反映後、GitHub Pages deploymentと公開HTML・画像・CTA等の検証が成功した場合だけZoho Campaigns Draftを作成する。
- 自動化の終点はDraft作成。Test Email、予約、本番送信、`sendCampaign`系APIは実装・実行しない。
- OAuthのClient ID、Client Secret、Refresh Token、Access Tokenをコード、設定JSON、HTML、ログ、artifact、commitへ保存しない。
- `EMERGENCY - Recover Zoho Draft Only` は管理者専用のDraft復旧口とする。

## 正式フロー要約

Claudeが制作条件確認
→ ユーザー承認
→ Claudeが `Import Drive Images` をworkflow_dispatchで実行し、Actions結果・repository file・Pages正式URLを確認
→ 主訴求決定
→ Claudeが件名＋HTML制作・PC/SP内部QA・調整
→ ユーザーFIX
→ Claudeが作業branchへ `mail.html` 保存・`campaign.json` 整備・検証・push
→ ユーザーのPR作成許可
→ ClaudeがREST APIでPR作成・base=`main` 確認
→ 最新Validation成功
→ auto-merge
→ GitHub Pages
→ 公開検証
→ Zoho Campaigns Draft
→ ユーザーがTest Email・本番送信を手動実行
