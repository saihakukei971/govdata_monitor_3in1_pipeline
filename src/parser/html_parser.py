from bs4 import BeautifulSoup
import re
from datetime import datetime
from urllib.parse import urlparse, urljoin


class HTMLParser:
    """HTMLページの解析を行うクラス"""

    def __init__(self, logger=None):
        self.logger = logger

    def parse(self, html_content, source_url, selector=None, source_name=""):
        """HTMLを解析してエントリのリストを返す"""
        try:
            if self.logger:
                self.logger.info(f"HTMLパース開始: {source_name}")

            # BeautifulSoupで解析
            soup = BeautifulSoup(html_content, 'html.parser')

            # ベースURLの取得
            parsed_url = urlparse(source_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

            # セレクタが指定されている場合はそれに従って要素を抽出
            elements = []
            if selector:
                elements = soup.select(selector)

            # エントリのリスト
            entries = []

            for element in elements:
                # タイトルの抽出
                title = element.get_text(strip=True)

                # リンクの抽出
                link = None
                a_tag = element.find('a')
                if a_tag and a_tag.has_attr('href'):
                    link_url = a_tag['href']

                    # 相対URLを絶対URLに変換
                    if not link_url.startswith(('http://', 'https://')):
                        if link_url.startswith('/'):
                            link_url = base_url + link_url
                        else:
                            link_url = urljoin(source_url, link_url)

                    link = link_url

                # 日付の抽出
                date_str = self._extract_date(element)
                if date_str:
                    published = date_str
                else:
                    published = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # エントリデータの構築
                entry_data = {
                    'title': title,
                    'link': link or source_url,
                    'published': published,
                    'source': source_name
                }

                entries.append(entry_data)

            if self.logger:
                self.logger.success(f"HTMLパース完了: {source_name} - {len(entries)}件")

            return entries

        except Exception as e:
            if self.logger:
                self.logger.error(f"HTMLパース例外: {source_name} - {e}")
            return []

    def _extract_date(self, element):
        """要素から日付を抽出"""
        # 日付を含むクラス名や要素を探す
        date_classes = ['date', 'time', 'datetime', 'published', 'updated']

        # クラスで探す
        for cls in date_classes:
            date_element = element.find(class_=re.compile(cls, re.IGNORECASE))
            if date_element:
                return date_element.get_text(strip=True)

        # time要素で探す
        time_element = element.find('time')
        if time_element:
            if time_element.has_attr('datetime'):
                return time_element['datetime']
            return time_element.get_text(strip=True)

        # 日付形式の文字列を探す
        text = element.get_text()

        # YYYY/MM/DD または YYYY-MM-DD 形式を探す
        date_match = re.search(r'\d{4}[/-]\d{1,2}[/-]\d{1,2}', text)
        if date_match:
            return date_match.group(0)

        # YYYY年MM月DD日 形式を探す
        date_match = re.search(r'\d{4}年\d{1,2}月\d{1,2}日', text)
        if date_match:
            return date_match.group(0)

        return None

    def extract_page_title(self, html_content):
        """ページタイトルを抽出"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            title_tag = soup.find('title')

            if title_tag:
                return title_tag.get_text(strip=True)
            else:
                # h1タグから取得
                h1_tag = soup.find('h1')
                if h1_tag:
                    return h1_tag.get_text(strip=True)

            return '不明なタイトル'

        except Exception as e:
            if self.logger:
                self.logger.error(f"ページタイトル抽出エラー: {e}")
            return '不明なタイトル'