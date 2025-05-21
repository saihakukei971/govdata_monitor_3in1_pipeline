import requests
from bs4 import BeautifulSoup
import json
import re
from pathlib import Path
from datetime import datetime
import hashlib
import m3u8


class VideoFetcher:
    """動画ページからビデオURLを取得するクラス"""

    def __init__(self, data_dir="data", logger=None):
        self.data_dir = Path(data_dir)
        self.logger = logger

        # データディレクトリが存在しない場合は作成
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.video_dir = self.data_dir / "video_captures"
        self.video_dir.mkdir(exist_ok=True, parents=True)

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

    def _extract_video_url(self, element, base_url):
        """ビデオURL抽出の共通処理"""
        # video要素から直接取得
        if element.name == 'video' and element.has_attr('src'):
            return element['src']

        # video > source要素から取得
        source = element.find('source')
        if source and source.has_attr('src'):
            return source['src']

        # aタグのhref属性から取得
        if element.name == 'a' and element.has_attr('href'):
            href = element['href']
            # 動画ファイル拡張子を持つリンク
            if re.search(r'\.(mp4|m3u8|mov|avi|wmv)(\?.*)?$', href, re.IGNORECASE):
                # 相対パスを絶対パスに変換
                if href.startswith('/'):
                    return f"{base_url}{href}"
                return href

            # iframe埋め込みを含むページへのリンク
            if not href.startswith('http'):
                if href.startswith('/'):
                    href = f"{base_url}{href}"
                else:
                    from urllib.parse import urljoin
                    href = urljoin(base_url, href)

            # リンク先ページを解析して動画URLを探す
            try:
                response = requests.get(href, timeout=30)
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                soup = BeautifulSoup(response.text, 'html.parser')

                # iframe検索
                iframe = soup.find('iframe')
                if iframe and iframe.has_attr('src'):
                    iframe_src = iframe['src']
                    if 'youtube.com' in iframe_src or 'youtu.be' in iframe_src:
                        return iframe_src

                # video要素検索
                video = soup.find('video')
                if video:
                    if video.has_attr('src'):
                        return video['src']
                    source = video.find('source')
                    if source and source.has_attr('src'):
                        return source['src']

                # JS内の動画URL検索
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string:
                        # m3u8ファイルパターン検索
                        m3u8_matches = re.findall(r'[\'"]((https?://[^\'"\s]+\.m3u8)[^\'"]*)[\'"]', script.string)
                        if m3u8_matches:
                            return m3u8_matches[0][0]

                        # mp4ファイルパターン検索
                        mp4_matches = re.findall(r'[\'"]((https?://[^\'"\s]+\.mp4)[^\'"]*)[\'"]', script.string)
                        if mp4_matches:
                            return mp4_matches[0][0]
            except Exception as e:
                if self.logger:
                    self.logger.error(f"リンク先解析エラー: {href} - {e}")

        return None

    def _process_m3u8(self, m3u8_url):
        """m3u8ファイルを解析して最高画質のビデオURLを取得"""
        try:
            response = requests.get(m3u8_url, timeout=30)
            response.raise_for_status()

            m3u8_obj = m3u8.loads(response.text)

            # プレイリストがある場合
            if m3u8_obj.playlists:
                # 最高画質のプレイリストを選択
                best_playlist = max(m3u8_obj.playlists, key=lambda p: p.stream_info.bandwidth)

                # 相対パスを絶対パスに変換
                if not best_playlist.uri.startswith('http'):
                    from urllib.parse import urljoin
                    return urljoin(m3u8_url, best_playlist.uri)

                return best_playlist.uri

            # セグメントがある場合
            if m3u8_obj.segments:
                return m3u8_url

        except Exception as e:
            if self.logger:
                self.logger.error(f"m3u8解析エラー: {m3u8_url} - {e}")

        return m3u8_url

    def fetch(self, source):
        """動画ページから新しい動画URLを取得"""
        if self.logger:
            self.logger.info(f"動画URL取得開始: {source['name']} ({source['url']})")

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

            # ベースURLの取得
            from urllib.parse import urlparse
            parsed_url = urlparse(source['url'])
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

            # セレクタが指定されている場合はそれに従って要素を抽出
            items = []
            if 'video_selector' in source and source['video_selector']:
                items = soup.select(source['video_selector'])

            # 動画URLのリストを取得
            new_videos = []
            source_id = source['url']

            # ソースIDがwatched_urlsに存在しない場合は初期化
            if source_id not in self.watched_urls["video"]:
                self.watched_urls["video"][source_id] = []

            for item in items:
                # 動画URLの抽出
                video_url = self._extract_video_url(item, base_url)

                if video_url:
                    # m3u8ファイルの場合は処理
                    if video_url.endswith('.m3u8'):
                        video_url = self._process_m3u8(video_url)

                    # タイトルの抽出
                    title = None
                    # 要素自体にタイトルがある場合
                    if item.get_text(strip=True):
                        title = item.get_text(strip=True)
                    # 親要素または兄弟要素からタイトルを探す
                    elif item.parent:
                        # h1, h2, h3, h4, h5, h6 を探す
                        for heading in item.parent.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                            title = heading.get_text(strip=True)
                            break

                        # titleがなければp要素を探す
                        if not title:
                            p = item.parent.find('p')
                            if p:
                                title = p.get_text(strip=True)
                    # タイトルが取得できなかった場合はURLから生成
                    if not title:
                        from urllib.parse import urlparse
                        parsed_video_url = urlparse(video_url)
                        title = f"{source['name']}の動画 - {Path(parsed_video_url.path).stem}"

                    # 新着判定
                    if video_url not in self.watched_urls["video"][source_id]:
                        # 新着動画として追加
                        video_id = self._get_content_hash(video_url)

                        new_videos.append({
                            'id': video_id,
                            'title': title,
                            'url': video_url,
                            'source_name': source['name'],
                            'source_url': source['url'],
                            'found_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'capture_interval': source.get('capture_interval', 5),
                            'summarize': source.get('summarize', True)
                        })

                        # 監視済みURLに追加
                        self.watched_urls["video"][source_id].append(video_url)

            # 監視済みURLを保存
            self._save_watched_urls()

            if self.logger:
                self.logger.success(f"動画URL取得完了: {source['name']} - 新着{len(new_videos)}件")

            return new_videos

        except Exception as e:
            if self.logger:
                self.logger.error(f"動画URL取得エラー: {source['name']} - {e}")
            return []