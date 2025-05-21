# govdata_monitor_3in1_pipeline

政府機関のRSSフィード・固定URL・動画コンテンツを監視し、新着情報の通知と動画のキャプチャ・要約を行うシステムです。

## 機能

- RSS/固定URLの定期監視と新着情報の記録
- 動画ページの監視と新着動画の検出
- 動画からのスクリーンショット自動取得
- 音声の自動文字起こし（Whisper使用）
- テキストの自動要約（OpenAI GPT使用）
- Slack/メール/CLIでの通知

## 必要条件

- Python 3.9以上
- ffmpeg（動画処理用）
- OpenAI API Key（要約機能用）

## インストール方法

1. リポジトリをクローン or ダウンロード

```bash
git clone https://github.com/yourusername/GovInfoWatcher.git
cd GovInfoWatcher
```

2. 必要なライブラリをインストール

```bash
pip install -r requirements.txt
```

3. 設定ファイルの編集
`config/settings.yaml` を編集して監視対象のURL、通知方法などを設定します。

4. 秘密キーの設定（要約機能を使う場合）
`config/secrets.yaml` を作成し、OpenAI APIキーを設定します。

```yaml
openai_api_key: "your-api-key-here"
```

## 使用方法

### Windows環境での実行
`run.bat`をダブルクリックして実行します。

### コマンドラインでの実行

```bash
# 全ての監視処理を実行
python scripts/run_all.py

# URL監視のみ実行
python scripts/run_url_watcher.py

# 動画監視のみ実行
python scripts/run_video_watcher.py
```

### 定期実行の設定
Windows環境の場合は、タスクスケジューラで `run.bat` を定期実行するように設定します。

## ディレクトリ構成
* `config/`: 設定ファイル
* `data/`: 保存データ
* `logs/`: 実行ログ
* `scripts/`: 実行スクリプト
* `src/`: ソースコード
* `tests/`: テストコード

## 主な設定項目

### RSS/固定URLの追加
`config/settings.yaml` の `rss_sources` または `html_sources` に追加します。

### 動画ソースの追加
`config/settings.yaml` の `video_sources` に追加します。セレクタは動画要素を特定するために使用されます。

### 通知設定
`config/settings.yaml` の `notification` セクションで、通知方法（CLI/Slack/メール）を設定します。
