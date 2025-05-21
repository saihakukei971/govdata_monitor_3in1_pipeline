from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urlparse, urljoin
import m3u8


class VideoParser:
    """動画ページとm3u8ファイルの解析を行うクラス"""

    def __init__(self, logger=None):
        self.logger = logger

    def parse_video_page(self, html_content, source_url, video_selector=None, source_name=""):
        """動画ページを解析して動画情報を抽出"""
        try:
            if self.logger:
                self.logger.info(f"動画ページ解析開始: {source_name}")

            # BeautifulSoupで解析
            soup = BeautifulSoup(html_content, 'html.parser')

            # ベースURLの取得
            parsed_url = urlparse(source_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

            # セレクタが指定されている場合はそれに従って要素を抽出
            video_elements = []
            if video_selector:
                video_elements = soup.select(video_selector)

            # 動画情報のリスト
            videos = []

            for element in video_elements:
                # 動画URLの抽出
                video_url = self._extract_video_url(element, base_url, source_url)

                if video_url:
                    # タイトルの抽出
                    title = self._extract_video_title(element, soup)

                    # 動画情報の構築
                    video_info = {
                        'url': video_url,
                        'title': title or f"{source_name}の動画",
                        'source_name': source_name,
                        'source_url': source_url
                    }

                    videos.append(video_info)

            # セレクタで見つからない場合はページ全体から探す
            if not videos:
                # video要素を探す
                for video in soup.find_all('video'):
                    video_url = self._extract_video_url(video, base_url, source_url)

                    if video_url:
                        title = self._extract_video_title(video, soup)

                        video_info = {
                            'url': video_url,
                            'title': title or f"{source_name}の動画",
                            'source_name': source_name,
                            'source_url': source_url
                        }

                        videos.append(video_info)

                # iframe要素を探す
                for iframe in soup.find_all('iframe'):
                    if iframe.has_attr('src'):
                        iframe_src = iframe['src']

                        # YouTubeなどの埋め込み動画
                        if 'youtube.com' in iframe_src or 'youtu.be' in iframe_src or 'vimeo.com' in iframe_src:
                            title = self._extract_video_title(iframe, soup)

                            video_info = {
                                'url': iframe_src,
                                'title': title or f"{source_name}の動画",
                                'source_name': source_name,
                                'source_url': source_url,
                                'embed': True
                            }

                            videos.append(video_info)

                # JavaScriptから動画URLを探す
                js_videos = self._extract_videos_from_js(soup, base_url)
                videos.extend(js_videos)

            if self.logger:
                self.logger.success(f"動画ページ解析完了: {source_name} - {len(videos)}件の動画を検出")

            return videos

        except Exception as e:
            if self.logger:
                self.logger.error(f"動画ページ解析例外: {source_name} - {e}")
            return []

    def _extract_video_url(self, element, base_url, page_url):
        """要素から動画URLを抽出"""
        # video要素から直接取得
        if element.name == 'video' and element.has_attr('src'):
            return self._normalize_url(element['src'], base_url, page_url)

        # video > source要素から取得
        source = element.find('source')
        if source and source.has_attr('src'):
            return self._normalize_url(source['src'], base_url, page_url)

        # aタグのhref属性から取得
        if element.name == 'a' and element.has_attr('href'):
            href = element['href']

            # 動画ファイル拡張子を持つリンク
            if re.search(r'\.(mp4|m3u8|mov|avi|wmv)(\?.*)?$', href, re.IGNORECASE):
                return self._normalize_url(href, base_url, page_url)

        # data-src属性から取得（遅延読み込み対応）
        if element.has_attr('data-src'):
            return self._normalize_url(element['data-src'], base_url, page_url)

        return None

    def _normalize_url(self, url, base_url, page_url):
        """URLを正規化（相対パスを絶対パスに変換）"""
        if not url.startswith(('http://', 'https://')):
            if url.startswith('//'):
                # プロトコル相対URLの場合
                parsed = urlparse(page_url)
                return f"{parsed.scheme}:{url}"
            elif url.startswith('/'):
                # ルート相対パスの場合
                return f"{base_url}{url}"
            else:
                # 相対パスの場合
                return urljoin(page_url, url)

        return url

    def _extract_video_title(self, element, soup):
        """動画のタイトルを抽出"""
        # 要素自体にタイトルがある場合
        if element.get_text(strip=True):
            return element.get_text(strip=True)

        # 親要素または兄弟要素からタイトルを探す
        parent = element.parent

        # 見出し要素を探す
        for heading_tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            # 親要素内の見出し
            heading = parent.find(heading_tag)
            if heading:
                return heading.get_text(strip=True)

            # 近くの見出し
            prev_heading = element.find_previous(heading_tag)
            if prev_heading:
                return prev_heading.get_text(strip=True)

        # titleタグからタイトルを取得
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)

        return None

    def _extract_videos_from_js(self, soup, base_url):
        """JavaScriptから動画URLを抽出"""
        videos = []

        scripts = soup.find_all('script')
        for script in scripts:
            if not script.string:
                continue

            # m3u8ファイルパターン検索
            m3u8_matches = re.findall(r'[\'"]((https?://[^\'"\s]+\.m3u8)[^\'"]*)[\'"]', script.string)
            for match in m3u8_matches:
                videos.append({
                    'url': match[0],
                    'title': f"m3u8動画 {len(videos)+1}",
                    'format': 'm3u8'
                })

            # mp4ファイルパターン検索
            mp4_matches = re.findall(r'[\'"]((https?://[^\'"\s]+\.mp4)[^\'"]*)[\'"]', script.string)
            for match in mp4_matches:
                videos.append({
                    'url': match[0],
                    'title': f"mp4動画 {len(videos)+1}",
                    'format': 'mp4'
                })

            # JSON文字列を探す
            json_objects = re.findall(r'({[^{}]*"url"[^{}]*})', script.string)
            for json_obj in json_objects:
                try:
                    # JSON文字列の修正（JavaScript -> JSON）
                    json_str = re.sub(r'([{,])\s*(\w+):', r'\1"\2":', json_obj)
                    data = json.loads(json_str)

                    if 'url' in data:
                        url = data['url']
                        if isinstance(url, str) and (url.endswith('.mp4') or url.endswith('.m3u8')):
                            videos.append({
                                'url': url,
                                'title': data.get('title', f"JSON動画 {len(videos)+1}"),
                                'format': url.split('.')[-1]
                            })
                except Exception:
                    pass

        return videos

    def parse_m3u8(self, m3u8_content, url):
        """m3u8ファイルを解析して最高画質のプレイリストを取得"""
        try:
            if self.logger:
                self.logger.info(f"m3u8解析開始: {url}")

            m3u8_obj = m3u8.loads(m3u8_content)

            # プレイリストがある場合（マスタープレイリスト）
            if m3u8_obj.playlists:
                # 最高画質のプレイリストを選択
                best_playlist = max(m3u8_obj.playlists, key=lambda p: p.stream_info.bandwidth)

                result = {
                    'type': 'master',
                    'url': url,
                    'best_quality_url': self._normalize_url(best_playlist.uri, '', url),
                    'bandwidth': best_playlist.stream_info.bandwidth,
                    'resolution': best_playlist.stream_info.resolution,
                    'variants': len(m3u8_obj.playlists)
                }

                if self.logger:
                    self.logger.success(f"m3u8マスタープレイリスト解析完了: {url} - 最高画質: {result['resolution']}")

                return result

            # セグメントがある場合（メディアプレイリスト）
            if m3u8_obj.segments:
                segments = []

                for segment in m3u8_obj.segments:
                    segments.append({
                        'uri': self._normalize_url(segment.uri, '', url),
                        'duration': segment.duration
                    })

                result = {
                    'type': 'media',
                    'url': url,
                    'segments': segments,
                    'duration': sum(segment['duration'] for segment in segments),
                    'segment_count': len(segments)
                }

                if self.logger:
                    self.logger.success(f"m3u8メディアプレイリスト解析完了: {url} - セグメント数: {len(segments)}")

                return result

            # プレイリストもセグメントもない場合
            if self.logger:
                self.logger.warning(f"m3u8解析: プレイリストもセグメントも見つかりません: {url}")

            return {
                'type': 'unknown',
                'url': url
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"m3u8解析例外: {url} - {e}")

            return {
                'type': 'error',
                'url': url,
                'error': str(e)
            }