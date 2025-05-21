import sqlite3
import json
from pathlib import Path
from datetime import datetime


class DBStorage:
    """SQLiteデータベースへのデータ保存を管理するクラス"""

    def __init__(self, data_dir="data", db_name="govinfo.db", logger=None):
        self.data_dir = Path(data_dir)
        self.logger = logger

        # データディレクトリが存在しない場合は作成
        self.data_dir.mkdir(exist_ok=True, parents=True)

        # データベースファイルのパス
        self.db_path = self.data_dir / db_name

        # データベースの初期化
        self._init_db()

    def _init_db(self):
        """データベースの初期化"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # RSS/HTMLエントリテーブルの作成
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS url_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                published TEXT,
                source TEXT,
                description TEXT,
                source_type TEXT NOT NULL,
                fetch_date TEXT NOT NULL,
                json_data TEXT
            )
            ''')

            # 動画エントリテーブルの作成
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                source_name TEXT,
                source_url TEXT,
                found_date TEXT NOT NULL,
                processed_date TEXT,
                summary TEXT,
                transcript TEXT,
                thumbnail_path TEXT,
                json_data TEXT
            )
            ''')

            # URLインデックスの作成
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_url_link ON url_entries (link)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_url ON video_entries (url)')

            conn.commit()
            conn.close()

            if self.logger:
                self.logger.info(f"データベース初期化成功: {self.db_path}")

        except Exception as e:
            if self.logger:
                self.logger.error(f"データベース初期化エラー: {e}")

    def save_url_entry(self, entry, source_type='rss'):
        """URL情報をデータベースに保存"""
        try:
            # エントリデータの検証
            if not isinstance(entry, dict):
                raise ValueError("エントリはdict型である必要があります")

            if 'link' not in entry or 'title' not in entry:
                raise ValueError("エントリにはlinkとtitleが必要です")

            # 既存エントリの確認
            if self.url_entry_exists(entry['link']):
                if self.logger:
                    self.logger.info(f"既存のURLエントリをスキップ: {entry['link']}")
                return False

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 現在の日時
            fetch_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # JSONデータ
            json_data = json.dumps(entry, ensure_ascii=False)

            # データ挿入
            cursor.execute('''
            INSERT INTO url_entries
            (title, link, published, source, description, source_type, fetch_date, json_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.get('title', ''),
                entry['link'],
                entry.get('published', fetch_date),
                entry.get('source', ''),
                entry.get('description', ''),
                source_type,
                fetch_date,
                json_data
            ))

            conn.commit()
            conn.close()

            if self.logger:
                self.logger.info(f"URLエントリ保存成功: {entry['title']} ({entry['link']})")

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"URLエントリ保存エラー: {e}")
            return False

    def url_entry_exists(self, link):
        """URLエントリが既に存在するか確認"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT id FROM url_entries WHERE link = ?', (link,))
            result = cursor.fetchone()

            conn.close()

            return result is not None

        except Exception as e:
            if self.logger:
                self.logger.error(f"URLエントリ存在確認エラー: {e}")
            return False

    def get_url_entries(self, limit=100, source_type=None, source=None):
        """URLエントリを取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = 'SELECT * FROM url_entries'
            params = []

            conditions = []

            if source_type:
                conditions.append('source_type = ?')
                params.append(source_type)

            if source:
                conditions.append('source = ?')
                params.append(source)

            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)

            query += ' ORDER BY fetch_date DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            entries = []
            for row in rows:
                entry = dict(row)

                # JSON文字列をパース
                if entry['json_data']:
                    try:
                        json_data = json.loads(entry['json_data'])
                        entry.update(json_data)
                    except Exception:
                        pass

                # json_dataフィールドは不要
                entry.pop('json_data', None)

                entries.append(entry)

            conn.close()

            if self.logger:
                self.logger.info(f"URLエントリ取得成功: {len(entries)}件")

            return entries

        except Exception as e:
            if self.logger:
                self.logger.error(f"URLエントリ取得エラー: {e}")
            return []

    def save_video_entry(self, video):
        """動画情報をデータベースに保存"""
        try:
            # エントリデータの検証
            if not isinstance(video, dict):
                raise ValueError("エントリはdict型である必要があります")

            if 'url' not in video or 'title' not in video:
                raise ValueError("エントリにはurlとtitleが必要です")

            # 既存エントリの確認
            if self.video_entry_exists(video['url']):
                if self.logger:
                    self.logger.info(f"既存の動画エントリをスキップ: {video['url']}")
                return False

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 現在の日時
            found_date = video.get('found_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            # JSONデータ
            json_data = json.dumps(video, ensure_ascii=False)

            # データ挿入
            cursor.execute('''
            INSERT INTO video_entries
            (title, url, source_name, source_url, found_date, processed_date, summary, transcript, thumbnail_path, json_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video.get('title', ''),
                video['url'],
                video.get('source_name', ''),
                video.get('source_url', ''),
                found_date,
                video.get('processed_date', None),
                video.get('summary', None),
                video.get('transcript', None),
                video.get('thumbnail_path', None),
                json_data
            ))

            conn.commit()
            conn.close()

            if self.logger:
                self.logger.info(f"動画エントリ保存成功: {video['title']} ({video['url']})")

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"動画エントリ保存エラー: {e}")
            return False

    def video_entry_exists(self, url):
        """動画エントリが既に存在するか確認"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT id FROM video_entries WHERE url = ?', (url,))
            result = cursor.fetchone()

            conn.close()

            return result is not None

        except Exception as e:
            if self.logger:
                self.logger.error(f"動画エントリ存在確認エラー: {e}")
            return False

    def update_video_entry(self, url, updates):
        """動画エントリを更新"""
        try:
            if not self.video_entry_exists(url):
                if self.logger:
                    self.logger.warning(f"更新対象の動画エントリが見つかりません: {url}")
                return False

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 更新項目の構築
            update_cols = []
            update_vals = []

            for key, value in updates.items():
                if key in ['title', 'source_name', 'source_url', 'processed_date', 'summary', 'transcript', 'thumbnail_path']:
                    update_cols.append(f"{key} = ?")
                    update_vals.append(value)

            # JSONデータの更新
            cursor.execute('SELECT json_data FROM video_entries WHERE url = ?', (url,))
            result = cursor.fetchone()

            if result and result[0]:
                try:
                    json_data = json.loads(result[0])
                    json_data.update(updates)

                    update_cols.append("json_data = ?")
                    update_vals.append(json.dumps(json_data, ensure_ascii=False))
                except Exception:
                    pass

            if not update_cols:
                if self.logger:
                    self.logger.warning(f"更新項目がありません: {url}")
                conn.close()
                return False

            # 更新クエリの実行
            query = f"UPDATE video_entries SET {', '.join(update_cols)} WHERE url = ?"
            update_vals.append(url)

            cursor.execute(query, update_vals)

            conn.commit()
            conn.close()

            if self.logger:
                self.logger.info(f"動画エントリ更新成功: {url}")

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"動画エントリ更新エラー: {e}")
            return False

    def get_video_entries(self, limit=100, source_name=None, processed=None):
        """動画エントリを取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = 'SELECT * FROM video_entries'
            params = []

            conditions = []

            if source_name:
                conditions.append('source_name = ?')
                params.append(source_name)

            if processed is not None:
                if processed:
                    conditions.append('processed_date IS NOT NULL')
                else:
                    conditions.append('processed_date IS NULL')

            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)

            query += ' ORDER BY found_date DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            videos = []
            for row in rows:
                video = dict(row)

                # JSON文字列をパース
                if video['json_data']:
                    try:
                        json_data = json.loads(video['json_data'])
                        video.update(json_data)
                    except Exception:
                        pass

                # json_dataフィールドは不要
                video.pop('json_data', None)

                videos.append(video)

            conn.close()

            if self.logger:
                self.logger.info(f"動画エントリ取得成功: {len(videos)}件")

            return videos

        except Exception as e:
            if self.logger:
                self.logger.error(f"動画エントリ取得エラー: {e}")
            return []