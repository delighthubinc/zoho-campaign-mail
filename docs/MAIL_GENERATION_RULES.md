# メール生成 正式運用ルール

本書は、セミナー告知メール制作に関して人間・ChatGPT・Codexが共通で参照する正式仕様です。GitHub上の本書と `templates/` を正本とし、ChatGPT用と本番生成用に別々のテンプレートを作りません。

## 基本原則

- 通常のChatGPT Chatから制作を開始し、原稿だけでなくHTMLプレビューまでユーザー承認を得ます。
- 既存テンプレートを再利用し、イベント固有情報はcampaignデータと可変ブロックで差し替えます。
- ChatGPTはGitHubにある最新テンプレートでプレビューを作ります。Codexは承認済みの原稿・画像・ブロック構成・デザインを同じテンプレートで本番反映し、再解釈や再設計をしません。
- テンプレート自体の変更が必要な場合は既存版を無断で破壊せず、影響範囲を示した変更案としてユーザーの確認を受けます。
- GitHub Pages上のHTML確認が終わるまでZoho Draftを作成しません。送信・テスト送信・予約送信はこのリポジトリの対象外で、最終送信判断は必ずユーザーが行います。

## ChatGPTでの制作開始からFIXまで（必須順序）

ChatGPTは新規セミナー制作のたびに次の順序を守ります。presetとUTMは提案できますが、ユーザーの明示確認なしに確定または次工程へ進めません。

1. GitHubの最新正式仕様、`templates/`、共通素材、取り込み済みcampaign素材を確認する。
2. `preset` を `standard` / `large` のどちらにするか提案する。
3. **「このpresetでよいですか？」と確認し、ユーザーの明示承認を得る。**
4. presetを出発点として使用する`blocks`と順序の案を提示する。
5. CTA本体URLと最低限 `utm_source`、`utm_medium`、`utm_campaign` の候補を提示する。
6. **「このUTMでよいですか？」と確認し、ユーザーの明示承認を得る。**
7. 使用画像を毎回棚卸しし、継続利用・新規・差し替えを明確にする。
8. 新規・差し替え画像をCodex実装前に、**ChatGPTが `[automation:image-import]` Issueを作成 → GitHub Actionsが自動取込 → ChatGPTがIssue結果を確認 → repository fileを確認 → 正式GitHub Pages URLを確定**の順で取り込む。ユーザーへActions画面の操作を求めず、手動 **Import Drive Images** はIssue bridgeが技術的に失敗した場合の管理者fallbackに限る。
9. GitHub Pages上の正式画像URL、承認済みCTA/UTM、正式generatorと同じ仕様でHTMLプレビューを作る。
10. HTML確認中はcampaignデータ上のblocksを追加・削除・並び替え、再生成して調整する。
11. 文面・画像・CTA・UTM・blocks・HTMLをユーザーがFIXした後にだけCodex用実装プロンプトを作る。

## 正式フロー
### Ver.2（通常のcampaign本番反映）

通常フローは、campaign作成 → PR → `PR Campaign Validation` → GitHub Appによるauto-merge → GitHub Pages deployment → 公開HTML検証 → Zoho Campaigns Draft自動作成まで動作確認済みであり、今後もこの経路を正式運用とします。

1. ユーザーがChatGPTへメルマガ制作を依頼する。
2. ChatGPTがGitHubの最新正式テンプレート、Google Drive等の原稿、画像素材、CTAを確認する。
3. ChatGPTとユーザーが文面、件名、使用画像、CTA等を調整する。
4. 使用画像をCodex実装前にGitHubへ取り込む。campaign固有画像は `campaigns/<slug>/images/`、共通画像は `assets/common/` に置く。新規・差し替えのcampaign画像は、ChatGPTがGitHub connectorからタイトルが完全一致する `[automation:image-import]` Issueを作成し、strict JSON本文に `campaign_slug` と1〜20件の `images`（`drive_file_id`、`filename`）だけを指定する。Actionsが既存 **Import Drive Images** と同じ検証・取込処理を実行するため、ユーザーはGitHub Actions画面を操作しない。

   ```json
   {
     "campaign_slug": "forum-20260910-0811",
     "images": [
       {"drive_file_id": "18xGRVkAAn7IAwGaF0AZ4gz8pp82R_uaU", "filename": "banner.png"}
     ]
   }
   ```

   Issue作成者はrepository adminに限定し、slug、Drive ID、単一filename、画像拡張子、件数、取得内容をfail-closedで検証する。同名の既存画像は上書きせず、新しいfilenameで再申請する。成功コメントのpathとGitHub Pages URLを確認した後、ChatGPTはrepository file自体も再確認する。Issue経路が技術的に失敗した場合だけ、管理者が既存 **Import Drive Images** をfallbackとして手動実行できる。
