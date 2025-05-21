import sys
import os
import yaml
from pathlib import Path
from datetime import datetime

# パス設定
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from src.utils.logger import get_logger
from src.fetcher.video_fetcher import VideoFetcher
from src.processor.video_capture import VideoCapture
from src.processor.transcriber import Transcriber
from src.processor.summarizer import Summarizer
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


def load_secrets():
    """秘密キー設定ファイルの読み込み"""
    secrets_file = root_dir / "config" / "secrets.yaml"

    if not secrets_file.exists():
        return {}

    try:
        with open(secrets_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"秘密キー設定ファイルの読み込みエラー: {e}")
        return {}


def main():
    """動画監視メインスクリプト"""
    # 設定の読み込み
    config = load_config()
    secrets = load_secrets()

    # ログディレクトリ
    log_dir = root_dir / config["general"]["log_dir"]
    log_dir.mkdir(exist_ok=True, parents=True)

    # データディレクトリ
    data_dir = root_dir / config["general"]["data_dir"]
    data_dir.mkdir(exist_ok=True, parents=True)

    # ロガーの初期化
    logger = get_logger(log_dir=log_dir)
    logger.info("動画監視処理を開始します")

    # 動画フェッチャーの初期化
    video_fetcher = VideoFetcher(data_dir=data_dir, logger=logger)

    # 動画キャプチャの初期化
    video_capture = VideoCapture(data_dir=data_dir, logger=logger)

    # 文字起こしモジュールの初期化
    transcriber = Transcriber(data_dir=data_dir, logger=logger)

    # 要約モジュールの初期化
    openai_api_key = secrets.get("openai_api_key", os.environ.get("OPENAI_API_KEY"))
    summarizer = Summarizer(data_dir=data_dir, logger=logger, api_key=openai_api_key)

    # 通知モジュールの初期化
    notifier = Notifier(config["notification"], logger=logger)

    # 動画取得処理
    new_videos = []
    processed_videos = []

    for source in config["video_sources"]:
        if source.get("enabled", True):
            videos = video_fetcher.fetch(source)
            new_videos.extend(videos)

    # 見つかった動画の処理
    for video in new_videos:
        # キャプチャ処理
        metadata = video_capture.capture(video)

        if metadata and video.get("summarize", True):
            # 文字起こし処理
            transcript = transcriber.transcribe(video)

            if transcript:
                # 要約処理
                summary = summarizer.summarize(transcript)

                if summary:
                    processed_video = {
                        "id": video["id"],
                        "title": video["title"],
                        "url": video["url"],
                        "source_name": video["source_name"],
                        "source_url": video["source_url"],
                        "processed_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "summary": summary.get("summary", "要約なし"),
                        "screenshots": metadata.get("screenshots", [])
                    }

                    processed_videos.append(processed_video)

    # 新着動画の通知
    if processed_videos:
        logger.info(f"合計 {len(processed_videos)} 件の動画を処理しました")
        notifier.notify_video_updates(processed_videos)
    else:
        logger.info("新着動画はありませんでした")

    logger.info("動画監視処理が完了しました")


if __name__ == "__main__":
    main()