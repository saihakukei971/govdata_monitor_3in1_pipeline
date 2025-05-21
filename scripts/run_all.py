import sys
import os
import yaml
import subprocess
from pathlib import Path
from datetime import datetime

# パス設定
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from src.utils.logger import get_logger


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
    """すべての監視処理を一括実行"""
    # 設定の読み込み
    config = load_config()

    # ログディレクトリ
    log_dir = root_dir / config["general"]["log_dir"]
    log_dir.mkdir(exist_ok=True, parents=True)

    # ロガーの初期化
    logger = get_logger(log_dir=log_dir)
    logger.info("一括監視処理を開始します")

    # URL監視スクリプトの実行
    logger.info("URL監視処理を実行します")
    url_watcher_script = root_dir / "scripts" / "run_url_watcher.py"

    url_result = subprocess.run(
        [sys.executable, str(url_watcher_script)],
        capture_output=True,
        text=True
    )

    if url_result.returncode == 0:
        logger.success("URL監視処理が正常に完了しました")
    else:
        logger.error(f"URL監視処理でエラーが発生しました: {url_result.stderr}")

    # 動画監視スクリプトの実行
    logger.info("動画監視処理を実行します")
    video_watcher_script = root_dir / "scripts" / "run_video_watcher.py"

    video_result = subprocess.run(
        [sys.executable, str(video_watcher_script)],
        capture_output=True,
        text=True
    )

    if video_result.returncode == 0:
        logger.success("動画監視処理が正常に完了しました")
    else:
        logger.error(f"動画監視処理でエラーが発生しました: {video_result.stderr}")

    logger.info("一括監視処理が完了しました")


if __name__ == "__main__":
    main()