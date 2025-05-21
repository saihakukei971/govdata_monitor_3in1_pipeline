import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import json
import tempfile

# プロジェクトのルートディレクトリをパスに追加
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from src.fetcher.rss_fetcher import RSSFetcher


class TestRSSFetcher(unittest.TestCase):
    """RSSFetcherクラスのテスト"""

    def setUp(self):
        """テスト前の準備"""
        # 一時ディレクトリの作成
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = self.temp_dir.name

        # モックロガー
        self.mock_logger = MagicMock()

        # RSSFetcherのインスタンス化
        self.rss_fetcher = RSSFetcher(data_dir=self.data_dir, logger=self.mock_logger)

        # サンプルRSSソース
        self.sample_source = {
            "name": "テスト RSS",
            "url": "https://example.com/rss.xml",
            "enabled": True
        }

    def tearDown(self):
        """テスト後のクリーンアップ"""
        # 一時ディレクトリの削除
        self.temp_dir.cleanup()

    def test_init(self):
        """初期化のテスト"""
        # データディレクトリが作成されているか
        self.assertTrue(Path(self.data_dir).exists())

        # watched_urlsが初期化されているか
        self.assertEqual(self.rss_fetcher.watched_urls, {"rss": {}, "html": {}, "video": {}})

    def test_load_watched_urls(self):
        """監視済みURLのロードテスト"""
        # サンプルデータの作成
        sample_data = {"rss": {"test": ["url1", "url2"]}, "html": {}, "video": {}}

        # ファイルに保存
        watched_file = Path(self.data_dir) / "watched_urls.json"
        with open(watched_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f)

        # データのロード
        result = self.rss_fetcher._load_watched_urls()

        # 期待される結果
        self.assertEqual(result, sample_data)

    def test_save_watched_urls(self):
        """監視済みURLの保存テスト"""
        # サンプルデータの設定
        self.rss_fetcher.watched_urls = {"rss": {"test": ["url1", "url2"]}, "html": {}, "video": {}}

        # データの保存
        self.rss_fetcher._save_watched_urls()

        # 保存されたファイルの読み込み
        watched_file = Path(self.data_dir) / "watched_urls.json"
        with open(watched_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        # 期待される結果
        self.assertEqual(loaded_data, self.rss_fetcher.watched_urls)

    @patch('feedparser.parse')
    def test_fetch_success(self, mock_parse):
        """RSS取得成功のテスト"""
        # モックの設定
        mock_entry = {
            'title': 'テスト記事',
            'link': 'https://example.com/article1',
            'published_parsed': (2023, 1, 1, 12, 0, 0, 0, 0, 0),
            'id': 'https://example.com/article1'
        }

        mock_parse.return_value = MagicMock(
            bozo=False,
            entries=[mock_entry]
        )

        # RSS取得の実行
        entries = self.rss_fetcher.fetch(self.sample_source)

        # 期待される結果
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['title'], 'テスト記事')
        self.assertEqual(entries[0]['link'], 'https://example.com/article1')

        # watched_urlsに追加されているか
        self.assertIn('https://example.com/article1', self.rss_fetcher.watched_urls["rss"]["https://example.com/rss.xml"])

    @patch('feedparser.parse')
    def test_fetch_error(self, mock_parse):
        """RSS取得エラーのテスト"""
        # モックの設定
        mock_parse.return_value = MagicMock(
            bozo=True,
            bozo_exception=Exception("RSS解析エラー"),
            entries=[]
        )

        # RSS取得の実行
        entries = self.rss_fetcher.fetch(self.sample_source)

        # 期待される結果
        self.assertEqual(entries, [])
        self.mock_logger.error.assert_called()

    @patch('feedparser.parse')
    def test_fetch_duplicate(self, mock_parse):
        """重複エントリのテスト"""
        # モックの設定
        mock_entry = {
            'title': 'テスト記事',
            'link': 'https://example.com/article1',
            'published_parsed': (2023, 1, 1, 12, 0, 0, 0, 0, 0),
            'id': 'https://example.com/article1'
        }

        mock_parse.return_value = MagicMock(
            bozo=False,
            entries=[mock_entry]
        )

        # 既に処理済みのURLを設定
        self.rss_fetcher.watched_urls["rss"]["https://example.com/rss.xml"] = ["https://example.com/article1"]

        # RSS取得の実行
        entries = self.rss_fetcher.fetch(self.sample_source)

        # 期待される結果（重複エントリは含まれない）
        self.assertEqual(entries, [])


if __name__ == '__main__':
    unittest.main()