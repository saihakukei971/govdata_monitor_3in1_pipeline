import feedparser
import requests
from datetime import datetime
import json
from pathlib import Path


class RSSFetcher:
    """RSSフィードからデータを取得するクラス"""

    def __init__(self, data_dir="data", logger=None):
        self.data_dir = Path(data_dir)
        self.logger = logger

        # データディレクトリが存在しない場合は作成
        self.data_dir.mkdir(exist_ok=True, parents=True)

        # 監視済みURLの保存ファイル
        self.watched_file = self.data_dir / "watched_urls.json"

        # 以前に取得したURLのリスト
        self.watched_urls = self._load_watched_urls()

    def _load_watched_urls(self):
        """監視済みURLをロード"""
        if self.watched_file.exists():
            try:
                with open(self.watched_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"監視済みURLの読み込みエラー: {e}")
                return {"rss": {}, "html": {}, "video": {}}
        else:
            return {"rss": {}, "html": {}, "video": {}}

    def _save_watched_urls(self):
        """監視済みURLを保存"""
        try:
            with open(self.watched_file, 'w', encoding='utf-8') as f:
                json.dump(self.watched_urls, f, ensure_ascii=False, indent=2)
        except Exception as e:
            if self.logger:
                self.logger.error(f"監視済みURLの保存エラー: {e}")

    def fetch(self, source):
        """RSSフィードを取得"""
        if self.logger:
            self.logger.info(f"RSS取得開始: {source['name']} ({source['url']})")

        # RSSフィードの取得
        try:
            feed = feedparser.parse(source['url'])

            # フィードの取得に失敗した場合
            if feed.bozo and not feed.entries:
                if self.logger:
                    self.logger.error(f"RSS取得エラー: {source['name']} - {feed.bozo_exception}")
                return []

            # 新着エントリの抽出
            new_entries = []
            source_id = source['url']

            # ソースIDがwatched_urlsに存在しない場合は初期化
            if source_id not in self.watched_urls["rss"]:
                self.watched_urls["rss"][source_id] = []

            for entry in feed.entries:
                # エントリのURLまたはIDを取得
                entry_id = entry.get('link', entry.get('id', ''))

                # 新着判定
                if entry_id and entry_id not in self.watched_urls["rss"][source_id]:
                    # エントリの公開日時を取得
                    published = entry.get('published_parsed')
                    if published:
                        published = datetime(*published[:6]).strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        published = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    # 新着エントリとして追加
                    new_entries.append({
                        'title': entry.get('title', 'タイトルなし'),
                        'link': entry_id,
                        'published': published,
                        'source': source['name']
                    })

                    # 監視済みURLに追加
                    self.watched_urls["rss"][source_id].append(entry_id)

            # 監視済みURLを保存
            self._save_watched_urls()

            if self.logger:
                self.logger.success(f"RSS取得完了: {source['name']} - 新着{len(new_entries)}件")

            return new_entries

        except Exception as e:
            if self.logger:
                self.logger.error(f"RSS取得エラー: {source['name']} - {e}")
            return []