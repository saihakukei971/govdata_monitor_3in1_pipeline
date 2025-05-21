import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
from datetime import datetime
import hashlib


class HTMLScraper:
    """固定URLからHTMLを取得して解析するクラス"""

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

    def _get_content_hash(self, content):
        """コンテンツのハッシュ値を取得"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def fetch(self, source):
        """HTML固定ページから新着情報を取得"""
        if self.logger:
            self.logger.info(f"HTML取得開始: {source['name']} ({source['url']})")

        # HTMLの取得
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(source['url'], headers=headers, timeout=30)
            response.raise_for_status()

            # 文字コードを適切に設定
            response.encoding = response.apparent_encoding

            # HTMLの解析
            soup = BeautifulSoup(response.text, 'html.parser')

            # セレクタが指定されている場合はそれに従って要素を抽出
            items = []
            if 'selector' in source and source['selector']:
                items = soup.select(source['selector'])

            # 新着情報の抽出
            new_entries = []
            source_id = source['url']

            # ソースIDがwatched_urlsに存在しない場合は初期化
            if source_id not in self.watched_urls["html"]:
                self.watched_urls["html"][source_id] = []

            for item in items:
                # タイトルの抽出
                title = item.get_text(strip=True)

                # リンクの抽出
                link = item.find('a')
                if link and link.has_attr('href'):
                    link_url = link['href']

                    # 相対URLを絶対URLに変換
                    if link_url.startswith('/'):
                        from urllib.parse import urlparse
                        parsed_url = urlparse(source['url'])
                        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        link_url = base_url + link_url
                else:
                    # リンクがない場合は要素のハッシュ値をIDとして使用
                    link_url = source['url'] + '#' + self._get_content_hash(title)

                # 新着判定
                if link_url not in self.watched_urls["html"][source_id]:
                    # 新着エントリとして追加
                    new_entries.append({
                        'title': title,
                        'link': link_url,
                        'published': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'source': source['name']
                    })

                    # 監視済みURLに追加
                    self.watched_urls["html"][source_id].append(link_url)

            # 監視済みURLを保存
            self._save_watched_urls()

            if self.logger:
                self.logger.success(f"HTML取得完了: {source['name']} - 新着{len(new_entries)}件")

            return new_entries

        except Exception as e:
            if self.logger:
                self.logger.error(f"HTML取得エラー: {source['name']} - {e}")
            return []