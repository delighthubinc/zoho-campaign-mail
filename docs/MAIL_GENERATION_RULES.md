# メール生成 正式運用ルール

本書は、セミナー告知メール制作に関して人間・ChatGPT・Codexが共通で参照する正式仕様です。GitHub上の本書と `templates/` を正本とし、ChatGPT用と本番生成用に別々のテンプレートを作りません。

## 基本原則

- 通常のChatGPT Chatから制作を開始し、原稿だけでなくHTMLプレビューまでユーザー確認を行います。
- 既存テンプレートを再利用し、イベント固有情報はcampaignデータと可変blockで差し替えます。
- ChatGPTはGitHubにある最新テンプレートでプレビューを作ります。Codexは承認済みの原稿・画像・block構成・デザインを同じテンプレートで本番反映し、再解釈や再設計をしません。
- テンプレート自体の変更が必要な場合は既存版を無断で破壊せず、影響範囲を示した変更案としてユーザー確認対象にします。
- ChatGPT制作工程では、必要事項が揃った後にpreset、UTM、blockなどを工程ごとに細切れで何度も承認させません。完成HTMLを主要な確認ゲートとします。
- GitHub Pages上のHTML確認が終わるまでZoho Draftを作成しません。送信・テスト送信・予約送信はこのリポジトリの自動化対象外で、最終送信判断は必ずユーザーが行います。
- campaign固有画像は各配信campaignごとに自己完結させます。過去campaignの同一画像を探して再利用するより、今回使用するGoogle Drive画像を毎回そのcampaign専用の `images/` へ取り込むことを優先します。

## ChatGPTでの制作開始からFIXまで

ChatGPTは新規セミナー制作のたびに、原則として次の流れで進めます。

1. GitHubの最新正式仕様、`templates/`、共通素材、取り込み済みcampaign素材を確認する。
2. Google Drive、LP、ユーザー提示情報等からセミナー内容、開催情報、登壇者、CTA等を把握する。
3. セミナー内容を踏まえ、**今回の主訴求・切り口をChatGPT側から積極的に提案する。**
   - 過去配信との重複確認は必須要件にしない。
   - 過去メルマガを参照できる場合は参考にしてよい。
   - ユーザーから「前回はこの訴求だった」「今回はこの切り口を使いたい」等の情報があれば、それを優先する。
4. `preset` は `standard` / `large` から適切な候補を提案する。presetは初期構成の補助情報であり、最終表示と順序は `blocks` を正とする。
5. CTA本体URLと、最低限 `utm_source`、`utm_medium`、`utm_campaign` の候補を整理する。`utm_content` は必要な場合のみ使用する。
6. **今回使用するGoogle Drive画像を決め、ユーザーが認識できる形で明示する。**
   - 少なくともDrive上のファイル名を列挙する。
   - 可能ならDrive上の場所と用途（メインバナー、登壇者名、セッション画像等）も示す。
   - ChatGPTが画像候補を選んだ場合は、「今回この画像を使う想定」であることが分かるようにする。
   - 「GitHubに画像がない」と報告する場合も、どのDrive画像を対象に確認したのかを明示する。
7. campaign固有画像は、過去campaignに同一・類似画像が存在するかを突合して再利用せず、今回campaign専用の `campaigns/<slug>/images/` へGoogle Driveから毎回取り込む。DriveとGitHubでファイル名が異なる過去素材の同一性判定を通常フローに入れない。
8. 画像取込は原則としてChatGPTが `[automation:image-import]` Issueを作成し、GitHub Actionsが自動取込する。ChatGPTはIssue結果とrepository fileを確認し、正式GitHub Pages URLを確定する。ユーザーへActions画面の手動操作を求めず、既存 **Import Drive Images** 手動workflowは自動経路が技術的に失敗した場合の管理者fallbackに限る。
9. 必要事項が制作に支障ない程度に揃ったら、ChatGPTは件名、本文、CTA、UTM、blocks、HTMLプレビューまで一気に作成する。
10. presetやUTMだけを理由に、毎回独立して「このpresetでよいですか」「このUTMでよいですか」と細切れの承認を要求しない。ただし、CTA本体URLなど推測すると誤配信・誤誘導につながる情報が不明な場合は確認して停止する。
11. ユーザーが完成HTMLを確認し、「別の訴求にしたい」「前回と重複するので変えたい」「画像を差し替えたい」等の修正を指示する。
12. 文面・画像・CTA・UTM・blocks・HTMLがFIXした後に、ChatGPTがCodex用実装プロンプトを作る。

