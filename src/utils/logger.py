import logging
import os
from datetime import datetime
from pathlib import Path


class Logger:
    """日付ごとのログファイルに追記形式で記録するロガー"""

    def __init__(self, log_dir="logs", app_name="GovInfoWatcher"):
        self.log_dir = Path(log_dir)
        self.app_name = app_name

        # ログディレクトリが存在しない場合は作成
        self.log_dir.mkdir(exist_ok=True, parents=True)

        # 今日の日付のログファイル名
        self.log_file = self.log_dir / f"{datetime.now().strftime('%Y%m%d')}.log"

        # ロガーの設定
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(logging.INFO)

        # すでにハンドラが設定されている場合は追加しない
        if not self.logger.handlers:
            # ファイルハンドラ (追記モード)
            file_handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
            file_handler.setLevel(logging.INFO)

            # コンソールハンドラ
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)

            # フォーマッタ
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # ハンドラの追加
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def info(self, message):
        """情報ログを記録"""
        self.logger.info(message)

    def error(self, message):
        """エラーログを記録"""
        self.logger.error(message)

    def warning(self, message):
        """警告ログを記録"""
        self.logger.warning(message)

    def debug(self, message):
        """デバッグログを記録"""
        self.logger.debug(message)

    def success(self, message):
        """成功ログを記録 (INFOレベルで記録)"""
        self.logger.info(f"✅ {message}")


# グローバルなロガーインスタンス
def get_logger(log_dir="logs"):
    return Logger(log_dir=log_dir)