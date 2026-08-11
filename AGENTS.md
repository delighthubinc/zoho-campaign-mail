# AI / Codex 実務ルール

メール生成の正式ルールは `docs/MAIL_GENERATION_RULES.md` を最優先で参照する。

## 基本

- セミナー告知メールは毎回ゼロから独自デザインを作らず、`templates/base/email.html`、`templates/seminar/blocks/*.html`、`templates/seminar/fragments/*.html` を標準部品として使う。
- 新規セミナーは `template_type: seminar`、presetは `standard` / `large` を初期構成案として使える。presetやblocksは初稿用であり、FIX後の最終表示の正本ではない。
- ユーザーがFIXした `campaigns/<slug>/mail.html` が、そのcampaignの表示内容の唯一の正本。
- `campaign.json` はcampaign識別、Zoho管理名、subject、preheader、CTA/UTM、画像manifest等の管理・Validation・automation用であり、HTML生成元ではない。通常campaignの `content_source` は `fixed_html`。
- `scripts/build_email.py` は初期HTML生成、標準デザイン参照、開発・テスト用途。FIX済み `mail.html` を再生成して一致させるためには使わない。

## ChatGPT制作

- 制作開始時にGitHubで正式仕様・標準デザインを確認し、Google Driveで今回のセミナー情報・素材を確認する。
- 最初の返答で、preset、CTA、UTM、今回使用するDrive画像のファイル名＋用途をまとめて提示し、制作条件を1回で確認する。presetやUTMを項目ごとに細切れ承認しない。
- 制作条件承認後、今回の主訴求を3〜5案程度提案し、ユーザーに選んでもらう。過去配信の訴求を把握できる場合は参考にしてよいが、確認のためだけに制作を止めない。
- 訴求決定後は、件名、preheader、本文、CTA、画像、HTMLプレビューまで一気に作成する。
- 既存block相当の表現では対応するblock / fragmentの実際のHTML/CSSを原則そのまま使用する。ユーザーから明示的な変更指示がない箇所を独自に再設計しない。
- ユーザーの個別指示による文面、レイアウト、CSS、レスポンシブ変更はcampaignの完成HTML上で反映してよい。変更指示を受けていない他blockまで連鎖的に変更しない。
- ユーザーが「今後もこれを標準にしたい」と明示した場合だけ、通常campaign制作とは分けたtemplate / system変更として扱う。

## 画像

- Delight Hubロゴ、共通署名画像等の固定素材だけ `assets/common/` を再利用する。
- バナー、登壇者、セッション画像等のcampaign固有画像は、過去campaignに同じ画像があっても通常は再利用せず、各campaignごとにGoogle Driveの元画像から `campaigns/<slug>/images/` へ取り込む。
- 同一campaignの専用 `images/` に今回使用する同一画像が正常に存在する場合のみ再取込不要。
- ChatGPTは取込前または取込済み判断時に、対象Driveファイル名と用途を必ずユーザーへ明示する。
- 未取込なら原則ChatGPTが `[automation:image-import]` Issueを作成し、Actionsで取り込む。完了後はIssue結果、repository file、GitHub Pages URLを確認する。
- CodexはPNG、JPG/JPEG、GIF、WebPその他のbinary fileを追加・変更・コピーしない。正式画像URLが未確定ならfail-closedで停止する。

## FIX済みHTMLの受け渡し

- FIX後のHTMLファイルをCodexへ添付しない。HTML全文をCodexチャットへコピペして受け渡すことも通常フローでは行わない。
- ユーザーがHTMLをFIXしたら、ChatGPTが `main` からcampaign用作業branchを作成し、FIX済みHTMLを `campaigns/<slug>/mail.html` へ直接保存する。
- ChatGPTは `main` を直接変更しない。
- 保存後、FIX済みHTMLがそのまま反映されていること、意図しない他ファイル変更がないことを確認する。

## Codex通常campaignルール

ユーザーはChatGPTが指定した**同じ作業branch**をCodexで選択して実行する。

Codexは以下を厳守する。

- `campaigns/<slug>/mail.html` はChatGPT上でユーザー確認・FIX済みの正本。**絶対に変更しない。**
- HTML/CSS/文面/レスポンシブ挙動を再解釈、再設計、再生成しない。
- FIX済みHTMLをblocksへ逆変換しない。
- `build_email.py` から `mail.html` を再生成しない。
- 通常変更するcampaign成果物は原則 `campaigns/<slug>/campaign.json` のみ。
- `campaign.json` を現行正式仕様とFIX済み `mail.html` に合わせて整備する。
- `content_source: "fixed_html"` を維持する。
- subject、preheader、CTA、UTM、images manifest等を `mail.html` と整合させる。
- 画像binary、template、fragment、script、workflow、config、docs等を通常campaignでは変更しない。
- Validation、unit tests、Python compile、`git diff --check` 等の必要な検証を実行する。
- `mail.html` が変更されていないことをGit diff / hash等で確認する。
- push、PR作成、`gh pr create` は行わない。実装・テスト・ローカルcommitで停止する。
- 完了後、変更ファイル、campaign.json主要設定、`mail.html` 未変更、Validation/テスト結果、commit ID、想定外変更の有無を報告する。

## Codex後・PR

- Codex結果はChatGPTへ戻し、ChatGPTが差分、`campaign.json`、subject/preheader、CTA/UTM、images、Validation、テスト、想定外変更をレビューする。
- ChatGPTレビューで問題なしとなり、ユーザーがOKした後、ユーザーがCodex画面からPR作成する。
- PR作成は意図的な人間の承認ゲートであり、Codexが自動的に越える前提にしない。
- **通常campaignの最終PRは必ず `main` 向けに作成する。** 作業branchをbaseにしたPRを最終PRとして使わない。
- main向けPRには、ChatGPTが作業branchへ保存した `mail.html` と、Codexが整備した `campaign.json` の両方が差分として含まれる状態にする。

## 自動化

- 通常campaign限定PRは `PR Campaign Validation` 成功後、GitHub Appがauto-mergeする。
- template、workflow、script、config、docsその他を含むシステム変更PRは自動マージせず、ユーザーレビュー待ちとする。
- main反映後は同一commitのGitHub Pages deployment成功と公開HTML・画像・CTA等の検証が完了するまでZoho Draftを作らない。
- 公開検証成功時だけZoho Campaigns Draftを作成する。
- 自動化の終点はDraft作成。Test Email、予約、本番送信、`sendCampaign`系APIは実装・実行しない。
- OAuthのClient ID、Client Secret、Refresh Token、Access Tokenをコード、設定JSON、HTML、ログ、artifact、commitへ保存しない。
- auto-mergeには専用GitHub App installation tokenを使う。
- `EMERGENCY - Recover Zoho Draft Only` は管理者専用のDraft復旧口とし、Zoho UIとledgerを確認した障害時だけ使用する。

## 正式フロー要約

Chatで制作条件確認
→ 訴求決定
→ 件名＋HTML制作・調整
→ ユーザーFIX
→ ChatGPTがGitHub作業branchへ `mail.html` 保存
→ Codexが同branchで `campaign.json` 整備・検証（`mail.html` 変更禁止）
→ ChatGPTレビュー
→ ユーザーOK
→ Codex画面からmain向けPR
→ Validation
→ auto-merge
→ GitHub Pages
→ 公開検証
→ Zoho Campaigns Draft
→ ユーザーがTest Email・本番送信を手動実行
