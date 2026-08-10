# AI / Codex 実務ルール

- セミナー告知メールは既存テンプレートを原則使用し、毎回ゼロからHTMLデザインを作らない。
- 新規セミナーは `template_type: seminar` を使用し、`preset` は `standard` / `large` の初期構成案としてChatGPTが提案する。preset選択後もcampaign単位で追加・削除・並び替えできるが、ユーザーがFIXした `mail.html` の表示を正とする。既存の `large_seminar` 等は後方互換用として変更しない。
- ChatGPTはセミナー内容を把握したうえで、今回の主訴求・切り口をユーザーへ積極的に提案する。過去配信との重複確認は必須要件にしないが、ユーザーから過去訴求や避けたい切り口の情報があれば優先して反映する。
- 必要事項（preset、主訴求、CTA、UTM、画像等）が制作に支障ない程度に揃った後は、細かな工程ごとに何度も承認を求めず、ChatGPT側で件名・本文・CTA・UTM・HTMLプレビューまで一気に作成して提示する。ユーザーは完成HTMLを見て必要な修正を指示する。
- CTA本体URLなど、推測すると誤配信・誤誘導につながる情報が不明な場合だけは確認して停止する。UTMやpresetは候補を明示するが、独立した承認ゲートとして毎回「このUTMでよいですか」「このpresetでよいですか」と細切れに確認しない。
- ChatGPTで承認済みの原稿・画像・ブロック構成・デザインをCodexが勝手に再設計しない。
- テンプレート変更が必要な場合、既存テンプレートを破壊せず、ユーザー確認対象の変更案として扱う。
- メール生成の正式ルールは `docs/MAIL_GENERATION_RULES.md` を参照する。テンプレートは初期制作・デザイン参照に使い、FIX後の表示内容の正本はcampaignの `mail.html` とする。ChatGPT用とCodex用の別テンプレートを作らない。
- Zoho Campaignsへの送信・テスト送信・予約送信は実装も実行もしない。Zoho Draft作成はHTMLのGitHub Pages公開・確認後に限り、最終送信判断は必ずユーザーが行う。
- OAuthのClient ID、Client Secret、Refresh Token、Access Tokenをコード、設定JSON、生成物、ログへ出さない。
- 本番HTMLに仮のCTA URLを残さない。CTA URLが不明な場合は推測せず、ユーザーへ確認する。
- CTAとUTMの正式ルールは `docs/MAIL_GENERATION_RULES.md` に従う。ChatGPTはcampaignごとにUTM候補を提示し、HTMLプレビュー時点から本番と同じCTA URLを使用する。
- 全セミナーメールは `templates/base/email.html` を共通基盤とし、`assets/common/` のDelight Hubロゴ、Zoho宛名差し込みタグ、配信対象注意書き、天野晴香のプロフィール画像を含む共通署名を必ず表示する。
- 新規セミナーメールの本文で既存blockに相当する表現を使う場合、ChatGPTは `templates/seminar/blocks/<block名>.html` と、そのblockから挿入される `templates/seminar/fragments/*.html` のHTML/CSSを標準部品として原則そのまま使用し、block名や概念だけを参考に独自デザインをゼロから作らない。開催概要は `event_info.html`、`section_heading.html`、`event_info_row.html`、CTAは `cta.html`、基調講演は `keynote_speakers.html` と登壇者用fragmentを参照する。
- `templates/base/email.html` は固定シェル、`standard` / `large` presetは初期block構成、`templates/seminar/blocks/*.html` は各blockの外側標準レイアウト、`templates/seminar/fragments/*.html` はblock内部の標準部品、FIX済み `campaigns/<slug>/mail.html` はcampaign最終表示の正本として役割を分ける。
- ユーザーの個別指示によるblockの変更はcampaignの完成HTML上で行い、FIX後の変更をblock templateへ逆反映しない。ユーザーが今後の標準化を明示した場合だけ、通常campaign制作とは分けたsystem/template変更として扱う。
- セミナーバナーは `build_cta_url()` で生成したCTAと同じ本番URLへのリンクにし、直下にイベントページへ遷移する旨の注意書きを表示する。
- ロゴとプロフィール画像など、全campaignで共通利用する固定素材だけを `assets/common/` で再利用する。会社・担当者・宛名・注意書き等の公開共通情報は `config/email_defaults.json` で管理する。
- **イベント固有・配信固有の画像（バナー、登壇者、セッション画像等）は、過去campaignに同じ画像が存在していても再利用判定を行わず、各campaignごとにGoogle Driveの元画像から `campaigns/<slug>/images/` へ毎回取り込む。** DriveとGitHubの過去ファイル名を突合して同一画像かどうかを判定する運用は行わない。
- ChatGPTは画像取込前に、今回使用するGoogle Drive画像をユーザーが認識できる形で明示する。少なくともDrive上のファイル名を列挙し、可能ならDrive上の場所・用途（メインバナー、登壇者名等）も示す。「GitHubに画像がない」と報告する場合も、どのDrive画像を対象に確認したかを必ず明示する。
- 今回使用する画像が確定したら、原則としてChatGPTが `[automation:image-import]` Issueを作成し、Actionsから既存の一括取込処理を実行する。完了後はIssue結果とrepository fileを確認し、存在を確認できた正式GitHub Pages URLだけをHTMLプレビューで使用する。自動経路に技術的障害がある場合のみ、管理者向けfallbackとして既存の `Import Drive Images` 手動workflowを案内する。
- 同一Drive画像を複数campaignで使用する場合も、各campaign専用ディレクトリへ別々に取り込む。これにより、配信済みcampaignが参照するGitHub Pages画像URLを将来の配信作業で上書き・削除しない。
- 通常campaign実装でCodexが変更する成果物は原則 `campaigns/<slug>/campaign.json` と `campaigns/<slug>/mail.html` に限る。CodexはPNG、JPG/JPEG、GIF、WebPその他のbinary fileを新規追加・変更・コピーせず、`campaign.json` からChatGPTが事前に取り込んだcampaign専用GitHub Pages画像URLを参照する。
- 今回使用すると確認したDrive画像がcampaign専用ディレクトリへ未取り込み、正式画像URLが不明、またはDrive素材しかない場合、Codexは画像やURLを推測せず、binary fileをPRへ含めない。「今回使用する画像を先にcampaign専用ディレクトリへ取り込む必要がある」と報告してfail-closedで停止する。

