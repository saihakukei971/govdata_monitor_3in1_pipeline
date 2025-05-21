import json
import os
from pathlib import Path
import openai
from datetime import datetime


class Summarizer:
    """文字起こしテキストを要約するクラス"""

    def __init__(self, data_dir="data", logger=None, api_key=None):
        self.data_dir = Path(data_dir)
        self.logger = logger

        # OpenAI APIキーの設定
        if api_key:
            openai.api_key = api_key
        else:
            openai.api_key = os.environ.get("OPENAI_API_KEY")

        # データディレクトリが存在しない場合は作成
        self.data_dir.mkdir(exist_ok=True, parents=True)

        # 要約保存ディレクトリ
        self.summaries_dir = self.data_dir / "summaries"
        self.summaries_dir.mkdir(exist_ok=True, parents=True)

    def _check_api_key(self):
        """APIキーが設定されているか確認"""
        return openai.api_key is not None and openai.api_key != ""

    def summarize(self, transcript, max_length=1000):
        """文字起こしテキストを要約"""
        if not self._check_api_key():
            if self.logger:
                self.logger.error("OpenAI APIキーが設定されていません")
            return None

        video_id = transcript["id"]
        title = transcript["title"]
        text = transcript["text"]

        # テキストが短すぎる場合は要約せずにそのまま返す
        if len(text) < 300:
            if self.logger:
                self.logger.info(f"テキストが短いため要約なし: {title} ({len(text)}文字)")

            summary_data = {
                "id": video_id,
                "title": title,
                "url": transcript["url"],
                "source_name": transcript["source_name"],
                "source_url": transcript["source_url"],
                "summary_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "summary": text,
                "original_length": len(text),
                "summary_length": len(text),
                "summarized": False
            }

            return summary_data

        # 要約保存用ディレクトリ
        summary_dir = self.summaries_dir / video_id
        summary_dir.mkdir(exist_ok=True, parents=True)

        # 要約ファイル
        summary_file = summary_dir / "summary.json"

        # すでに要約が存在する場合は読み込んで返す
        if summary_file.exists():
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary_data = json.load(f)

                if self.logger:
                    self.logger.info(f"既存の要約を使用: {title}")

                return summary_data
            except Exception as e:
                if self.logger:
                    self.logger.error(f"要約ファイル読み込みエラー: {e}")

        if self.logger:
            self.logger.info(f"要約開始: {title} ({len(text)}文字)")

        try:
            # GPT APIを使用してテキストを要約
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは政府機関の公式動画の内容を要約するアシスタントです。以下の文字起こしテキストを重要なポイントを含めて簡潔に要約してください。政策・規制・手続きなどの重要な情報は必ず含めてください。"},
                    {"role": "user", "content": f"以下の「{title}」の動画文字起こしを400字以内で要約してください。\n\n{text}"}
                ],
                max_tokens=1024,
                temperature=0.3
            )

            # 要約の取得
            summary = response.choices[0].message.content.strip()

            # 要約データの作成
            summary_data = {
                "id": video_id,
                "title": title,
                "url": transcript["url"],
                "source_name": transcript["source_name"],
                "source_url": transcript["source_url"],
                "summary_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "summary": summary,
                "original_length": len(text),
                "summary_length": len(summary),
                "summarized": True
            }

            # 要約データの保存
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, ensure_ascii=False, indent=2)

            if self.logger:
                self.logger.success(f"要約完了: {title} - {len(summary)}文字")

            return summary_data

        except Exception as e:
            if self.logger:
                self.logger.error(f"要約エラー: {title} - {e}")
            return None