# AI / Codex 実務ルール

- セミナー告知メールは既存テンプレートを原則使用し、毎回ゼロからHTMLデザインを作らない。
- 新規セミナーは `template_type: seminar` を使用し、`preset` は `standard` / `large` の初期構成案としてChatGPTが提案する。最終表示と順序は `blocks` を正とし、preset選択後もcampaign単位で追加・削除・並び替えできる。既存の `large_seminar` 等は後方互換用として変更しない。
- ChatGPTはセミナー内容を把握したうえで、今回の主訴求・切り口をユーザーへ積極的に提案する。過去配信との重複確認は必須要件にしないが、ユーザーから過去訴求や避けたい切り口の情報があれば優先して反映する。
- 必要事項（preset、主訴求、CTA、UTM、画像等）が制作に支障ない程度に揃った後は、細かな工程ごとに何度も承認を求めず、ChatGPT側で件名・本文・CTA・UTM・blocks・HTMLプレビューまで一気に作成して提示する。ユーザーは完成HTMLを見て必要な修正を指示する。
- CTA本体URLなど、推測すると誤配信・誤誘導につながる情報が不明な場合だけは確認して停止する。UTMやpresetは候補を明示するが、独立した承認ゲートとして毎回「このUTMでよいですか」「このpresetでよいですか」と細切れに確認しない。
- ChatGPTで承認済みの原稿・画像・ブロック構成・デザインをCodexが勝手に再設計しない。
- テンプレート変更が必要な場合、既存テンプレートを破壊せず、ユーザー確認対象の変更案として扱う。
- メール生成の正式ルールは `docs/MAIL_GENERATION_RULES.md`、デザインの正本は `templates/` を参照する。ChatGPT用とCodex用の別テンプレートを作らない。
- Zoho Campaignsへの送信・テスト送信・予約送信は実装も実行もしない。Zoho Draft作成はHTMLのGitHub Pages公開・確認後に限り、最終送信判断は必ずユーザーが行う。
- OAuthのClient ID、Client Secret、Refresh Token、Access Tokenをコード、設定JSON、生成物、ログへ出さない。
- 本番HTMLに仮のCTA URLを残さない。CTA URLが不明な場合は推測せず、ユーザーへ確認する。
- CTAとUTMの正式ルールは `docs/MAIL_GENERATION_RULES.md` に従う。ChatGPTはcampaignごとにUTM候補を提示し、HTMLプレビュー時点から本番と同じCTA URLを使用する。
- 全セミナーメールは `templates/base/email.html` を共通基盤とし、`assets/common/` のDelight Hubロゴ、Zoho宛名差し込みタグ、配信対象注意書き、天野晴香のプロフィール画像を含む共通署名を必ず表示する。
- セミナーバナーは `build_cta_url()` で生成したCTAと同じ本番URLへのリンクにし、直下にイベントページへ遷移する旨の注意書きを表示する。
- ロゴとプロフィール画像をcampaign単位で複製せず、会社・担当者・宛名・注意書き等の公開共通情報をcampaign JSONへコピーしない。共通値は `config/email_defaults.json` で管理する。
- 使用画像はCodex実装前にGitHubへ取り込み、ChatGPTのHTMLプレビューからGitHub Pages上の正式画像URLを使用する。campaign固有画像は `campaigns/<slug>/images/`、共通画像は `assets/common/` に置く。新規・差し替えのcampaign画像は、原則としてChatGPTが `[automation:image-import]` Issueを作成し、Actionsから既存の一括取込処理を実行する。完了後はIssue結果とrepository fileを確認し、存在を確認できた正式URLだけを使用する。自動経路に技術的障害がある場合のみ、管理者向けfallbackとして既存の `Import Drive Images` 手動workflowを案内する。
- 通常campaign実装でCodexが変更する成果物は原則 `campaigns/<slug>/campaign.json` と `campaigns/<slug>/mail.html` に限る。CodexはPNG、JPG/JPEG、GIF、WebPその他のbinary fileを新規追加・変更・コピーせず、`campaign.json` からGitHub Pages上の取り込み済み画像URLを参照する。
- 必要画像がGitHub上にない、正式画像URLが不明、またはDrive素材しかなく未取り込みの場合、Codexは画像やURLを推測せず、binary fileをPRへ含めない。「画像を先にGitHubへ取り込む必要がある」と報告してfail-closedで停止する。

## Ver.2 自動化フロー

- GitHubへ取り込み済みの正式画像URLを使ったChatGPT上の原稿・本番CTA・HTMLが承認された通常のcampaign反映は、1つの `campaigns/<slug>/` 配下の `campaign.json` と `mail.html` だけを原則変更する。
- campaign JSONにはディレクトリ名と同じ `campaign_slug`、メール件名 `subject`、本文へ表示しない一意な管理名 `zoho_campaign_name` を必須で保持する。
- Codexは承認済み内容を実装し、テスト・コミットまで行う。実装完了後は結果をChatGPTへ戻し、ChatGPTが差分・テスト結果・想定外変更の有無をレビューする。
- ChatGPTレビューで問題なしとなりユーザーがOKした後、ユーザーがCodex画面のPR作成操作を実行する。PR作成は意図的な人間の承認ゲートであり、Codexが自動的に越える前提にしない。
- PR検証成功後の自動マージは上記campaign限定PRだけに許可する。template、workflow、script、config、docsその他を含むPRは必ずユーザーレビュー待ちとし、自動マージしない。
- main反映後は、同一commitのGitHub Pages deployment成功と公開HTML・画像・CTAの検証が完了するまでZoho Draftを作らない。
- 自動化の終点はZoho Campaigns Draft作成である。`sendcampaign`、テストメール、予約、本番送信、contact listへの配信をコード・workflowへ追加してはならない。
- OAuth値はRepository Secretsからのみ渡し、ログ、artifact、JSON、HTML、commitへ保存しない。
- auto-mergeには専用GitHub App installation tokenを使い、後段のmain push workflowを`GITHUB_TOKEN`のイベント抑止から分離する。
- fail-closed停止時の `EMERGENCY - Recover Zoho Draft Only` は管理者専用のDraft復旧口とし、Zoho UIとledgerを確認した障害時以外は使用しない。
