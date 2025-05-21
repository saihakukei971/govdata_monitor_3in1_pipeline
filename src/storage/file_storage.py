import json
import yaml
import os
from pathlib import Path
from datetime import datetime


class FileStorage:
    """ファイルへのデータ保存を管理するクラス"""

    def __init__(self, data_dir="data", logger=None):
        self.data_dir = Path(data_dir)
        self.logger = logger

        # データディレクトリが存在しない場合は作成
        self.data_dir.mkdir(exist_ok=True, parents=True)

    def save_json(self, data, filename, subdirectory=None):
        """JSONデータを保存"""
        try:
            # サブディレクトリがある場合
            if subdirectory:
                save_dir = self.data_dir / subdirectory
                save_dir.mkdir(exist_ok=True, parents=True)
                file_path = save_dir / filename
            else:
                file_path = self.data_dir / filename

            # 親ディレクトリが存在しない場合は作成
            file_path.parent.mkdir(exist_ok=True, parents=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            if self.logger:
                self.logger.info(f"JSON保存成功: {file_path}")

            return str(file_path)

        except Exception as e:
            if self.logger:
                self.logger.error(f"JSON保存エラー: {filename} - {e}")
            return None

    def load_json(self, filename, subdirectory=None, default=None):
        """JSONデータを読み込み"""
        try:
            # サブディレクトリがある場合
            if subdirectory:
                file_path = self.data_dir / subdirectory / filename
            else:
                file_path = self.data_dir / filename

            # ファイルが存在しない場合
            if not file_path.exists():
                if self.logger:
                    self.logger.warning(f"JSONファイルが見つかりません: {file_path}")
                return default

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if self.logger:
                self.logger.info(f"JSON読み込み成功: {file_path}")

            return data

        except Exception as e:
            if self.logger:
                self.logger.error(f"JSON読み込みエラー: {filename} - {e}")
            return default

    def save_yaml(self, data, filename, subdirectory=None):
        """YAMLデータを保存"""
        try:
            # サブディレクトリがある場合
            if subdirectory:
                save_dir = self.data_dir / subdirectory
                save_dir.mkdir(exist_ok=True, parents=True)
                file_path = save_dir / filename
            else:
                file_path = self.data_dir / filename

            # 親ディレクトリが存在しない場合は作成
            file_path.parent.mkdir(exist_ok=True, parents=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

            if self.logger:
                self.logger.info(f"YAML保存成功: {file_path}")

            return str(file_path)

        except Exception as e:
            if self.logger:
                self.logger.error(f"YAML保存エラー: {filename} - {e}")
            return None

    def load_yaml(self, filename, subdirectory=None, default=None):
        """YAMLデータを読み込み"""
        try:
            # サブディレクトリがある場合
            if subdirectory:
                file_path = self.data_dir / subdirectory / filename
            else:
                file_path = self.data_dir / filename

            # ファイルが存在しない場合
            if not file_path.exists():
                if self.logger:
                    self.logger.warning(f"YAMLファイルが見つかりません: {file_path}")
                return default

            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if self.logger:
                self.logger.info(f"YAML読み込み成功: {file_path}")

            return data

        except Exception as e:
            if self.logger:
                self.logger.error(f"YAML読み込みエラー: {filename} - {e}")
            return default

    def save_text(self, text, filename, subdirectory=None, mode='w'):
        """テキストを保存"""
        try:
            # サブディレクトリがある場合
            if subdirectory:
                save_dir = self.data_dir / subdirectory
                save_dir.mkdir(exist_ok=True, parents=True)
                file_path = save_dir / filename
            else:
                file_path = self.data_dir / filename

            # 親ディレクトリが存在しない場合は作成
            file_path.parent.mkdir(exist_ok=True, parents=True)

            with open(file_path, mode, encoding='utf-8') as f:
                f.write(text)

            if self.logger:
                self.logger.info(f"テキスト保存成功: {file_path}")

            return str(file_path)

        except Exception as e:
            if self.logger:
                self.logger.error(f"テキスト保存エラー: {filename} - {e}")
            return None

    def load_text(self, filename, subdirectory=None, default=""):
        """テキストを読み込み"""
        try:
            # サブディレクトリがある場合
            if subdirectory:
                file_path = self.data_dir / subdirectory / filename
            else:
                file_path = self.data_dir / filename

            # ファイルが存在しない場合
            if not file_path.exists():
                if self.logger:
                    self.logger.warning(f"テキストファイルが見つかりません: {file_path}")
                return default

            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            if self.logger:
                self.logger.info(f"テキスト読み込み成功: {file_path}")

            return text

        except Exception as e:
            if self.logger:
                self.logger.error(f"テキスト読み込みエラー: {filename} - {e}")
            return default

    def save_binary(self, data, filename, subdirectory=None):
        """バイナリデータを保存"""
        try:
            # サブディレクトリがある場合
            if subdirectory:
                save_dir = self.data_dir / subdirectory
                save_dir.mkdir(exist_ok=True, parents=True)
                file_path = save_dir / filename
            else:
                file_path = self.data_dir / filename

            # 親ディレクトリが存在しない場合は作成
            file_path.parent.mkdir(exist_ok=True, parents=True)

            with open(file_path, 'wb') as f:
                f.write(data)

            if self.logger:
                self.logger.info(f"バイナリ保存成功: {file_path}")

            return str(file_path)

        except Exception as e:
            if self.logger:
                self.logger.error(f"バイナリ保存エラー: {filename} - {e}")
            return None

    def load_binary(self, filename, subdirectory=None, default=None):
        """バイナリデータを読み込み"""
        try:
            # サブディレクトリがある場合
            if subdirectory:
                file_path = self.data_dir / subdirectory / filename
            else:
                file_path = self.data_dir / filename

            # ファイルが存在しない場合
            if not file_path.exists():
                if self.logger:
                    self.logger.warning(f"バイナリファイルが見つかりません: {file_path}")
                return default

            with open(file_path, 'rb') as f:
                data = f.read()

            if self.logger:
                self.logger.info(f"バイナリ読み込み成功: {file_path}")

            return data

        except Exception as e:
            if self.logger:
                self.logger.error(f"バイナリ読み込みエラー: {filename} - {e}")
            return default

    def list_files(self, subdirectory=None, pattern="*"):
        """ファイル一覧を取得"""
        try:
            # サブディレクトリがある場合
            if subdirectory:
                search_dir = self.data_dir / subdirectory
            else:
                search_dir = self.data_dir

            # ディレクトリが存在しない場合
            if not search_dir.exists():
                if self.logger:
                    self.logger.warning(f"ディレクトリが見つかりません: {search_dir}")
                return []

            # ファイル一覧を取得
            files = list(search_dir.glob(pattern))

            if self.logger:
                self.logger.info(f"ファイル一覧取得成功: {search_dir} - {len(files)}件")

            return [str(f.relative_to(self.data_dir)) for f in files if f.is_file()]

        except Exception as e:
            if self.logger:
                self.logger.error(f"ファイル一覧取得エラー: {e}")
            return []

    def create_dated_directory(self, base_dir=None):
        """日付ごとのディレクトリを作成"""
        try:
            # 日付文字列
            date_str = datetime.now().strftime('%Y%m%d')

            # ベースディレクトリ
            if base_dir:
                dated_dir = self.data_dir / base_dir / date_str
            else:
                dated_dir = self.data_dir / date_str

            # ディレクトリの作成
            dated_dir.mkdir(exist_ok=True, parents=True)

            if self.logger:
                self.logger.info(f"日付ディレクトリ作成成功: {dated_dir}")

            return str(dated_dir)

        except Exception as e:
            if self.logger:
                self.logger.error(f"日付ディレクトリ作成エラー: {e}")
            return None

    def file_exists(self, filename, subdirectory=None):
        """ファイルが存在するか確認"""
        try:
            # サブディレクトリがある場合
            if subdirectory:
                file_path = self.data_dir / subdirectory / filename
            else:
                file_path = self.data_dir / filename

            return file_path.exists()

        except Exception:
            return False