# Zoho Campaign Mail

ChatGPTとユーザーがFIXしたHTMLメールを正本として配置し、GitHub Pages で公開した `mail.html` を使って Zoho Campaigns の **Draft だけ**を作成するリポジトリです。

> [!IMPORTANT]
> このリポジトリには、送信、予約送信、既存キャンペーンの更新機能はありません。`create_zoho_draft.py` が呼び出す Zoho Campaigns API は `createCampaign` だけです。

メール制作におけるChatGPT、Codex、GitHub Actions、ユーザーの役割と承認フローは、正本である [メール生成 正式運用ルール](docs/MAIL_GENERATION_RULES.md) を参照してください。

## ディレクトリ構成

```text
.
├── campaigns/
│   ├── api-test-20260809.html   # 既存の動作確認用ファイル
│   └── <campaign-slug>/
│       ├── campaign.json        # 識別・CTA/UTM・画像等の管理/Validationデータ
│       ├── mail.html            # FIX済み表示内容の正本
│       └── images/              # 公開する画像
├── config/
│   ├── email_defaults.json      # 全セミナーメール共通の公開ブランド・署名設定
│   ├── zoho.json                # 実運用の非機密固定設定
│   └── zoho.example.json        # 新しい環境向けの設定例
├── scripts/
│   ├── build_email.py           # 初期HTML生成・デザイン参照・開発用
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
- ローカル開発でpayloadを確認する場合は `--dry-run` を使用できます。通常のDraft作成は公開検証後にActionsが自動実行します。
- スクリプトは HTTPS の GitHub Pages URLのみを `content_url` として許可し、slugとファイル名を検証します。

## セットアップ

Python 3.10 以降を使用します。初期実装はPython標準ライブラリだけで動作し、追加パッケージは不要です。

```bash
cp .env.example .env
```

`.env` に3つのOAuth値を設定します。実運用のTopic ID、listkey、From、Reply-To、GitHub Pages Base URLは、非機密の固定値として `config/zoho.json` に設定済みです。

`mailing_lists` は「表示名 → listkey」の対応で、配信先が増えた場合も項目を追加できます。

## 1. Codex実装前に画像を取り込む

使用画像は、ChatGPTがHTMLプレビューを確定しCodex用プロンプトを作るより前にGitHubへ取り込みます。campaign固有画像は `campaigns/<slug>/images/`、ロゴや担当者画像などの共通画像は `assets/common/` に配置し、GitHub Pages上の正式画像URLを確定してください。公開Google Drive画像は、既存の **Import Drive Image**、**Import Drive Images**、**Import Common Asset** workflowを用途に応じて使用します。これらの仕組みをCodexで作り直したり、通常campaign PRへ画像binaryを含めたりしません。

以下はローカル素材を取り込む既存方法です。

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

Google Drive上の公開画像は上記の既存workflowで取り込みます。取り込み後、GitHub Pages上で参照する正式URLをChatGPTのHTMLプレビューと `campaign.json` の両方で使用します。

## 2. FIX済みHTMLメールを配置する

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

このコマンドは初期HTML作成や開発に利用できます。通常campaignでは、ChatGPT上でユーザーがFIXしたHTMLファイルそのものを `campaigns/<slug>/mail.html` に配置します。`campaign.json` は管理・Validation用であり、checked-in HTMLを再生成できる必要はありません。

### セミナーテンプレート

`campaign.json` の `template_type` により構成を選択します。正式な種別と制作・承認フローの詳細は [メール生成 正式運用ルール](docs/MAIL_GENERATION_RULES.md) を参照してください。不動産未来フォーラム2026は次のコマンドで再生成できます。

```bash
python3 scripts/build_email.py \
  --campaign-slug forum-20260910 \
  --content campaigns/forum-20260910/campaign.json \
  --config config/zoho.json \
  --overwrite
```

## 3. PR以降のVer.2自動処理

通常フローは、画像をCodex実装前にGitHubへ取り込み、ChatGPTがGitHubの正式テンプレート・GitHub Pages上の正式画像URL・本番CTAを使ったHTMLをユーザーとFIXしてから、FIX済みHTMLファイルそのものと実装プロンプトをCodexへ渡します。CodexはHTMLを再設計・再生成せず、画像binaryも追加・変更・コピーせず、原則として `campaign.json` と `mail.html` だけを実装します。必要画像または正式URLが未確定なら推測せず、「画像を先にGitHubへ取り込む必要がある」と報告してfail-closedで停止します。Codexの実装・テスト結果をChatGPTがレビューし、ユーザーOK後にユーザーがPR作成操作を行うと、通常の単一campaign反映ではGitHub Actionsが次を自動実行します。ユーザーがPages表示を確認してから手動でDraft workflowを起動する操作はありません。

1. PR変更範囲、全テスト、compile、FIX済みHTMLのplaceholder、仮値、CTA・UTM、画像、共通素材、Zoho宛名タグ、JavaScript、Secretを検証（HTML再生成一致は行わない）
2. required checks成功かつ競合なしの場合だけauto-merge
3. mainと同一commitのGitHub Pages deployment完了を待機
4. 公開HTML、campaign識別情報、画像、CTAをHTTPで検証
5. 検証成功時だけZoho Campaigns Draftを作成して停止

通常フローの動作確認は、campaign作成からPR検証、GitHub Appによるauto-merge、Pages deployment、公開内容検証、Zoho Campaigns Draft作成まで完了しています。**自動化の終点はDraft作成**です。その後、ユーザーがZoho Campaigns画面でDraftを確認し、同画面の **Test Emailを手動実行**して本文・画像・リンク・表示を確認します。問題がなければ、ユーザー自身が本番送信を最終判断して手動実行します。

公開URLは次の形式です。

```text
https://delighthubinc.github.io/zoho-campaign-mail/campaigns/2026-example/mail.html
```

template、workflow、script、config、docs等を含むPRは自動マージされず、ユーザーレビューが必要です。正式な条件は [メール生成 正式運用ルール](docs/MAIL_GENERATION_RULES.md) を参照してください。

## 4. Draft作成スクリプトのローカルdry-run

通常運用ではActionsがcampaign JSONから値を読み取ります。開発時に通信なしでペイロードだけを確認する場合は、次のdry-runを使用できます。

```bash
python3 scripts/create_zoho_draft.py \
  --config config/zoho.json \
  --campaign-file campaigns/forum-20260910/campaign.json \
  --dry-run
```

dry-runの出力には、Topic、設定済み配信リスト、From、Reply-To、`content_url` が含まれますが、OAuth通信もZoho API通信も行いません。通常運用で人間が`--dry-run`を外して実行することはありません。

### 実装しない操作

- Zoho CampaignsのTest Emailの自動実行
- メールの本番送信、予約送信
- `sendCampaign` 系APIの使用
- 既存Draftの送信操作
- ユーザーの最終確認を経ない外部へのメール送信
- 既存Draftまたはキャンペーンの更新
- UPDATE系API
- Google Drive API認証・ダウンロード（初期実装では未対応）

## 障害時だけのDraft recovery

通常フローがledgerを`reserved`にした後で停止した場合に限り、repository管理者はActionsの **EMERGENCY - Recover Zoho Draft Only** を利用できます。先にZoho Campaigns UIで同名Draftが存在しないことを確認し、明示確認文字列を入力します。current mainの公開HTMLとledgerを再検証し、未作成と判断できる場合だけDraft作成を一度試行します。通常運用では使用しません。
