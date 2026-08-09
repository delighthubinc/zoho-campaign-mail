# Zoho Campaign Mail

ChatGPT で確定したメール原稿と画像素材から HTML メールを生成し、GitHub Pages で公開した `mail.html` を使って Zoho Campaigns の **Draft だけ**を作成するリポジトリです。

> [!IMPORTANT]
> このリポジトリには、送信、予約送信、既存キャンペーンの更新機能はありません。`create_zoho_draft.py` が呼び出す Zoho Campaigns API は `createCampaign` だけです。

メール制作におけるChatGPT、Codex、GitHub Actions、ユーザーの役割と承認フローは、正本である [メール生成 正式運用ルール](docs/MAIL_GENERATION_RULES.md) を参照してください。

## ディレクトリ構成

```text
.
├── campaigns/
│   ├── api-test-20260809.html   # 既存の動作確認用ファイル
│   └── <campaign-slug>/
│       ├── mail.html            # 公開する生成済みメール
│       └── images/              # 公開する画像
├── config/
│   ├── email_defaults.json      # 全セミナーメール共通の公開ブランド・署名設定
│   ├── zoho.json                # 実運用の非機密固定設定
│   └── zoho.example.json        # 新しい環境向けの設定例
├── scripts/
│   ├── build_email.py           # 原稿から mail.html を生成
│   ├── publish_images.py        # 画像を公開ディレクトリへ配置
│   └── create_zoho_draft.py     # Zoho Campaigns Draft を作成
├── templates/
│   ├── base/email.html           # セミナー共通の幅・フォント・フッター・レスポンシブ基盤
│   ├── seminar/large_seminar.html # 大型セミナーのブロック順とデザイン
│   └── email_template.html       # template_type未指定時の従来テンプレート
├── .env.example
└── .gitignore
```

## 安全方針

- GitHub ActionsではOAuthの `ZOHO_CLIENT_ID`、`ZOHO_CLIENT_SECRET`、`ZOHO_REFRESH_TOKEN` をRepository Secretsだけから環境変数へ渡します。ローカル実行時に限り `.env` をフォールバックとして利用できます。
- `.env` は Git 管理しません。Access Token はファイルへ保存せず、ログにも出しません。
- listkey、Topic ID、From、Reply-To、GitHub Pages Base URL は非機密の固定設定として JSON に保存できます。
- 必要な Scope は `ZohoCampaigns.campaign.CREATE`、`ZohoCampaigns.campaign.READ`、`ZohoCampaigns.contact.READ` です。`ZohoCampaigns.campaign.UPDATE` は使用しません。
- Draft 作成前にはまず `--dry-run` で入力を確認してください。dry-run はOAuth通信もZoho API通信も行いません。
- スクリプトは HTTPS の GitHub Pages URLのみを `content_url` として許可し、slugとファイル名を検証します。

## セットアップ

Python 3.10 以降を使用します。初期実装はPython標準ライブラリだけで動作し、追加パッケージは不要です。

```bash
cp .env.example .env
```

`.env` に3つのOAuth値を設定します。実運用のTopic ID、listkey、From、Reply-To、GitHub Pages Base URLは、非機密の固定値として `config/zoho.json` に設定済みです。

`mailing_lists` は「表示名 → listkey」の対応で、配信先が増えた場合も項目を追加できます。

## 1. 画像を配置する

画像マニフェストの例（`work/images.json`）:

```json
{
  "images": [
    {"name": "banner.jpg", "source": "work/banner.jpg"},
    {"name": "speaker.jpg", "drive_file_id": "GOOGLE_DRIVE_FILE_ID"}
  ]
}
```

現時点ではローカルの `source` のコピーに対応しています。

```bash
python3 scripts/publish_images.py \
  --campaign-slug 2026-example \
  --manifest work/images.json
```

Google Drive の `drive_file_id` / `drive_url` はインターフェースだけを定義しており、ダウンロード処理は未実装です。Driveから手動で安全に取得したファイルを `source` で指定してください。

## 2. HTMLメールを生成する

原稿JSONの例（`work/content.json`）:

```json
{
  "preheader": "メール一覧に表示する短い説明",
  "heading": "セミナーのご案内",
  "hero_image": {"filename": "banner.jpg", "alt": "セミナーバナー"},
  "paragraphs": ["本文1段落目。", "本文2段落目。"],
  "cta": {"label": "詳細を見る", "url": "https://example.jp/event"},
  "footer": "株式会社Delight Hub"
}
```

