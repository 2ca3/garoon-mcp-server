# Garoon MCP Server

GaroonのREST APIをModel Context Protocol (MCP)サーバとして提供するプロジェクトです。Claude Desktop等のMCPクライアントから、Garoonのスケジュールやメッセージ機能を利用できます。

A Model Context Protocol (MCP) server that provides integration with Garoon (Cybozu's groupware solution).

## 機能 / Features

- **スケジュール管理 / Schedule Management**:
  - 自分のスケジュールの閲覧・作成
  - 他のユーザーのスケジュール閲覧（targetTypeパラメータ対応）
  - イベントメニュー（種別）の指定対応
- **会議スケジューラー / Meeting Scheduler**:
  - 空き時間の自動検索（自分と相手の両方が空いている時間を検出）
  - 参加者付きで会議を自動設定
  - 営業時間・昼休みの考慮
- **ユーザー検索 / User Search**:
  - 名前やメールアドレスでユーザーを検索
  - 他ユーザーのスケジュール確認に必要なユーザーIDの取得

## 必要要件 / Requirements

- Python 3.10以上
- Garoonアカウント（REST API利用権限が必要）
- Claude Desktop（推奨）またはその他のMCPクライアント
- `uv`パッケージマネージャー（推奨）

## セットアップ手順 / Installation

### 1. リポジトリのクローン / Clone the repository

```bash
git clone <repository-url>
cd garoon-mcp-server
```

### 2. 依存パッケージのインストール / Install dependencies

推奨: `uv`を使用（高速で信頼性の高いパッケージマネージャー）

```bash
# uvのインストール（まだインストールしていない場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 依存パッケージのインストール
uv pip install -e .
```

または、従来の方法:

```bash
# 仮想環境の作成
python3 -m venv .venv
source .venv/bin/activate  # Windowsの場合: .venv\Scripts\activate

# 依存パッケージのインストール
pip install -e .
```

### 3. 環境変数の設定 / Configure environment variables

`.env.example`をコピーして`.env`を作成し、自分のGaroon認証情報を設定します。

```bash
cp .env.example .env
```

`.env`ファイルを編集 / Edit `.env` file:

```env
GAROON_BASE_URL=https://your-subdomain.cybozu.com
GAROON_USERNAME=your.email@company.com
GAROON_PASSWORD=your_password_here
LOG_LEVEL=INFO
```

### 4. 認証テスト / Test authentication

```bash
python3 test_auth.py
```

認証が成功すると、以下のようなメッセージが表示されます:

```
✅ Authentication successful!
✅ API call successful, response: {...}
```

## Claude Desktopでの使用方法 / Using with Claude Desktop

### 1. Claude Desktop設定ファイルの編集 / Edit Claude Desktop config

以下の場所にある設定ファイルを編集します:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### 2. MCPサーバの設定を追加 / Add MCP server configuration

```json
{
  "mcpServers": {
    "garoon": {
      "command": "/path/to/garoon-mcp-server/.venv/bin/python",
      "args": ["/path/to/garoon-mcp-server/main.py"],
      "env": {
        "GAROON_BASE_URL": "https://your-subdomain.cybozu.com",
        "GAROON_USERNAME": "your.email@company.com",
        "GAROON_PASSWORD": "your_password_here"
      }
    }
  }
}
```

**注意 / Note**:
- `/path/to/garoon-mcp-server`を実際のプロジェクトパスに置き換えてください
- Windowsの場合: `C:\\path\\to\\garoon-mcp-server\\.venv\\Scripts\\python.exe`

### 3. Claude Desktopの再起動 / Restart Claude Desktop

設定を反映するため、Claude Desktopを完全に終了して再起動します。

**注意**: Claude Code（VSCode拡張機能）も同じ設定ファイルを使用するため、Claude Desktop / Claude Code の両方で利用可能です。

### 4. 使用例 / Usage examples

Claude Desktopで以下のようにGaroon機能を使用できます:

**自分のスケジュール確認:**
```
今日のスケジュールを教えて
```

**スケジュール作成:**
```
明日の10時から11時に「会議」という予定を作成して
```

**他のユーザーのスケジュール確認:**
```
山田さんの明日のスケジュールを確認して
```

**ユーザー検索:**
```
「田中」という名前のユーザーを探して
```

**会議の空き時間検索と設定:** 🆕
```
山田さんと明日の午後、1時間会議したい。空いている時間は？
```

```
14:00-15:00で「プロジェクト会議」という会議を設定してください
```

## Dockerを使った設定（オプション） / Using Docker (Optional)

Dockerを使ってMCPサーバを実行することもできます。

### 1. Dockerイメージのビルド / Build Docker image

```bash
docker build -t garoon-mcp-server .
```

### 2. Claude Desktop設定でDockerを使用 / Use Docker in Claude Desktop config

```json
{
  "mcpServers": {
    "garoon": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "GAROON_BASE_URL",
        "-e",
        "GAROON_USERNAME",
        "-e",
        "GAROON_PASSWORD",
        "garoon-mcp-server:latest"
      ],
      "env": {
        "GAROON_BASE_URL": "https://your-subdomain.cybozu.com",
        "GAROON_USERNAME": "your.email@company.com",
        "GAROON_PASSWORD": "your_password_here"
      }
    }
  }
}
```

### Docker使用のメリット / Benefits of using Docker

- ✅ Python環境の隔離
- ✅ 依存関係の管理が容易
- ✅ デプロイが簡単

## 認証方式 / Authentication

このMCPサーバは、Garoon REST APIの`X-Cybozu-Authorization`ヘッダーを使用して認証します。ユーザー名とパスワードをBase64エンコードして送信します。

This MCP server uses the `X-Cybozu-Authorization` header for Garoon REST API authentication. Username and password are Base64 encoded.

## 利用可能なツール / Available Tools

#### get_schedule
自分または他のユーザーのスケジュールを取得します / Get schedule events from Garoon for yourself or other users.

Parameters:
- `start_date` (required): 開始日 (YYYY-MM-DD形式) / Start date in YYYY-MM-DD format
- `end_date` (required): 終了日 (YYYY-MM-DD形式) / End date in YYYY-MM-DD format
- `user_id` (optional): ユーザーID（指定すると他ユーザーのスケジュールを取得、省略すると自分のスケジュール） / User ID to get schedule for (if not specified, returns your own schedule)

**注意**: `user_id`を指定する場合、内部的に`targetType="user"`パラメータが自動的に追加されます。

#### create_schedule
新しいスケジュールイベントを作成します / Create a new schedule event in Garoon.

Parameters:
- `subject` (required): イベントのタイトル / Event subject/title
- `start_datetime` (required): 開始日時 (ISO形式) / Start datetime in ISO format
- `end_datetime` (required): 終了日時 (ISO形式) / End datetime in ISO format
- `description` (optional): イベントの説明 / Event description
- `event_menu` (optional): イベントメニュー（例: "会議", "外出"）/ Event menu/category. Defaults to "-----" if omitted.

**注意**: ログインユーザー（`GAROON_USERNAME`）が自動的に参加者として追加されます。

#### search_users
Garoonのユーザーを名前やその他の条件で検索します / Search for users in Garoon by name or other criteria.

Parameters:
- `query` (required): 検索クエリ（ユーザー名、メールアドレス等） / Search query (user name, email, etc.)
- `limit` (optional): 最大取得件数（デフォルト: 20） / Maximum number of results to return (default: 20)

**使用例**: 他のユーザーのスケジュールを確認する前に、このツールでユーザーIDを検索できます。

#### find_available_time 🆕
自分と指定ユーザーの両方が空いている時間帯を検索します / Find available time slots for a meeting with another user.

Parameters:
- `user_id` (required): 相手のユーザーID / Other user's Garoon user ID
- `start_date` (required): 検索開始日 (YYYY-MM-DD) / Search start date
- `end_date` (required): 検索終了日 (YYYY-MM-DD) / Search end date
- `duration_minutes` (required): 必要な会議時間（分） / Required meeting duration in minutes
- `start_time` (optional): 営業開始時刻 (HH:MM, デフォルト: 09:00) / Daily start time
- `end_time` (optional): 営業終了時刻 (HH:MM, デフォルト: 18:00) / Daily end time
- `exclude_lunch` (optional): 昼休み除外 (デフォルト: true) / Exclude lunch time 12:00-13:00

**戻り値**: 最大3件の空き時間候補（開始・終了時刻）

#### create_meeting
参加者付きで会議スケジュールを作成します / Create a meeting with attendees.

Parameters:
- `subject` (required): 会議のタイトル / Meeting subject/title
- `start_datetime` (required): 開始日時 (ISO形式) / Start datetime (ISO format)
- `end_datetime` (required): 終了日時 (ISO形式) / End datetime (ISO format)
- `attendee_ids` (required): 参加者のユーザーIDリスト / List of attendee user IDs
- `description` (optional): 会議の説明 / Meeting description
- `event_menu` (optional): イベントメニュー（例: "会議", "外出"）/ Event menu/category. Defaults to "-----" if omitted.

**注意**: ログインユーザー（`GAROON_USERNAME`）が自動的に参加者の先頭に追加されます。`attendee_ids` に含まれている場合は重複しません。

## トラブルシューティング / Troubleshooting

### 認証エラーが発生する場合 / Authentication errors

- Garoonのユーザー名とパスワードが正しいか確認してください
- GaroonのベースURLが正しいか確認してください（末尾のスラッシュは不要）
- Garoonアカウントが有効で、API利用が許可されているか確認してください

### MCPサーバが起動しない場合 / Server won't start

- Pythonのパスが正しいか確認してください
- 仮想環境が有効化されているか確認してください
- 依存パッケージがインストールされているか確認してください

### ユーザー検索やスケジュール取得でエラーが発生する場合 / User search or schedule retrieval errors

- **「指定されたURIパスが見つかりません」エラー**:
  - Garoon APIのバージョンを確認してください（クラウド版またはパッケージ版4.10以降が必要）
  - ユーザーアカウントにAPI利用権限があるか確認してください

- **他ユーザーのスケジュールが取得できない**:
  - `user_id`パラメータと`targetType`パラメータの両方が必要です（本MCPサーバでは自動的に設定されます）
  - 閲覧権限がないスケジュールは取得できません

## セキュリティに関する注意 / Security Notes

⚠️ **重要 / Important**:

- `.env`ファイルは絶対にgitにコミットしないでください / Never commit `.env` file to git
- パスワードやAPIキーを含むファイルは共有しないでください / Don't share files containing passwords or API keys
- 本番環境では、より安全な認証方式（OAuth等）の使用を検討してください / Consider using more secure authentication methods (OAuth, etc.) in production

## ファイル構成 / File Structure

```
garoon-mcp-server/
├── main.py                        # MCPサーバのメインエントリーポイント
├── garoon_client.py               # Garoon APIクライアント
├── tests/
│   ├── test_main.py               # MCPツールのユニットテスト
│   └── test_garoon_client.py      # Garoon APIクライアントのユニットテスト
├── pyproject.toml                 # プロジェクト設定と依存関係
├── .env                           # 環境変数（gitに含めない）
├── .env.example                   # 環境変数のテンプレート
├── .gitignore                     # Git除外設定
└── README.md                      # このファイル
```

## 開発 / Development

### 開発用依存パッケージのインストール / Installing development dependencies

```bash
# uvを使用する場合
uv pip install -e ".[dev]"

# または、pipを使用する場合
pip install -e ".[dev]"
```

### コードフォーマット / Code formatting

```bash
uv run black .
# または: black .
```

### 型チェック / Type checking

```bash
uv run mypy main.py garoon_client.py
# または: mypy main.py garoon_client.py
```

### テストの実行 / Running tests

```bash
uv run pytest
# または: pytest
```

## 変更履歴 / Changelog

### v0.3.0

**追加された機能:**
- ✅ `eventMenu`パラメーター対応（`create_schedule` / `create_meeting`）
- ✅ ログインユーザーを自動的に参加者に追加（`GAROON_USERNAME`を使用）
- ✅ `create_meeting`の重複参加者排除

**バグ修正:**
- `eventType`の値を正しい`"REGULAR"`に修正（誤: `"NORMAL"`）
- `subject` / `notes`のリクエスト形式をAPI仕様に準拠（文字列直接）
- `start` / `end`に`timeZone`フィールドを追加
- `attendees`の`id`フィールドを正しい`code`フィールドに修正

### v0.2.0

**追加された機能:**
- ✅ 空き時間自動検索機能（`find_available_time`ツール）
  - 自分と相手の両方が空いている時間を自動検出
  - 営業時間・昼休みの考慮
  - 最大3件の候補を提示
- ✅ 参加者付き会議作成（`create_meeting`ツール）
- ✅ タイムゾーン指定対応（`GAROON_TIMEZONE`環境変数）

### v0.1.0

**追加された機能:**
- ✅ Garoon REST API統合（X-Cybozu-Authorization認証）
- ✅ スケジュール管理（取得・作成）
- ✅ ユーザー検索機能（`search_users`ツール）
- ✅ 他ユーザーのスケジュール確認（`targetType`パラメータ対応）

## ライセンス / License

MIT License - see LICENSE file for details.

## サポート / Support

問題が発生した場合は、Issueを作成してください。

For issues and questions, please create an issue on GitHub.