5. GitHub Pages上で参照する正式な画像URLを確定する。
6. ChatGPTがGitHubの正式テンプレート、GitHubへ取り込み済みの正式画像URL、本番CTAを使ってHTMLプレビューを作成する。
7. ユーザーがChatGPT上で文面、件名、画像、CTA、HTMLレイアウトを確認してFIXする。
8. ChatGPTがCodex用の実装プロンプトを作成する。
9. Codexが承認済み内容を実装する。通常変更するcampaign成果物は原則 `campaigns/<slug>/campaign.json` と `campaigns/<slug>/mail.html` とする。
10. CodexはGitHub上に既に存在する画像URLを参照し、画像binaryを新規追加・変更・コピーしない。
11. CodexはGitHubの既存正式テンプレートを使用して `mail.html` を生成する。
12. CodexはChatGPT上で承認済みのデザインを独自に改善・再設計・再解釈しない。
13. Codexがテスト、コミット、PR作成を行う。
14. `PR Campaign Validation` が変更範囲、全テスト、Python compile、HTML再生成一致、placeholder、CTA、UTM、画像、Secret混入、その他既存validatorを自動検証する。
15. 通常campaignだけを変更したPRは、required checks成功後にGitHub Appがauto-mergeする。システム・テンプレート変更PRはユーザーレビュー待ちとする。
16. main反映後、GitHub Actionsが同一commitのGitHub Pages deployment完了を待つ。
17. GitHub Actionsが公開HTML、campaign識別情報、画像、CTA等を再検証する。
18. 公開検証がすべて成功した場合だけ、Zoho Campaigns Draftを自動作成する。
19. 自動化はここで停止する。
20. ユーザーがZoho Campaigns画面でDraftを確認し、**Test Email** を手動実行して本文、画像、リンク、表示崩れ等を確認する。
21. 問題がなければ、ユーザーがZoho Campaigns画面から本番送信を最終判断し、手動実行する。

したがって、自動化の終点は **Zoho Campaigns Draft作成**、人間の確認開始点は **Zoho CampaignsのTest Email**、本番送信は **ユーザーによる手動操作**です。

`PR Campaign Validation` は全unit test、全Pythonファイルのcompile、`git diff --check`、対象HTML再生成とchecked-in差分、placeholder、仮URL、Zoho差し込みタグ、CTA/UTM、バナーとCTAの同一性、共通画像およびSecretらしき値を検査します。1つの `campaigns/<slug>/campaign.json` と `mail.html` を共に変更するPRだけがauto-merge候補です。画像の削除に関する既存仕様は維持しますが、`images/*` の新規追加・変更を含むcampaign PRはauto-merge対象外です。競合、required checkの失敗・未完了時はGitHub auto-mergeがマージしません。auto-mergeの操作には `GITHUB_TOKEN` を使わず、専用GitHub App installation tokenを使用します。これによりマージが作るmainのpush eventは抑止されず、後段workflowへ確実に接続します。

template、workflow、script、config、docs等を含むシステム変更PR、複数campaign、対象外パス、draft PR、fork PRは自動マージしません。これらはユーザーレビューを必須とします。

main反映後の `Verify Pages and Create Zoho Draft` は、固定sleepだけで進めずGitHub Deployments APIで同一commit SHAの `github-pages` deployment成功を待ちます。その後HTTP取得を再試行し、HTTP 200、UTF-8 HTML、subject、placeholder、CTA、バナー、共通ロゴ・署名画像、登壇者画像を検査し、CTAはHEAD（非対応時はGET）で到達性を確認します。

公開検証に成功した場合だけ、`campaign.json` の `campaign_slug`、`subject`、本文非表示の `zoho_campaign_name` と `config/zoho.json` の `default_mailing_lists` を使い、`createCampaign` APIでDraftを作成します。手動workflow入力はありません。同一commit SHA・slug・Zoho管理名のSHA-256 markerをautomation専用GitHub IssueへAPI呼出し前に予約し、再実行時の二重作成をfail-closedで防ぎます。API失敗後も自動再作成せず、ledgerを人間が調査します。workflow concurrencyも同一SHAの同時実行を直列化します。