```bash
python3 scripts/build_email.py \
  --campaign-slug 2026-example \
  --content work/content.json \
  --config config/zoho.json
```

出力先は `campaigns/2026-example/mail.html` です。既存ファイルを置き換える場合だけ `--overwrite` を付けます。原稿文字列はHTMLとして解釈せずエスケープされ、段落内の改行だけが `<br>` に変換されます。

### セミナーテンプレート

`campaign.json` の `template_type` により構成を選択します。正式な種別と制作・承認フローの詳細は [メール生成 正式運用ルール](docs/MAIL_GENERATION_RULES.md) を参照してください。不動産未来フォーラム2026は次のコマンドで再生成できます。

```bash
python3 scripts/build_email.py \
  --campaign-slug forum-20260910 \
  --content campaigns/forum-20260910/campaign.json \
  --config config/zoho.json \
  --overwrite
```

## 3. GitHub Pagesへ公開する

生成したHTMLと画像をレビューしてコミット・pushし、以下のURLをブラウザや `curl` で取得できることを確認します。

```text
https://delighthubinc.github.io/zoho-campaign-mail/campaigns/2026-example/mail.html
```

GitHub Pagesの反映前にDraft作成を実行しないでください。

## 4. Draftを作成する

まず通信なしでペイロードを確認します。

```bash
python3 scripts/create_zoho_draft.py \
  --config config/zoho.json \
  --campaign-slug 2026-example \
  --campaign-name "2026年 セミナー案内" \
  --subject "セミナー開催のお知らせ" \
  --mailing-list "過去リスト（新）" \
  --mailing-list "CRMから連携されたリスト" \
  --dry-run
```

dry-runの出力には、Topic、選択したリスト名と `list_details`、From、Reply-To、`content_url` が含まれます。`list_details` はZoho Campaignsが要求する `{"<listkey1>":[],"<listkey2>":[]}` 形式です。

確認後、`--dry-run` を外したときだけ、OAuth Access Tokenを取得して `POST /api/v1.1/createCampaign` を1回呼び出します。

```bash
python3 scripts/create_zoho_draft.py \
  --config config/zoho.json \
  --campaign-slug 2026-example \
  --campaign-name "2026年 セミナー案内" \
  --subject "セミナー開催のお知らせ" \
  --mailing-list "過去リスト（新）" \
  --mailing-list "CRMから連携されたリスト"
```

### 実装しない操作

- メールの送信、テスト送信、予約送信
- 既存Draftまたはキャンペーンの更新
- UPDATE系API
- Google Drive API認証・ダウンロード（初期実装では未対応）

## GitHub ActionsからZoho Campaigns Draftを作成する手順

このworkflowが行うのは、新規Draftを作る `createCampaign` の呼び出しだけです。送信、予約送信、既存キャンペーンの更新は行いません。

1. GitHubリポジトリの **Settings → Secrets and variables → Actions** で、次の3項目をRepository Secretsに登録します（値をリポジトリ内のファイルへ保存しないでください）。
   - `ZOHO_CLIENT_ID`
   - `ZOHO_CLIENT_SECRET`
   - `ZOHO_REFRESH_TOKEN`
2. HTMLメールと画像をコミット・pushし、対象の `mail.html` がGitHub Pagesへ反映されるまで待ちます。
3. GitHubの **Actions** 画面から **Create Zoho Draft** workflowを選び、**Run workflow** を開きます。
4. 次の入力項目を指定します。
   - `campaign_slug`: `campaigns/<campaign_slug>/mail.html` のディレクトリ名
   - `campaign_name`: Zoho Campaignsに表示するキャンペーン名
   - `subject`: メールの件名
5. **Run workflow** を押します。workflowは回帰テスト、GitHub PagesのHTTP 200確認、秘密情報を含まないDraft内容の確認を順に行ってから、固定の2配信リストを対象にDraftを作成します。Pagesが未反映の場合はDraftを作らずエラー終了します。
6. 成功後、Zoho Campaignsを開き、作成されたDraftの件名、本文、From、Reply-To、Topic、配信リストを最終確認してください。送信操作はこのリポジトリの対象外です。
