# メール生成 正式運用ルール

本書は、セミナー告知メール制作に関して人間・ChatGPT・Codexが共通で参照する正式仕様です。GitHub上の本書と `templates/` を正本とし、ChatGPT用と本番生成用に別々のテンプレートを作りません。

## 基本原則

- 通常のChatGPT Chatから制作を開始し、原稿だけでなくHTMLプレビューまでユーザー承認を得ます。
- 既存テンプレートを再利用し、イベント固有情報はcampaignデータと可変ブロックで差し替えます。
- ChatGPTはGitHubにある最新テンプレートでプレビューを作ります。Codexは承認済みの原稿・画像・ブロック構成・デザインを同じテンプレートで本番反映し、再解釈や再設計をしません。
- テンプレート自体の変更が必要な場合は既存版を無断で破壊せず、影響範囲を示した変更案としてユーザーの確認を受けます。
- GitHub Pages上のHTML確認が終わるまでZoho Draftを作成しません。送信・テスト送信・予約送信はこのリポジトリの対象外で、最終送信判断は必ずユーザーが行います。

## 正式フロー

1. ユーザーがChatGPTへセミナーとGoogle Driveフォルダを提示する。
2. ChatGPTが本書とGitHubの最新テンプレートを確認する。
3. ChatGPTがDrive内の概要、過去原稿、公開用画像素材を確認する。
4. ChatGPTが `template_type` を選択してメール原稿を作成する。
5. ChatGPTがCTAの本体URLを確認し、UTMパラメータを確定する。URLが不明なら推測せずユーザーへ確認する。
6. ChatGPTが確定したCTA情報を含むcampaignデータ相当の情報を整理する。
7. ChatGPTがGitHubと同一のテンプレートおよび本番と同一のCTA URLでHTMLプレビューを作り、ユーザーと文章・画像・レイアウトを調整する。
8. ユーザーが文章、CTA URL、デザインをFIXする。
9. Codexが承認済み内容をcampaignデータと画像へ反映し、既存テンプレートでHTMLを生成してテスト・PRを行う。
10. GitHub Pagesへ公開し、ユーザーが表示とCTA遷移を確認する。
11. HTML確認後に限りGitHub ActionsからZoho Campaigns Draftを作成する。
12. ユーザーがZoho Draftを最終確認し、リポジトリ外で実際の送信を判断する。

## 担当範囲

### ChatGPT

- Google Driveの対象セミナーフォルダ、セミナー概要、過去メルマガ、公開用画像素材の確認
- `template_type` の選択とメール原稿の作成
- CTA本体URLの確認、UTMパラメータの確定（不明時はユーザーへ確認）
- campaignデータ相当の情報整理
- GitHub上の最新テンプレートと本番CTA URLを使用したHTMLプレビューの作成
- ユーザーとの文章・画像・デザイン調整と、承認内容の確定

### Codex / GitHub

- 承認済み内容のcampaignデータへの反映
- 必要画像のGitHub配置
- 既存の正式テンプレートによる本番HTML生成
- HTML要件・リンク・原稿・既存機能のテスト
- コミット、PR、GitHub Pages公開

Codexは承認済みデザインを独自に改善・再設計しません。差異や実装上の制約がある場合は、変更前に確認対象として明示します。

### GitHub Actions

- ユーザーが指定した公開Google Drive画像の取り込み
- GitHub PagesへのHTML公開後、確認済みHTMLを参照するZoho Draftの作成

Actionsはメール送信、テスト送信、予約送信を行いません。

### ユーザー

- ChatGPT上で原稿とHTMLデザインを確認し、FIXを判断
- 必要に応じたPRとGitHub Pages表示の確認
- Zoho Draftの最終確認
- 実際にメールを送信するかどうかの最終判断

## `template_type` の正式ルール

### `standard_seminar`

