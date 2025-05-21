import subprocess
import json
from pathlib import Path
import tempfile
import whisper
import os
from datetime import datetime


class Transcriber:
    """動画から文字起こしを行うクラス"""

    def __init__(self, data_dir="data", logger=None, model_name="small"):
        self.data_dir = Path(data_dir)
        self.logger = logger
        self.model_name = model_name

        # データディレクトリが存在しない場合は作成
        self.data_dir.mkdir(exist_ok=True, parents=True)

        # 文字起こし保存ディレクトリ
        self.transcripts_dir = self.data_dir / "transcripts"
        self.transcripts_dir.mkdir(exist_ok=True, parents=True)

        # Whisperモデルのロード
        try:
            self.model = whisper.load_model(self.model_name)
            if self.logger:
                self.logger.info(f"Whisperモデル '{self.model_name}' をロードしました")
        except Exception as e:
            self.model = None
            if self.logger:
                self.logger.error(f"Whisperモデルのロードエラー: {e}")

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

    def _extract_audio(self, video_url, output_file):
        """動画から音声を抽出"""
        try:
            cmd = [
                "ffmpeg",
                "-i", video_url,
                "-vn",  # 映像を除外
                "-acodec", "pcm_s16le",  # 音声コーデック
                "-ar", "16000",  # サンプリングレート
                "-ac", "1",  # モノラル
                output_file,
                "-y"  # 上書き
            ]

            subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"音声抽出エラー: {video_url} - {e}")
            return False

    def transcribe(self, video):
        """動画から文字起こしを行う"""
        if not self._check_ffmpeg():
            if self.logger:
                self.logger.error("ffmpegがインストールされていません")
            return None

        if self.model is None:
            if self.logger:
                self.logger.error("Whisperモデルがロードされていません")
            return None

        video_id = video["id"]
        video_url = video["url"]
        title = video["title"]

        # 文字起こし保存用ディレクトリ
        transcript_dir = self.transcripts_dir / video_id
        transcript_dir.mkdir(exist_ok=True, parents=True)

        # 文字起こしファイル
        transcript_file = transcript_dir / "transcript.json"

        # すでに文字起こしが存在する場合は読み込んで返す
        if transcript_file.exists():
            try:
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript_data = json.load(f)

                if self.logger:
                    self.logger.info(f"既存の文字起こしを使用: {title}")

                return transcript_data
            except Exception as e:
                if self.logger:
                    self.logger.error(f"文字起こしファイル読み込みエラー: {e}")

        if self.logger:
            self.logger.info(f"文字起こし開始: {title} ({video_url})")

        try:
            # 一時ファイルの作成
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_audio_path = temp_file.name

            # 音声の抽出
            if not self._extract_audio(video_url, temp_audio_path):
                if self.logger:
                    self.logger.error(f"音声抽出に失敗しました: {video_url}")
                os.unlink(temp_audio_path)
                return None

            # 文字起こしの実行
            result = self.model.transcribe(
                temp_audio_path,
                language="ja",  # 日本語
                fp16=False,
                verbose=True
            )

            # 一時ファイルの削除
            os.unlink(temp_audio_path)

            # 文字起こし結果の整形
            transcript_data = {
                "id": video_id,
                "title": title,
                "url": video_url,
                "source_name": video["source_name"],
                "source_url": video["source_url"],
                "transcribe_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "language": result.get("language", "ja"),
                "text": result.get("text", ""),
                "segments": []
            }

            # セグメント情報の追加
            for segment in result.get("segments", []):
                transcript_data["segments"].append({
                    "start": segment.get("start", 0),
                    "end": segment.get("end", 0),
                    "text": segment.get("text", "")
                })

            # 文字起こし結果の保存
            with open(transcript_file, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, ensure_ascii=False, indent=2)

            if self.logger:
                self.logger.success(f"文字起こし完了: {title} - {len(transcript_data['text'])}文字")

            return transcript_data

        except Exception as e:
            if self.logger:
                self.logger.error(f"文字起こしエラー: {title} ({video_url}) - {e}")

            # 一時ファイルが残っていたら削除
            try:
                if 'temp_audio_path' in locals() and os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
            except Exception:
                pass

            return None