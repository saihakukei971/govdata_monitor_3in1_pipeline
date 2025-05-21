from datetime import datetime
import feedparser


class RSSParser:
    """RSSフィードの解析を行うクラス"""

    def __init__(self, logger=None):
        self.logger = logger

    def parse(self, feed_content, source_name=""):
        """RSSフィードを解析してエントリのリストを返す"""
        try:
            if self.logger:
                self.logger.info(f"RSSパース開始: {source_name}")

            # 文字列の場合はfeedparserで解析
            if isinstance(feed_content, str):
                feed = feedparser.parse(feed_content)
            else:
                feed = feed_content

            # パース失敗の場合
            if feed.bozo and not feed.entries:
                if self.logger:
                    self.logger.error(f"RSSパースエラー: {source_name} - {feed.bozo_exception}")
                return []

            entries = []

            for entry in feed.entries:
                # エントリのURLまたはIDを取得
                entry_id = entry.get('link', entry.get('id', ''))

                # 公開日時の取得と変換
                published = entry.get('published_parsed') or entry.get('updated_parsed')
                if published:
                    published_date = datetime(*published[:6]).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    published_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # エントリデータの構築
                entry_data = {
                    'title': entry.get('title', 'タイトルなし'),
                    'link': entry_id,
                    'published': published_date,
                    'source': source_name,
                    'description': entry.get('description', entry.get('summary', ''))
                }

                entries.append(entry_data)

            if self.logger:
                self.logger.success(f"RSSパース完了: {source_name} - {len(entries)}件")

            return entries

        except Exception as e:
            if self.logger:
                self.logger.error(f"RSSパース例外: {source_name} - {e}")
            return []

    def extract_feed_metadata(self, feed_content):
        """フィードのメタデータを抽出"""
        try:
            if isinstance(feed_content, str):
                feed = feedparser.parse(feed_content)
            else:
                feed = feed_content

            feed_info = feed.get('feed', {})

            metadata = {
                'title': feed_info.get('title', '不明なフィード'),
                'link': feed_info.get('link', ''),
                'description': feed_info.get('description', feed_info.get('subtitle', '')),
                'language': feed_info.get('language', ''),
                'updated': feed_info.get('updated', '')
            }

            return metadata

        except Exception as e:
            if self.logger:
                self.logger.error(f"フィードメタデータ抽出エラー: {e}")
            return {
                'title': '不明なフィード',
                'link': '',
                'description': '',
                'language': '',
                'updated': ''
            }