OAuth値は `ZOHO_CLIENT_ID`、`ZOHO_CLIENT_SECRET`、`ZOHO_REFRESH_TOKEN` Repository SecretsからDraft作成stepだけへ渡します。成功・失敗を問わずZoho APIレスポンス本文、token、secretは通常ログへ出力・artifact化しません。自動化は `createCampaign` 以外のZoho操作を行わず、`sendcampaign`、テストメール、予約送信、本番送信、contact listへの実配信を明示的に禁止します。

Zoho CampaignsのTest Email、本番送信、予約送信は自動化せず、`sendCampaign`系APIを使用しません。既存Draftの送信操作も行わず、ユーザーの最終確認なしに外部へメールを送信しません。

通常の予約済みmarkerでDraft作成が停止した場合だけ、管理者は `EMERGENCY - Recover Zoho Draft Only` を手動実行できます。current mainのcampaign JSONと公開HTMLを再検証し、ledgerが `reserved` かつ `created` でない場合だけ、明示確認文字列を要求してDraft作成を1回試行します。実行前にZoho UIでDraftが存在しないことを確認します。このworkflowも送信APIを持たず、通常フローでは使用しません。

### リポジトリ管理者が初回だけ行う設定

1. Settings → General → Pull Requestsで **Allow auto-merge** と **Allow squash merging** を有効にします。
2. mainのRuleset/Branch protectionでPull Requestを必須にし、required status checkへ **PR Campaign Validation / validate-campaign** を登録します。required checkの未完了を許す管理者bypassは自動化に付与しません。
3. GitHub Appをこのrepository専用に作成し、Repository permissionsを **Contents: Read and write**、**Pull requests: Read and write** のみにしてinstallします。App IDをActions variable `CAMPAIGN_AUTOMATION_APP_ID`、private keyをRepository Secret `CAMPAIGN_AUTOMATION_APP_PRIVATE_KEY`へ登録します。専用App tokenでauto-mergeするため、main push後のworkflowが`GITHUB_TOKEN`イベント抑止の対象になりません。
4. Pagesをmainから公開し、`github-pages` deploymentが作成されることを確認します。
5. Repository Secretsへ `ZOHO_CLIENT_ID`、`ZOHO_CLIENT_SECRET`、`ZOHO_REFRESH_TOKEN` を登録します。EnvironmentやJSONへ値を複製しません。
6. Issuesを有効にします。初回成功時に `[automation] Zoho Draft ledger` が自動作成されるため、削除・closeしません。

## 担当範囲

### ChatGPT

- GitHub上の最新正式テンプレートの確認
- Google Drive等の原稿、セミナー概要、過去メルマガ、公開用画像素材、CTAの整理
- 必要画像がGitHubへ取り込み済みであることと、GitHub Pages上の正式画像URLの確認
- 未取り込み画像がある場合、Codex用プロンプト作成前に専用画像取込Issueを作成し、完了コメントと実際のrepository fileの両方を確認。確認できたGitHub Pages正式URLだけでHTMLプレビューへ進む
- Issue経由の自動取込が技術的に失敗した場合だけ理由を説明し、管理者向けfallbackとして既存 **Import Drive Images** 手動workflowを案内
- 新規セミナーの `template_type: seminar`、preset候補、blocks案とメール原稿の作成。presetはユーザーの明示確認後に確定
- CTA本体URLとcampaignごとのUTM候補を提示し、「このUTMでよいですか？」への明示確認後に確定
- campaignデータ相当の情報整理
- GitHub上の最新テンプレート、取り込み済みの正式画像URL、本番CTAを使用したHTMLプレビューの作成
- ユーザーとの文章・画像・HTMLレイアウト調整と、承認内容の確定
- 正式画像URLを使ったHTMLのFIX後にCodex用実装プロンプトを作成

### Codex

- 承認済み内容のcampaignデータへの反映
- 既存の正式テンプレートによる本番HTML生成
- HTML要件・リンク・原稿・既存機能のテスト
- コミットとPR作成（Pages公開・検証・Draft作成はActionsが自動実行）

Codexは承認済みデザインを独自に改善・再設計しません。差異や実装上の制約がある場合は、変更前に確認対象として明示します。通常campaign実装ではPNG、JPG/JPEG、GIF、WebPその他のbinary fileを新規追加・変更・コピーせず、取り込み済みのGitHub Pages画像URLを `campaign.json` で参照します。必要画像がGitHub上に存在しない、正式画像URLが不明、またはDrive素材しかなく未取り込みの場合は推測やbinary追加をせず、「画像を先にGitHubへ取り込む必要がある」と報告してfail-closedで停止します。

### GitHub Actions

- ユーザーが指定した公開Google Drive画像の取り込み
- PR検証、条件付きauto-merge、Pages deployment待機、公開HTML・画像・CTA検証
- 公開検証済みHTMLを参照するZoho Draftの自動作成

