# AI / Codex 実務ルール

メール生成の正式ルールは `docs/MAIL_GENERATION_RULES.md` を最優先で参照する。

## 基本

- セミナー告知メールは `templates/base/email.html`、`templates/seminar/blocks/*.html`、`templates/seminar/fragments/*.html` を標準部品として使い、毎回ゼロから独自デザインを作らない。
- 新規セミナーは `template_type: seminar`、presetは `standard` / `large` を初期構成案として使える。FIX後の表示正本は `campaigns/<slug>/mail.html`。
- `campaign.json` はcampaign識別、Zoho管理名、subject、preheader、CTA/UTM、画像manifest等の管理・Validation・automation用で、HTML生成元ではない。通常 `content_source` は `fixed_html`。
- `scripts/build_email.py` は初期HTML生成・標準デザイン参照・開発テスト用途。FIX済み `mail.html` を再生成しない。

## ChatGPT制作

- 制作開始時にGitHubで正式仕様・標準デザイン、Google Driveで今回のセミナー情報・素材を確認する。
- 最初の返答でpreset、CTA、UTM、今回使用するDrive画像のファイル名＋用途をまとめて提示し、制作条件を1回で確認する。
- 制作条件承認後、主訴求を3〜5案程度提案してユーザーに選んでもらう。
- 訴求決定後は件名、preheader、本文、CTA、画像、HTMLプレビューまで一気に作成する。
- 既存block相当の表現は対応するblock / fragmentの実際のHTML/CSSを原則そのまま使用する。ユーザーから明示的な変更指示がない箇所を独自再設計しない。
- campaign固有の変更はユーザーが指示した箇所だけに限定する。

## 共通シェル・署名

- ロゴ、宛名、配信対象注意書き、フッター署名は手入力・記憶・過去の別担当者情報から再構成しない。
- `templates/base/email.html` と `config/email_defaults.json` の現在値をそのまま使用する。
- `company_name`、`department`、`contact_name`、`postal_code`、`address`、`email`、`corporate_site_url`、`logo_url`、`contact_image_url`、`zoho_recipient`、`recipient_notice`、`banner_notice` は共通正本として扱う。
- 担当者名、部署、住所、メール、プロフィール画像等をcampaign都合で変更しない。
- Validationは共通画像だけでなく共通署名の主要文字列も `email_defaults.json` と一致することを検査する。

## 画像

- Delight Hubロゴ、共通署名画像等の固定素材だけ `assets/common/` を再利用する。
- campaign固有画像は過去campaignとの再利用判定をせず、各campaignごとにGoogle Driveの元画像から `campaigns/<slug>/images/` へ取り込む。同一campaignに同一画像が正常に存在する場合のみ再取込不要。
- ChatGPTは取込前または取込済み判断時に、対象Driveファイル名と用途を必ずユーザーへ明示する。
- 未取込なら原則ChatGPTが `[automation:image-import]` Issueを作成し、Actionsで取り込む。完了後はIssue結果、repository file、GitHub Pages URLを確認する。
- Codexは画像binaryを追加・変更・コピーしない。正式画像URLが未確定ならfail-closedで停止する。

## FIX済みHTMLの受け渡し

- FIX後のHTMLをCodexへ添付・巨大コピペしない。
- ユーザーがHTMLをFIXしたら、ChatGPTが `main` からcampaign用作業branchを作成し、FIX済みHTMLを `campaigns/<slug>/mail.html` へ直接保存する。
- ChatGPTは `main` を直接変更しない。保存後、FIX済みHTMLがそのまま反映され、意図しない他ファイル変更がないことを確認する。

## Codex通常campaignルール

ユーザーはChatGPTが指定した同じ作業branchをCodexで選択する。Codexは以下を厳守する。

- `mail.html` はユーザーFIX済みの正本。絶対に変更しない。
- HTML/CSS/文面/レスポンシブ挙動を再解釈・再設計・再生成しない。
- blocksへ逆変換せず、`build_email.py` から再生成しない。
- 通常変更するcampaign成果物は原則 `campaigns/<slug>/campaign.json` のみ。
- `campaign.json` を現行正式仕様と `mail.html` に合わせ、`content_source: "fixed_html"`、subject、preheader、CTA、UTM、images manifest等を整合させる。
- 画像binary、template、fragment、script、workflow、config、docs等を通常campaignでは変更しない。
- Validation、unit tests、Python compile、`git diff --check` 等を実行し、`mail.html` 未変更もhash/diffで確認する。
- push、PR作成、`gh pr create` は行わず、実装・テスト・ローカルcommitで停止する。
- 完了後、変更ファイル、主要設定、`mail.html` 未変更、Validation/テスト結果、commit ID、想定外変更の有無を報告する。

## Codex後・PR

- Codex結果をChatGPTへ戻し、ChatGPTが `mail.html` 未変更、`campaign.json`、subject/preheader、CTA/UTM、images、共通署名、Validation、テスト、想定外変更をレビューする。
- 問題なければChatGPTが「PRを作成してよいですか？」と確認する。
- ユーザーが明示OKした後、**ChatGPTがCodexのhead branchから `main` 向けPRを直接作成する。Codex画面のPRボタンは通常campaignでは使わない。**
- PR作成直後にbaseが `main` であること、mainとの差分に `mail.html` と `campaign.json` の両方が含まれることを確認する。
- PR作成は意図的な人間の承認ゲートである。

## 自動化

- `PR Campaign Validation` はpull requestの `edited` イベントでも新規実行する。base変更時にClose→Reopenや古いrunの再実行を必要としない。
- 通常campaign限定PRはrequired checks成功後、GitHub Appがauto-mergeする。
- template、workflow、script、config、docs等を含むシステム変更PRは自動マージせずユーザーレビュー待ちとする。
- main反映後、GitHub Pages deploymentと公開HTML・画像・CTA等の検証が成功した場合だけZoho Campaigns Draftを作成する。
- 自動化の終点はDraft作成。Test Email、予約、本番送信、`sendCampaign`系APIは実装・実行しない。
- OAuthのClient ID、Client Secret、Refresh Token、Access Tokenをコード、設定JSON、HTML、ログ、artifact、commitへ保存しない。
- `EMERGENCY - Recover Zoho Draft Only` は管理者専用のDraft復旧口とする。

## 正式フロー要約

Chatで制作条件確認
→ 訴求決定
→ 件名＋HTML制作・調整
→ ユーザーFIX
→ ChatGPTがGitHub作業branchへ `mail.html` 保存
→ Codexが同branchで `campaign.json` 整備・検証（`mail.html` 変更禁止）
→ ChatGPTレビュー
→ ユーザーOK
→ ChatGPTがCodex head branchからmain向けPR作成
→ Validation
→ auto-merge
→ GitHub Pages
→ 公開検証
→ Zoho Campaigns Draft
→ ユーザーがTest Email・本番送信を手動実行
