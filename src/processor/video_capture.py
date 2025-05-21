import subprocess
import os
import json
from pathlib import Path
import tempfile
from datetime import datetime
import re


class VideoCapture:
    """動画からスクリーンショットを取得するクラス"""

    def __init__(self, data_dir="data", logger=None):
        self.data_dir = Path(data_dir)
        self.logger = logger

        # データディレクトリが存在しない場合は作成
        self.data_dir.mkdir(exist_ok=True, parents=True)

        # 動画キャプチャ保存ディレクトリ
        self.captures_dir = self.data_dir / "video_captures"
        self.captures_dir.mkdir(exist_ok=True, parents=True)

    def _check_ffmpeg(self):
        """ffmpegがインストールされているか確認"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            return result.returncode == 0
        except Exception:
            return False

    def _get_video_duration(self, video_url):
        """動画の長さを取得"""
        try:
            # FFmpegを使用して動画の長さを取得
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                video_url
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )

            data = json.loads(result.stdout)
            duration = float(data["format"]["duration"])
            return duration

        except Exception as e:
            if self.logger:
                self.logger.error(f"動画長さ取得エラー: {video_url} - {e}")
            return 0

    def _sanitize_filename(self, filename):
        """ファイル名に使用できない文字を置換"""
        # ファイル名に使用できない文字を置換
        return re.sub(r'[\\/*?:"<>|]', "_", filename)

    def capture(self, video):
        """動画からスクリーンショットを取得"""
        if not self._check_ffmpeg():
            if self.logger:
                self.logger.error("ffmpegがインストールされていません")
            return None

        video_id = video["id"]
        video_url = video["url"]
        title = video["title"]

        # サムネイル保存用ディレクトリ
        video_capture_dir = self.captures_dir / video_id
        video_capture_dir.mkdir(exist_ok=True, parents=True)

        # メタ情報保存
        metadata = {
            "id": video_id,
            "title": title,
            "url": video_url,
            "source_name": video["source_name"],
            "source_url": video["source_url"],
            "capture_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "screenshots": []
        }

        # メタデータファイル
        metadata_file = video_capture_dir / "metadata.json"

        if self.logger:
            self.logger.info(f"動画キャプチャ開始: {title} ({video_url})")

        try:
            # 動画の長さを取得
            duration = self._get_video_duration(video_url)

            if duration <= 0:
                if self.logger:
                    self.logger.error(f"動画長さが取得できません: {video_url}")
                return None

            # キャプチャする時間間隔
            capture_interval = video.get("capture_interval", 5)

            # キャプチャ時間ポイントを計算
            if duration <= 30:
                # 30秒以下の動画なら冒頭、中間、終わり付近
                capture_points = [1, duration // 2, max(1, duration - 3)]
            else:
                # 長い動画なら等間隔で最大10枚
                max_captures = 10
                step = max(capture_interval, duration / max_captures)
                capture_points = [min(i * step, duration - 1) for i in range(1, max_captures + 1) if i * step < duration - 1]

            # スクリーンショット取得
            for i, time_point in enumerate(capture_points):
                screenshot_file = video_capture_dir / f"screenshot_{i:02d}.jpg"

                # すでに存在する場合はスキップ
                if screenshot_file.exists():
                    metadata["screenshots"].append({
                        "file": str(screenshot_file.relative_to(self.data_dir)),
                        "time": time_point,
                        "exists": True
                    })
                    continue

                # FFmpegでスクリーンショット取得
                cmd = [
                    "ffmpeg",
                    "-ss", str(time_point),
                    "-i", video_url,
                    "-vframes", "1",
                    "-q:v", "2",
                    str(screenshot_file),
                    "-y"
                ]

                subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )

                if screenshot_file.exists():
                    metadata["screenshots"].append({
                        "file": str(screenshot_file.relative_to(self.data_dir)),
                        "time": time_point,
                        "exists": True
                    })
                    if self.logger:
                        self.logger.info(f"スクリーンショット取得: {time_point}秒 -> {screenshot_file.name}")

            # メタデータ保存
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            if self.logger:
                self.logger.success(f"動画キャプチャ完了: {title} - {len(metadata['screenshots'])}枚")

            return metadata

        except Exception as e:
            if self.logger:
                self.logger.error(f"動画キャプチャエラー: {title} ({video_url}) - {e}")
            return None