## 正式フロー
### Ver.2（通常campaign本番反映）

通常フローは、campaign実装 → 人間のPR作成承認 → `PR Campaign Validation` → GitHub Appによるauto-merge → GitHub Pages deployment → 公開HTML検証 → Zoho Campaigns Draft自動作成までを正式運用とします。

1. ユーザーがChatGPTへメルマガ制作を依頼する。
2. ChatGPTがGitHubの最新正式テンプレート、Google Drive等の原稿、画像素材、CTAを確認する。
3. ChatGPTが今回の主訴求を提案し、ユーザーの意向を反映する。
4. ChatGPTが今回使用するGoogle Drive画像をファイル名・用途とともに明示する。
5. campaign固有画像をGoogle Driveから今回campaign専用の `campaigns/<slug>/images/` へ毎回取り込む。共通固定素材だけは `assets/common/` を再利用する。
6. ChatGPTが必要事項を整理し、細切れの確認を挟まず、件名・本文・CTA・UTM・HTMLプレビューまで作成する。
7. ユーザーがChatGPT上で文面、件名、画像、CTA、HTMLレイアウトを確認してFIXする。
8. ChatGPTがCodex用実装プロンプトを作成する。
9. Codexが承認済み内容を実装する。通常変更するcampaign成果物は原則 `campaigns/<slug>/campaign.json` と `campaigns/<slug>/mail.html` とする。
10. CodexはGitHub上に既に存在する今回campaign専用画像URLを参照し、画像binaryを新規追加・変更・コピーしない。
11. Codexは既存正式テンプレートを使って `mail.html` を生成し、承認済みデザインを独自に改善・再設計・再解釈しない。
12. Codexが必要なテストを実行し、コミットまで行う。
13. **Codex実装完了後、その結果をChatGPTへ戻す。ChatGPTが差分、テスト結果、想定外変更の有無をレビューする。**
14. 問題があればChatGPTがCodex向け修正指示を作り、再実装する。
15. **ChatGPTレビューで問題なしとなり、ユーザーがOKした後、ユーザーがCodex画面でPR作成操作を実行する。**
16. PR作成操作は未自動化ではなく、**意図的な人間の承認ゲート**として残す。Codexが自動的にPR作成まで完了する前提にしない。
17. `PR Campaign Validation` が変更範囲、全テスト、Python compile、HTML再生成一致、placeholder、CTA、UTM、画像、Secret混入、その他既存validatorを自動検証する。
18. 通常campaignだけを変更したPRは、required checks成功後にGitHub Appがauto-mergeする。システム・テンプレート変更PRはユーザーレビュー待ちとする。
19. main反映後、GitHub Actionsが同一commitのGitHub Pages deployment完了を待つ。
20. GitHub Actionsが公開HTML、campaign識別情報、画像、CTA等を再検証する。
21. 公開検証がすべて成功した場合だけ、Zoho Campaigns Draftを自動作成する。
22. 自動化はここで停止する。
23. ユーザーがZoho Campaigns画面でDraftを確認し、**Test Email** を手動実行して本文、画像、リンク、表示崩れ等を確認する。
24. 問題がなければ、ユーザーがZoho Campaigns画面から本番送信を最終判断し、手動実行する。

したがって通常campaignの承認・自動化境界は次のとおりです。

**Codex実装完了 → ChatGPTレビュー → ユーザーOK → ユーザーがCodex画面でPR作成 → Validation → auto-merge → Pages → Verify Pages and Create Zoho Draft → Zoho Draft作成**

自動化の終点は **Zoho Campaigns Draft作成**、送信前の人間確認開始点は **Zoho CampaignsのTest Email**、本番送信は **ユーザーによる手動操作**です。

## 画像取込ルール

### campaign固有画像