## FIX済みHTML正本ルール

- ChatGPTはユーザーと文面・レイアウト・CSS・レスポンシブ挙動まで確認し、FIX済みHTMLファイルそのものをCodexへ渡す。
- CodexはFIX済みHTMLを再解釈、再設計、blocksへの変換、再生成をせず、そのまま `mail.html` として配置する。
- `campaign.json` はcampaign識別、Zoho管理名、件名、CTA/UTM、画像等の管理・Validation用であり、HTML生成元ではない。`content_source` は `fixed_html` のみを許可する。
- `scripts/build_email.py` は初期HTML生成、デザイン参照、開発・テスト用途として残すが、通常campaignの再生成一致は必須条件にしない。
- PR前にChatGPTがCodexの差分とテスト結果をレビューし、ユーザーOK後にユーザーがCodex画面でPR作成する。

## Ver.2 自動化フロー

- GitHubへ取り込み済みのcampaign専用正式画像URLを使ったChatGPT上の原稿・本番CTA・HTMLが承認された通常のcampaign反映は、1つの `campaigns/<slug>/` 配下の `campaign.json` と `mail.html` だけを原則変更する。
- campaign JSONにはディレクトリ名と同じ `campaign_slug`、メール件名 `subject`、本文へ表示しない一意な管理名 `zoho_campaign_name` を必須で保持する。
- Codexは承認済み内容を実装し、テスト・コミットまで行う。実装完了後は結果をChatGPTへ戻し、ChatGPTが差分・テスト結果・想定外変更の有無をレビューする。
- ChatGPTレビューで問題なしとなりユーザーがOKした後、ユーザーがCodex画面のPR作成操作を実行する。PR作成は意図的な人間の承認ゲートであり、Codexが自動的に越える前提にしない。
- PR検証成功後の自動マージは上記campaign限定PRだけに許可する。template、workflow、script、config、docsその他を含むPRは必ずユーザーレビュー待ちとし、自動マージしない。
- main反映後は、同一commitのGitHub Pages deployment成功と公開HTML・画像・CTAの検証が完了するまでZoho Draftを作らない。
- 自動化の終点はZoho Campaigns Draft作成である。`sendcampaign`、テストメール、予約、本番送信、contact listへの配信をコード・workflowへ追加してはならない。
- OAuth値はRepository Secretsからのみ渡し、ログ、artifact、JSON、HTML、commitへ保存しない。
- auto-mergeには専用GitHub App installation tokenを使い、後段のmain push workflowを`GITHUB_TOKEN`のイベント抑止から分離する。
- fail-closed停止時の `EMERGENCY - Recover Zoho Draft Only` は管理者専用のDraft復旧口とし、Zoho UIとledgerを確認した障害時以外は使用しない。