Actionsはメール送信、テスト送信、予約送信を行いません。

### ユーザー

- ChatGPT上で文面・件名・画像・CTA・HTMLデザインを最終確定し、実装プロンプトをCodexへ投入
- システム・テンプレート変更PRだけをレビュー（通常campaign反映PRのPages確認・Draft作成操作は不要）
- 自動作成されたZoho Draftを確認し、Zoho CampaignsのTest Emailを手動実行して自分宛てに確認
- 本番送信を最終判断し、Zoho Campaigns画面から手動実行

## `template_type` / preset / blocksの正式ルール

### 新規セミナー: `seminar`

今後の新規セミナーcampaignは `template_type: seminar` を使用します。`preset` は任意fieldで、指定する場合は `standard` / `large` の2種類だけです。ChatGPTが初期構成を提案するための補助情報です。presetは表示blockを固定しません。campaign JSONに明示した `blocks` が最終表示と表示順の唯一の正であり、presetと異なってもblocksを優先します。したがって、`large` から `keynote_speakers` を削除することも、`standard` へ追加することもできます。

HTML確認後のblock追加・削除・並び替えは `campaign.json` のblocksだけを変更して正式generatorで再生成します。任意HTMLはcampaignデータへ渡さず、許可された構造化fieldをgeneratorがescapeしてtableベースHTMLへ変換します。

### 許可block schema

共通で `type` が必須です。`heading`、`subtitle`、`note` 等、以下で任意と記したfieldは省略できます。画像は `{ "url": "https://...", "alt": "..." }` 形式です。

| type | 必須field | 任意field / 内容 |
| --- | --- | --- |
| `hero` | `image` | `notice`。画像は共通CTA URLへリンク |
| `text` | `paragraphs`（文字列配列） | `heading` |
| `event_date` | `date` | `note` |
| `cta` | `label` | URL/UTMはcampaign直下の共通`cta`を使用 |
| `speaker` | `name`, `company`, `title`, `image` | `heading`, `subtitle` |
| `keynote_speakers` | `speakers`（speaker配列） | `heading` |
| `benefits` | `items`（文字列配列） | `heading` |
| `session_cards` | `sessions` | `heading` |
| `image_text` | `heading`, `paragraphs`, `image` | `image_position` (`left` / `right`) |
| `company_logos` | `logos`（画像配列） | `heading` |
| `notice` | `text` | なし |
| `divider` | なし | なし |
| `event_info` | `items`（表示名と値のobject） | `heading` |

`session_cards.sessions` の各要素は `time`、`company`、`title` が必須、`keynote`（boolean、既定false）が任意です。時間→会社名→講演タイトルの3段をtableベースで表示し、`keynote: true` の場合だけ「基調講演」バッジを付けます。

### legacy compatibility

`large_seminar` と予約済みの `standard_seminar` は削除しません。特に `campaigns/forum-20260910` は既存JSONを変更せず、`large_seminar` rendererでchecked-in `mail.html` と完全一致することを回帰テストで保証します。新規campaignで両者を使い分ける運用は行いません。

## テンプレートとcampaignデータ

- `templates/base/email.html`: 全セミナー共通のロゴ、宛名、配信対象注意書き、基本スタイル、署名、レスポンシブ対応
- `templates/seminar/seminar.html`: 汎用seminarのblocks挿入点。実レイアウトは安全なblock rendererが生成
- `templates/seminar/large_seminar.html`: 既存`large_seminar`後方互換用
- `templates/email_template.html`: `template_type`を持たない従来形式との後方互換用
- `config/email_defaults.json`: 会社情報、担当者情報、共通画像URL、Zoho宛名タグ、共通注意書き（公開情報のみ）

新規seminar campaign JSONは識別情報、`template_type`、`preset`、`subject`、`preheader`、共通`cta`と構造化`blocks`を保持します。会社情報や署名をcampaignごとにコピーしません。確定済みデータから `scripts/build_email.py` で `mail.html` を再生成します。

画像運用はPR #23で確定した規則を維持します。配信ごとに全画像を棚卸しし、campaign固有画像は `campaigns/<slug>/images/`、共通画像は `assets/common/` へ既存import workflowでCodex実装前に取り込みます。差し替えはキャッシュや旧素材との混同を避けるため原則新しいfilenameを使います。Codexはbinary画像を追加・変更・コピーせず、campaign JSONから正式なGitHub Pages URLだけを参照します。未取り込み、正式URL不明、Drive素材のみのいずれかならURLを推測せずfail-closedで停止します。