- バナー、登壇者画像、セッション画像、イベント固有ロゴ等は、原則として各配信campaign専用の `campaigns/<slug>/images/` に置きます。
- **過去campaignに同じ画像が存在していても、通常は再利用しません。今回使用するGoogle Drive画像を毎回そのcampaign専用ディレクトリへ取り込みます。**
- これにより、Drive上の元画像と過去GitHub画像のファイル名が異なる場合でも、同一性を検索・推測・突合する必要をなくします。
- 同一セミナーの2通目・3通目でも、それぞれのcampaign専用ディレクトリへ画像を取り込みます。
- 配信済みcampaignの画像URLは、そのメールの表示資産として保持します。過去campaignの `images/` を後続campaignの都合で上書き・削除・リネームしません。

### 共通画像

- Delight Hubロゴ、共通署名プロフィール画像等、全campaignで共通利用する固定素材だけは `assets/common/` の正本を再利用します。
- 会社情報、担当者、宛名、注意書き等の共通値は `config/email_defaults.json` で管理します。

### 画像選択のユーザー可視化

- ChatGPTは取込前に「今回使用するGoogle Drive画像」をユーザーへ明示します。
- 少なくともDrive上のファイル名を列挙し、可能ならDrive上の場所と用途も示します。
- 例：
  - `20260910bannerA-2.png` — メインバナー
  - `オラガ総研牧野氏（300×300）` — 基調講演・牧野氏
  - `スタイルアクト沖氏（300×300）` — 基調講演・沖氏
- ユーザーがどの画像を使う話なのか分からない状態で「画像がGitHubにありません」とだけ報告してはいけません。

### 取込方法

- campaign画像は、原則ChatGPTがタイトル完全一致の `[automation:image-import]` Issueを作成し、strict JSON本文に `campaign_slug` と1〜20件の `images`（`drive_file_id`、`filename`）だけを指定します。
- Issue作成者はrepository adminに限定し、slug、Drive ID、filename、画像拡張子、件数、取得内容をfail-closedで検証します。
- 同じcampaign内で同名ファイルが既にある場合は上書きせず、新しいfilenameで再申請します。
- 成功コメントのpathとGitHub Pages URLを確認後、ChatGPTはrepository file自体も再確認します。
- Issue経路が技術的に失敗した場合だけ、管理者が既存 **Import Drive Images** をfallbackとして手動実行できます。
- CodexはPNG、JPG/JPEG、GIF、WebP等のbinary fileを通常campaign PRへ新規追加・変更・コピーしません。
- 今回使用すると確認したDrive画像がcampaign専用ディレクトリへ未取り込み、正式URLが不明、またはDrive素材しかない場合、Codexは推測せずfail-closedで停止します。

## 担当範囲

### ChatGPT

- GitHub上の最新正式仕様・テンプレートの確認
- Google Drive等の原稿、セミナー概要、公開用画像素材、CTAの整理
- セミナー内容を踏まえた今回の訴求案の提案
- `template_type: seminar`、preset候補、blocks案、件名、メール原稿、CTA/UTM候補の作成
- 今回使用するGoogle Drive画像のファイル名・用途の明示
- campaign固有画像のcampaign専用ディレクトリへの毎回取込と正式URL確認
- 必要事項が揃った後、件名からHTMLプレビューまで細切れ承認なしで制作
- ユーザーとの文章・画像・HTMLレイアウト調整
- HTML FIX後のCodex用実装プロンプト作成
- Codex実装結果のレビューと、PR作成可否の判断支援

### Codex

- 承認済み内容のcampaignデータへの反映
- 既存正式テンプレートによる本番HTML生成
- HTML要件・リンク・原稿・既存機能のテスト
- コミットまでの実装作業
- 実装結果・テスト結果をユーザー／ChatGPTへ返す
- PR作成はユーザーの承認操作後に行う前提とし、自動承認ゲートとして扱わない

### ユーザー

- ChatGPTが提示した訴求案への意向提示
- ChatGPTが提示した今回使用画像の確認・必要に応じた差し替え指示
- 完成HTMLの確認と最終FIX
- Codex実装結果をChatGPTへ共有
- ChatGPTレビュー後の最終OK
- Codex画面でのPR作成操作
- 自動作成されたZoho Draftの確認
- Zoho CampaignsのTest Email手動実行
- 本番送信の最終判断と手動実行

