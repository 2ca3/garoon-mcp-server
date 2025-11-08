# Claude Desktop MCP設定ガイド

## 1. Claude Desktop設定ファイルの場所

macOSでは、Claude Desktopの設定ファイルは以下の場所にあります：

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

## 2. 設定ファイルの内容

以下の内容を`claude_desktop_config.json`ファイルに追加してください：

```json
{
  "mcpServers": {
    "garoon": {
      "command": "python3",
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

**注意**:
- `/path/to/garoon-mcp-server`を実際のプロジェクトパスに置き換えてください
- 認証情報は実際の値に置き換えてください

## 3. uvを使用する場合の推奨設定

```json
{
  "mcpServers": {
    "garoon": {
      "command": "uv",
      "args": ["run", "python", "/path/to/garoon-mcp-server/main.py"],
      "env": {
        "GAROON_BASE_URL": "https://your-subdomain.cybozu.com",
        "GAROON_USERNAME": "your.email@company.com",
        "GAROON_PASSWORD": "your_password_here"
      }
    }
  }
}
```

## 4. 設定手順

### 手順1: 設定ディレクトリを作成（存在しない場合）
```bash
mkdir -p ~/Library/Application\ Support/Claude
```

### 手順2: 設定ファイルを作成/編集
```bash
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### 手順3: 上記のJSON設定を貼り付け（認証情報を実際の値に置き換え）

### 手順4: Claude Desktopを再起動

## 5. 利用可能なツール

設定が完了すると、ClaudeでGaroonの以下の機能が利用できます：

- **get_schedule**: スケジュール取得（自分または他ユーザー）
  - start_date: 開始日 (YYYY-MM-DD)
  - end_date: 終了日 (YYYY-MM-DD)
  - user_id: ユーザーID (オプション、指定すると他ユーザーのスケジュールを取得)

- **search_users**: ユーザー検索
  - query: 検索クエリ（名前、メールアドレス等）
  - limit: 取得件数 (デフォルト: 20)

- **create_schedule**: スケジュール作成
  - subject: 件名
  - start_datetime: 開始日時 (ISO形式)
  - end_datetime: 終了日時 (ISO形式)
  - description: 説明 (オプション)

- **get_messages**: メッセージ取得
  - folder: フォルダ名 (inbox, sent等)
  - limit: 取得件数 (デフォルト: 20)

- **send_message**: メッセージ送信
  - to: 宛先ユーザーIDのリスト
  - subject: 件名
  - body: 本文

## 6. 使用例

設定完了後、Claude内で以下のようにリクエストできます：

```
今日のスケジュールを確認してください
```

```
明日の14:00-15:00に「プロジェクト打ち合わせ」のスケジュールを作成してください
```

```
中田さんの明日のスケジュールを確認してください
```

## 注意事項

⚠️ **セキュリティ**:
- 認証情報は適切に保護してください
- CLAUDE_SETUP.mdファイル（実際の認証情報を含むファイル）は絶対にGitにコミットしないでください
- このテンプレートファイルをコピーして個人用の設定ファイルを作成してください

- Garoon APIの利用制限にご注意ください
- Python 3.10以上がインストールされている必要があります