## 全セミナーメール共通仕様

- 最上部に `assets/common/delight-hub-logo.png` のDelight Hubロゴを自然なサイズで1回表示します。
- ロゴ下の宛名は `$[UD:COMPANY_NAME||]$　$[UD:LAST_NAME||]$様` をそのまま出力します。HTML生成処理はZohoタグと全角スペースを壊してはなりません。
- 宛名直下に、過去にセミナー等へ申し込んだ方を配信対象とする共通注意書きを本文より小さく、可読性のあるサイズで表示します。
- campaignのバナー画像は、既存の `build_cta_url()` が返すCTAと完全に同じ本番URLへのリンクにします。バナー直下には、クリックでイベントページへ遷移する旨を表示します。バナー専用のURL生成ロジックや仮URLは使用しません。
- 最下部には `assets/common/amano-haruka.png`、株式会社Delight Hub、企画部 天野 晴香、郵便番号、住所、`mailto:contact@delight-hub.jp`、`https://delight-hub.jp/` を含む共通署名を表示します。
- 共通画像は `assets/common/` の正本をGitHub Pages URLで参照し、campaignディレクトリへ複製しません。会社、担当者、共通画像、宛名、注意書きは `config/email_defaults.json` で一元管理し、campaign JSONへコピーしません。
- これらは個別blockやlegacy `large_seminar` 固有ではなくbaseの責務です。汎用 `seminar` も同じbaseを経由し、blocksにはイベント固有コンテンツだけを置きます。

## CTA URL / UTMの正式ルール

### 確定のタイミング

- ChatGPTはHTMLプレビューを作る前に、CTA本体URLと最低限 `utm_source`、`utm_medium`、`utm_campaign`（必要なら`utm_content`）のcampaignごとの候補を提示し、「このUTMでよいですか？」へのユーザーの明示確認後に確定します。
- HTMLプレビューから本番HTMLまで同じ本番CTA URLを使用します。`#`、空文字、`example.com`、存在を確認できないURLなどの仮リンクを本番 `campaign.json` / `mail.html` に残しません。
- 本体URLが不明な場合、ChatGPTやCodexはURLを推測・創作せず、ユーザー確認待ちとして報告します。

### UTM値

- `utm_source`、`utm_medium`、`utm_campaign` をシステム固定値にしません。ChatGPTがcampaignごとに候補と意図を提示し、ユーザーが明示確認した値を使用します。
- `utm_campaign` はcampaignごとに必ず確定し、機械可読で一貫した候補を提案しますが、`campaign_slug`から無断で決定しません。
- `utm_content` は任意です。同じ遷移先を位置別に計測する場合に `hero_cta`、`bottom_cta`、`banner` などを使用できます。指定しなければ各位置で同じCTA URLを使用します。

### campaign JSONの推奨形式

新規・移行済みcampaignでは完成URLを手入力せず、次の構造で保持します。

```json
{
  "cta": {
    "label": "無料で参加申し込み",
    "base_url": "https://events.example.jp/seminar/",
    "utm": {
      "source": "zoho",
      "medium": "email",
      "campaign": "forum_20260910"
    }
  }
}
```

`utm.content` は任意です。従来の `{"label": "詳細を見る", "url": "https://..."}` も引き続き受け付けるため、既存campaignは段階的に移行できます。`url` と `base_url` は同時指定せず、どちらか一方を指定します。

### URL生成と検証

`scripts/build_email.py` は標準ライブラリのURL解析・クエリ生成機能を使い、既存クエリを維持してUTMを追加し、値をURLエンコードします。フラグメントがある場合、クエリは `#...` より前に配置します。同名の生成対象UTMが本体URLに既にある場合は、campaignデータで確定した値へ置き換えます。

生成時にはCTAが空でない絶対 `http://` / `https://` URLであり、ホスト名を持ち、`#` 単独などの仮リンクでないこと、および指定したUTMが生成結果に含まれることを検証します。外部通信による存在確認はHTML生成の必須処理にしません。必要な場合は、GitHub Pages公開後に別工程（ActionsのHTTPステータス確認等）として行います。

## セキュリティと公開ゲート

- OAuthのClient ID、Client Secret、Refresh Token、Access Tokenをコード、設定JSON、campaignデータ、HTML、ログへ保存・出力しません。
- 画像は公開を許可された素材だけをGitHub Pagesへ配置します。
- Zoho Draft作成前に、GitHub ActionsがGitHub PagesのHTML、画像、CTA、件名、campaign識別情報を自動検証します。
- Draft作成は送信承認ではありません。送信操作はユーザーのみが判断します。