### GitHub Actions

- 指定された公開Google Drive画像のcampaign専用ディレクトリへの取込
- PR検証
- 条件付きauto-merge
- GitHub Pages deployment待機
- 公開HTML・画像・CTA検証
- 公開検証済みHTMLを参照するZoho Draft自動作成

Actionsはメール送信、テスト送信、予約送信を行いません。

## `template_type` / preset / blocks

### 新規セミナー: `seminar`

今後の新規セミナーcampaignは `template_type: seminar` を使用します。`preset` は任意fieldで、指定する場合は `standard` / `large` の2種類だけです。presetは初期構成案であり、表示blockを固定しません。campaign JSONに明示した `blocks` が最終表示と表示順の正です。

HTML確認後のblock追加・削除・並び替えは `campaign.json` のblocksを変更して正式generatorで再生成します。任意HTMLはcampaignデータへ直接渡さず、許可された構造化fieldをgeneratorがescapeしてtableベースHTMLへ変換します。

### 許可block schema

共通で `type` が必須です。画像は `{ "url": "https://...", "alt": "..." }` 形式です。

| type | 必須field | 任意field / 内容 |
| --- | --- | --- |
| `hero` | `image` | `notice`。画像は共通CTA URLへリンク |
| `text` | `paragraphs` | `heading` |
| `event_date` | `date` | `note` |
| `cta` | `label` | URL/UTMはcampaign直下の共通`cta`を使用 |
| `speaker` | `name`, `company`, `title`, `image` | `heading`, `subtitle` |
| `keynote_speakers` | `speakers` | `heading` |
| `benefits` | `items` | `heading` |
| `session_cards` | `sessions` | `heading` |
| `image_text` | `heading`, `paragraphs`, `image` | `image_position` (`left` / `right`) |
| `company_logos` | `logos` | `heading` |
| `notice` | `text` | なし |
| `divider` | なし | なし |
| `event_info` | `items` | `heading` |

`session_cards.sessions` は `time`、`company`、`title` が必須、`keynote`（boolean、既定false）が任意です。

### legacy compatibility

`large_seminar` と予約済みの `standard_seminar` は削除しません。特に `campaigns/forum-20260910` は既存JSONを変更せず、後方互換rendererでchecked-in `mail.html` と一致することを回帰テストで保証します。新規campaignでlegacy presetを使い分ける運用は行いません。

## テンプレートとcampaignデータ

- `templates/base/email.html`: 全セミナー共通基盤
- `templates/seminar/seminar.html`: 汎用seminarのblocks挿入点
- `templates/seminar/large_seminar.html`: 既存`large_seminar`後方互換用
- `templates/email_template.html`: `template_type`を持たない従来形式との後方互換用
- `config/email_defaults.json`: 会社情報、担当者情報、共通画像URL、Zoho宛名タグ、共通注意書き

新規seminar campaign JSONは識別情報、`template_type`、`preset`、`subject`、`preheader`、共通`cta`、構造化`blocks`を保持します。会社情報や署名をcampaignごとにコピーしません。確定済みデータから `scripts/build_email.py` で `mail.html` を再生成します。

## 全セミナーメール共通仕様

- 最上部に `assets/common/delight-hub-logo.png` のDelight Hubロゴを1回表示します。
- ロゴ下の宛名は `$[UD:COMPANY_NAME||]$　$[UD:LAST_NAME||]$様` をそのまま出力します。
- 宛名直下に配信対象の共通注意書きを本文より小さく表示します。
- campaignバナーは `build_cta_url()` が返すCTAと同じ本番URLへリンクし、直下にイベントページへ遷移する旨を表示します。
- 最下部には `assets/common/amano-haruka.png` を含む共通署名を表示します。
- 共通画像は `assets/common/` の正本をGitHub Pages URLで参照し、campaignディレクトリへ複製しません。
- 会社、担当者、共通画像、宛名、注意書きは `config/email_defaults.json` で一元管理します。

## CTA URL / UTM

### 確定のタイミング

