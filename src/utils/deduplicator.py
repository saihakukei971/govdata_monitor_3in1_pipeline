import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta


class Deduplicator:
    """重複データの検出と排除を行うクラス"""

    def __init__(self, data_dir="data", watched_file="watched_urls.json", logger=None):
        self.data_dir = Path(data_dir)
        self.logger = logger

        # データディレクトリが存在しない場合は作成
        self.data_dir.mkdir(exist_ok=True, parents=True)

        # 監視済みURLの保存ファイル
        self.watched_file = self.data_dir / watched_file

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

    def _get_content_hash(self, content):
        """コンテンツのハッシュ値を取得"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def is_new_url(self, url, source_id, source_type='rss'):
        """URLが新規かどうかを判定"""
        # ソースIDがwatched_urlsに存在しない場合は初期化
        if source_id not in self.watched_urls[source_type]:
            self.watched_urls[source_type][source_id] = []

        # 新規判定
        is_new = url not in self.watched_urls[source_type][source_id]

        if is_new and self.logger:
            self.logger.info(f"新規URL検出: {url}")

        return is_new

    def mark_as_processed(self, url, source_id, source_type='rss'):
        """URLを処理済みとしてマーク"""
        # ソースIDがwatched_urlsに存在しない場合は初期化
        if source_id not in self.watched_urls[source_type]:
            self.watched_urls[source_type][source_id] = []

        # 既に処理済みの場合はスキップ
        if url in self.watched_urls[source_type][source_id]:
            return False

        # 処理済みURLに追加
        self.watched_urls[source_type][source_id].append(url)

        # 監視済みURLを保存
        self._save_watched_urls()

        if self.logger:
            self.logger.info(f"URL処理済みマーク: {url}")

        return True

    def remove_old_urls(self, days=30):
        """古いURLをリストから削除"""
        try:
            # 現在の日時
            now = datetime.now()

            # 日数の指定がない場合は何もしない
            if days <= 0:
                return 0

            # 日付付きURLのみを残す（日付がないURLは削除しない）
            total_removed = 0

            # RSSエントリの処理
            for source_id in self.watched_urls["rss"]:
                old_urls = []

                for url in self.watched_urls["rss"][source_id]:
                    # URLに日付があるか確認（例: YYYY/MM/DD形式やYYYYMMDD形式）
                    date_found = False

                    # 日付の検出（YYYY/MM/DD形式）
                    for year in range(now.year - 5, now.year + 1):
                        if str(year) in url:
                            date_found = True

                            # 現在から指定日数前の日付
                            cutoff_date = now - timedelta(days=days)

                            # URLの日付が古いか確認
                            if str(year) < str(cutoff_date.year):
                                old_urls.append(url)
                                break

                    # 日付が見つからなかった場合は何もしない
                    if not date_found:
                        continue

                # 古いURLを削除
                for url in old_urls:
                    self.watched_urls["rss"][source_id].remove(url)
                    total_removed += 1

            # 監視済みURLを保存
            self._save_watched_urls()

            if self.logger:
                self.logger.info(f"古いURL削除完了: {total_removed}件")

            return total_removed

        except Exception as e:
            if self.logger:
                self.logger.error(f"古いURL削除エラー: {e}")
            return 0

    def filter_duplicates(self, entries, key_field='link'):
        """エントリの重複を排除"""
        try:
            # 重複チェック用のセット
            seen = set()
            unique_entries = []

            for entry in entries:
                # キーフィールドがない場合はスキップ
                if key_field not in entry:
                    continue

                key = entry[key_field]

                # 重複チェック
                if key not in seen:
                    seen.add(key)
                    unique_entries.append(entry)

            if self.logger:
                removed = len(entries) - len(unique_entries)
                if removed > 0:
                    self.logger.info(f"重複エントリ排除: {removed}件")

            return unique_entries

        except Exception as e:
            if self.logger:
                self.logger.error(f"重複排除エラー: {e}")
            return entries