通常の単発セミナー向けです。正式な種別名として予約されていますが、現時点では未実装です。実装されるまでは別種別へ読み替えず、必要性をユーザーへ報告します。

### `large_seminar`

フォーラム、大型イベント、複数登壇者・複数コンテンツを持つイベント向けです。`campaigns/forum-20260910` の「不動産未来フォーラム2026」をVer.1とします。

## テンプレートとcampaignデータ

- `templates/base/email.html`: 全セミナーメール共通のロゴ、宛名、配信対象注意書き、基本スタイル、署名、レスポンシブ対応
- `templates/seminar/large_seminar.html`: `large_seminar` のブロック順、余白、配色、情報階層
- `templates/email_template.html`: `template_type` を持たない従来形式との後方互換用
- `config/email_defaults.json`: 会社情報、担当者情報、共通画像URL、Zoho宛名タグ、共通注意書き（公開情報のみ）

ChatGPTのプレビューとCodexの本番生成は、いずれも上記GitHubテンプレートを参照します。

campaign JSONはHTMLではなく、イベント固有の `template_type`、`subject`、`preheader`、`banner`、`intro`、`speakers`、`benefits`、`event_info`、`cta` 等を保持します。会社情報や署名をcampaignごとにコピーしません。確定済みcampaignデータから `scripts/build_email.py` で `mail.html` を生成します。

## 全セミナーメール共通仕様

- 最上部に `assets/common/delight-hub-logo.png` のDelight Hubロゴを自然なサイズで1回表示します。
- ロゴ下の宛名は `$[UD:COMPANY_NAME||]$　$[UD:LAST_NAME||]$様` をそのまま出力します。HTML生成処理はZohoタグと全角スペースを壊してはなりません。
- 宛名直下に、過去にセミナー等へ申し込んだ方を配信対象とする共通注意書きを本文より小さく、可読性のあるサイズで表示します。
- campaignのバナー画像は、既存の `build_cta_url()` が返すCTAと完全に同じ本番URLへのリンクにします。バナー直下には、クリックでイベントページへ遷移する旨を表示します。バナー専用のURL生成ロジックや仮URLは使用しません。
- 最下部には `assets/common/amano-haruka.png`、株式会社Delight Hub、企画部 天野 晴香、郵便番号、住所、`mailto:contact@delight-hub.jp`、`https://delight-hub.jp/` を含む共通署名を表示します。
- 共通画像は `assets/common/` の正本をGitHub Pages URLで参照し、campaignディレクトリへ複製しません。会社、担当者、共通画像、宛名、注意書きは `config/email_defaults.json` で一元管理し、campaign JSONへコピーしません。
- これらは `large_seminar` 固有ではなくbaseの責務です。将来の `standard_seminar` も同じbaseを経由して自動適用します。seminar templateにはイベント種別固有ブロックだけを置きます。

## CTA URL / UTMの正式ルール

### 確定のタイミング

- ChatGPTはHTMLプレビューを作る前に、CTAの本体URL、`utm_source`、`utm_medium`、`utm_campaign`、必要な場合は `utm_content` をユーザーと確定します。
- HTMLプレビューから本番HTMLまで同じ本番CTA URLを使用します。`#`、空文字、`example.com`、存在を確認できないURLなどの仮リンクを本番 `campaign.json` / `mail.html` に残しません。
- 本体URLが不明な場合、ChatGPTやCodexはURLを推測・創作せず、ユーザー確認待ちとして報告します。

### UTM値

- 標準値は `utm_source=zoho`、`utm_medium=email` です。
- `utm_campaign` はキャンペーンごとに必ず確定し、`campaign_slug` と整合する機械可読で一貫した値にします。例: slug `forum-20260910` に対して `forum_20260910`。
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
- Zoho Draft作成前に、GitHub PagesのHTML、画像、CTA、件名、本文、レスポンシブ表示を確認します。
- Draft作成は送信承認ではありません。送信操作はユーザーのみが判断します。