- ChatGPTはHTMLプレビューを作る際に、CTA本体URLと最低限 `utm_source`、`utm_medium`、`utm_campaign`（必要なら`utm_content`）のcampaignごとの候補を提示します。
- presetやUTMを独立した必須承認ゲートにはしません。候補をHTML案と一緒に提示し、完成HTMLの確認過程でユーザーが修正できます。
- HTMLプレビューから本番HTMLまで同じ本番CTA URLを使用します。
- `#`、空文字、`example.com`、存在を確認できないURLなどの仮リンクを本番 `campaign.json` / `mail.html` に残しません。
- CTA本体URLが不明な場合はChatGPTやCodexが推測・創作せず、ユーザー確認待ちとします。

### UTM値

- `utm_source`、`utm_medium`、`utm_campaign` をシステム固定値にしません。ChatGPTがcampaignごとに一貫した候補を提示します。
- `utm_campaign` はcampaignごとに必ず確定します。
- `utm_content` は任意です。指定しなければ各位置で同じCTA URLを使用できます。
- campaign JSONでは原則 `base_url` と構造化した `utm` を保持し、generatorが完成URLを生成します。

`scripts/build_email.py` は既存queryを維持してUTMを追加し、値をURLエンコードします。同名UTMが既にある場合はcampaignデータの値へ置き換えます。生成時には絶対 `http://` / `https://` URL、host、placeholder不在、指定UTM反映を検証します。

## PR Validation / auto-merge

`PR Campaign Validation` は全unit test、全Pythonファイルのcompile、`git diff --check`、対象HTML再生成とchecked-in差分、placeholder、仮URL、Zoho差し込みタグ、CTA/UTM、バナーとCTAの同一性、共通画像、Secretらしき値等を検査します。

1つの `campaigns/<slug>/campaign.json` と `mail.html` を共に変更する通常campaign PRだけがauto-merge候補です。`images/*` の新規追加・変更を含むcampaign PRはauto-merge対象外です。競合、required check失敗・未完了時はマージしません。

template、workflow、script、config、docs、複数campaign、対象外path、draft PR、fork PR等のシステム変更は自動マージせず、ユーザーレビューを必須とします。

auto-mergeには専用GitHub App installation tokenを使用し、main push後のworkflowを `GITHUB_TOKEN` のイベント抑止から分離します。

## Pages検証とZoho Draft

main反映後の `Verify Pages and Create Zoho Draft` は、GitHub Deployments APIで同一commit SHAの `github-pages` deployment成功を待ちます。その後HTTP取得を再試行し、HTTP 200、UTF-8 HTML、subject、placeholder、CTA、バナー、共通ロゴ・署名画像、登壇者画像等を検査し、CTA到達性を確認します。

公開検証成功時だけ、`campaign.json` の `campaign_slug`、`subject`、本文非表示の `zoho_campaign_name` と `config/zoho.json` の `default_mailing_lists` を使い、`createCampaign` APIでDraftを作成します。

同一commit SHA・slug・Zoho管理名のmarkerをautomation専用GitHub IssueへAPI呼出し前に予約し、二重作成をfail-closedで防ぎます。API失敗後も自動再作成せず、ledgerを人間が調査します。workflow concurrencyも同一SHAの同時実行を直列化します。

OAuth値は `ZOHO_CLIENT_ID`、`ZOHO_CLIENT_SECRET`、`ZOHO_REFRESH_TOKEN` Repository SecretsからDraft作成stepだけへ渡し、APIレスポンス本文、token、secretを通常ログやartifactへ出力しません。

Zoho CampaignsのTest Email、本番送信、予約送信は自動化せず、`sendCampaign`系APIを使用しません。既存Draftの送信操作も行いません。

通常の予約済みmarkerでDraft作成が停止した場合のみ、管理者は `EMERGENCY - Recover Zoho Draft Only` を使用できます。Zoho UIとledgerを確認した障害時以外は使用しません。

## セキュリティと公開ゲート

- OAuthのClient ID、Client Secret、Refresh Token、Access Tokenをコード、設定JSON、campaignデータ、HTML、ログへ保存・出力しません。
- 画像は公開を許可された素材だけをGitHub Pagesへ配置します。
- Zoho Draft作成前にGitHub ActionsがGitHub PagesのHTML、画像、CTA、件名、campaign識別情報を自動検証します。
- Draft作成は送信承認ではありません。送信操作はユーザーのみが判断します。
