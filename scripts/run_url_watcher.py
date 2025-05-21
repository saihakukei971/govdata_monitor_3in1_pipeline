import sys
import os
import yaml
from pathlib import Path
from datetime import datetime

# パス設定
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from src.utils.logger import get_logger
from src.fetcher.rss_fetcher import RSSFetcher
from src.fetcher.html_scraper import HTMLScraper
from src.utils.notifier import Notifier


def load_config():
    """設定ファイルの読み込み"""
    config_file = root_dir / "config" / "settings.yaml"

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"設定ファイルの読み込みエラー: {e}")
        sys.exit(1)


def main():
    """URL監視メインスクリプト"""
    # 設定の読み込み
    config = load_config()

    # ログディレクトリ
    log_dir = root_dir / config["general"]["log_dir"]
    log_dir.mkdir(exist_ok=True, parents=True)

    # データディレクトリ
    data_dir = root_dir / config["general"]["data_dir"]
    data_dir.mkdir(exist_ok=True, parents=True)

    # ロガーの初期化
    logger = get_logger(log_dir=log_dir)
    logger.info("URL監視処理を開始します")

    # RSSフェッチャーの初期化
    rss_fetcher = RSSFetcher(data_dir=data_dir, logger=logger)

    # HTMLスクレイパーの初期化
    html_scraper = HTMLScraper(data_dir=data_dir, logger=logger)

    # 通知モジュールの初期化
    notifier = Notifier(config["notification"], logger=logger)

    # RSS取得処理
    rss_entries = []
    for source in config["rss_sources"]:
        if source.get("enabled", True):
            entries = rss_fetcher.fetch(source)
            rss_entries.extend(entries)

    # HTML取得処理
    html_entries = []
    for source in config["html_sources"]:
        if source.get("enabled", True):
            entries = html_scraper.fetch(source)
            html_entries.extend(entries)

    # 全エントリの結合
    all_entries = rss_entries + html_entries

    # 新着情報の通知
    if all_entries:
        logger.info(f"合計 {len(all_entries)} 件の新着情報を検出しました")
        notifier.notify_url_updates(all_entries)
    else:
        logger.info("新着情報はありませんでした")

    logger.info("URL監視処理が完了しました")


if __name__ == "__main__":
    main()