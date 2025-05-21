import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


class Notifier:
    """通知を送信するクラス"""

    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger
        self.enabled = config.get("enabled", False)
        self.method = config.get("method", "cli")

    def _format_url_entries(self, entries, max_entries=10):
        """URL通知のフォーマット"""
        if not entries:
            return "新着情報はありません。"

        # エントリ数の制限
        if len(entries) > max_entries:
            shown_entries = entries[:max_entries]
            remaining = len(entries) - max_entries
        else:
            shown_entries = entries
            remaining = 0

        # メッセージの構築
        lines = []

        for i, entry in enumerate(shown_entries, 1):
            title = entry.get("title", "タイトルなし")
            link = entry.get("link", "#")
            published = entry.get("published", "")
            source = entry.get("source", "")

            lines.append(f"{i}. 【{source}】 {title}")
            lines.append(f"   {link}")
            if published:
                lines.append(f"   {published}")
            lines.append("")

        if remaining > 0:
            lines.append(f"...他 {remaining} 件")

        return "\n".join(lines)

    def _format_video_entries(self, entries, max_entries=5):
        """動画通知のフォーマット"""
        if not entries:
            return "新着動画はありません。"

        # エントリ数の制限
        if len(entries) > max_entries:
            shown_entries = entries[:max_entries]
            remaining = len(entries) - max_entries
        else:
            shown_entries = entries
            remaining = 0

        # メッセージの構築
        lines = []

        for i, entry in enumerate(shown_entries, 1):
            title = entry.get("title", "タイトルなし")
            url = entry.get("url", "#")
            source_name = entry.get("source_name", "")
            summary = entry.get("summary", "要約なし")

            lines.append(f"{i}. 【{source_name}】 {title}")
            lines.append(f"   {url}")
            lines.append("")
            lines.append("   【要約】")
            lines.append(f"   {summary}")
            lines.append("")

        if remaining > 0:
            lines.append(f"...他 {remaining} 件")

        return "\n".join(lines)

    def notify_url_updates(self, entries):
        """URL更新の通知"""
        if not self.enabled or not entries:
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        subject = f"GovInfoWatcher: 新着情報 {len(entries)}件 ({timestamp})"
        message = self._format_url_entries(entries)

        return self._send_notification(subject, message)

    def notify_video_updates(self, entries):
        """動画更新の通知"""
        if not self.enabled or not entries:
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        subject = f"GovInfoWatcher: 新着動画・要約 {len(entries)}件 ({timestamp})"
        message = self._format_video_entries(entries)

        return self._send_notification(subject, message)

    def _send_notification(self, subject, message):
        """通知の送信"""
        if self.method == "cli":
            return self._send_cli_notification(subject, message)
        elif self.method == "slack":
            return self._send_slack_notification(subject, message)
        elif self.method == "email":
            return self._send_email_notification(subject, message)
        else:
            if self.logger:
                self.logger.error(f"未知の通知方法: {self.method}")
            return False

    def _send_cli_notification(self, subject, message):
        """CLI通知の送信"""
        print("\n" + "="*50)
        print(subject)
        print("="*50)
        print(message)
        print("="*50 + "\n")

        if self.logger:
            self.logger.info(f"CLI通知を送信しました: {subject}")

        return True

    def _send_slack_notification(self, subject, message):
        """Slack通知の送信"""
        if "slack" not in self.config:
            if self.logger:
                self.logger.error("Slack設定がありません")
            return False

        webhook_url = self.config["slack"].get("webhook_url", "")
        channel = self.config["slack"].get("channel", "#notifications")

        if not webhook_url:
            if self.logger:
                self.logger.error("Slack webhook URLが設定されていません")
            return False

        try:
            payload = {
                "channel": channel,
                "username": "GovInfoWatcher",
                "text": subject,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": subject
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message
                        }
                    }
                ]
            }

            response = requests.post(
                webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                if self.logger:
                    self.logger.info(f"Slack通知を送信しました: {subject}")
                return True
            else:
                if self.logger:
                    self.logger.error(f"Slack通知エラー: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            if self.logger:
                self.logger.error(f"Slack通知エラー: {e}")
            return False

    def _send_email_notification(self, subject, message):
        """メール通知の送信"""
        if "email" not in self.config:
            if self.logger:
                self.logger.error("メール設定がありません")
            return False

        smtp_server = self.config["email"].get("smtp_server", "")
        smtp_port = self.config["email"].get("smtp_port", 587)
        username = self.config["email"].get("username", "")
        password = self.config["email"].get("password", "")
        from_address = self.config["email"].get("from_address", "")
        to_address = self.config["email"].get("to_address", "")

        if not smtp_server or not username or not password or not from_address or not to_address:
            if self.logger:
                self.logger.error("メール設定が不完全です")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = from_address
            msg["To"] = to_address
            msg["Subject"] = subject

            msg.attach(MIMEText(message, "plain"))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)

            if self.logger:
                self.logger.info(f"メール通知を送信しました: {subject}")

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"メール通知エラー: {e}")
            return False