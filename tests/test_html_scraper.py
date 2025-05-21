import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import sys
import json
import requests

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from src.fetcher.html_scraper import HTMLScraper


class TestHTMLScraper(unittest.TestCase):
    """HTMLScraper のユースケース別徹底検証"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = self.temp_dir.name
        self.mock_logger = MagicMock()
        self.scraper = HTMLScraper(data_dir=self.data_dir, logger=self.mock_logger)

        self.sample_source = {
            "name": "官報HTML監視",
            "url": "https://example.com/news",
            "selector": ".news-item",
            "enabled": True
        }

        self.sample_html = '''
        <html><body>
            <div class="news-item">
                <a href="/article1">記事A</a>
            </div>
            <div class="news-item">
                <a href="https://example.com/article2">記事B</a>
            </div>
            <div class="news-item"> <!-- a無し -->
                <p>リンクなし記事</p>
            </div>
        </body></html>
        '''

    @patch("src.fetcher.html_scraper.requests.get")
    def test_scrape_extracts_new_links(self, mock_get):
        """正常系: リンク2件抽出 & watched登録"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self.sample_html
        mock_get.return_value = mock_response

        new_links = self.scraper.fetch(self.sample_source)

        expected = [
            "https://example.com/article1",
            "https://example.com/article2"
        ]
        self.assertEqual(sorted(new_links), sorted(expected))
        self.assertIn(self.sample_source["url"], self.scraper.watched_urls["html"])
        self.assertTrue(len(self.scraper.watched_urls["html"][self.sample_source["url"]]) >= 2)

    def test_watched_url_storage_and_reload(self):
        """watched_urls.jsonの読み書き"""
        self.scraper.watched_urls["html"]["dummy"] = ["https://example.com/test"]
        self.scraper._save_watched_urls()

        reloaded = HTMLScraper(data_dir=self.data_dir, logger=self.mock_logger)
        self.assertEqual(reloaded.watched_urls["html"]["dummy"], ["https://example.com/test"])

    @patch("src.fetcher.html_scraper.requests.get")
    def test_connection_error_handling(self, mock_get):
        mock_get.side_effect = requests.RequestException("失敗")
        result = self.scraper.fetch(self.sample_source)
        self.assertEqual(result, [])
        self.mock_logger.error.assert_called()

    @patch("src.fetcher.html_scraper.requests.get")
    def test_selector_yields_no_elements(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><p>見つからない</p></body></html>"
        mock_get.return_value = mock_response

        result = self.scraper.fetch(self.sample_source)
        self.assertEqual(result, [])
        self.mock_logger.info.assert_called()

    def tearDown(self):
        self.temp_dir.cleanup()
