"""
mailer.py — Console (dev) và SMTP (prod) mailer
Gộp cả send_activation (S1-08) và send_password_reset (S1-03)
"""
import smtplib
import ssl
from email.message import EmailMessage
from typing import Any


class ConsoleMailer:
    """In email ra terminal – dùng khi phát triển (MAIL_BACKEND=console)."""

    def send_activation(
        self, recipient: str, full_name: str, tmp_password: str, activation_url: str
    ) -> None:
        sep = "=" * 72
        print(f"\n{sep}\nEMAIL KÍCH HOẠT — HỆ THỐNG CRM")
        print(f"Tới       : {recipient}")
        print(f"Xin chào  : {full_name}")
        print(f"Mật khẩu tạm : {tmp_password}")
        print(f"Link kích hoạt: {activation_url}")
        print(f"{sep}\n")

    def send_password_reset(self, recipient: str, reset_url: str) -> None:
        sep = "=" * 72
        print(f"\n{sep}\nEMAIL ĐẶT LẠI MẬT KHẨU — HỆ THỐNG CRM")
        print(f"Tới  : {recipient}")
        print(f"Link (30 phút, 1 lần): {reset_url}")
        print(f"{sep}\n")


class SmtpMailer:
    """Gửi email thật qua SMTP."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        sender: str,
        use_ssl: bool,
        starttls: bool,
    ) -> None:
        self.host, self.port = host, port
        self.username, self.password = username, password
        self.sender, self.use_ssl, self.starttls = sender, use_ssl, starttls

    def _send(self, msg: EmailMessage) -> None:
        if self.use_ssl:
            with smtplib.SMTP_SSL(self.host, self.port, timeout=20) as s:
                if self.username:
                    s.login(self.username, self.password)
                s.send_message(msg)
        else:
            with smtplib.SMTP(self.host, self.port, timeout=20) as s:
                s.ehlo()
                if self.starttls:
                    s.starttls(context=ssl.create_default_context())
                    s.ehlo()
                if self.username:
                    s.login(self.username, self.password)
                s.send_message(msg)

    def send_activation(
        self, recipient: str, full_name: str, tmp_password: str, activation_url: str
    ) -> None:
        msg = EmailMessage()
        msg["From"], msg["To"] = self.sender, recipient
        msg["Subject"] = "Kích hoạt tài khoản — Hệ thống CRM"
        msg.set_content(
            f"Xin chào {full_name},\n\n"
            f"Tài khoản CRM của bạn đã được tạo.\n"
            f"Mật khẩu tạm: {tmp_password}\n"
            f"Liên kết kích hoạt: {activation_url}\n\n"
            "Vui lòng đổi mật khẩu sau khi đăng nhập."
        )
        msg.add_alternative(
            f"<p>Xin chào <strong>{full_name}</strong>,</p>"
            "<p>Tài khoản CRM của bạn đã được tạo.</p>"
            f"<p>Mật khẩu tạm: <strong>{tmp_password}</strong></p>"
            f'<p><a href="{activation_url}">Kích hoạt tài khoản</a></p>',
            subtype="html",
        )
        self._send(msg)

    def send_password_reset(self, recipient: str, reset_url: str) -> None:
        msg = EmailMessage()
        msg["From"], msg["To"] = self.sender, recipient
        msg["Subject"] = "Đặt lại mật khẩu — Hệ thống CRM"
        msg.set_content(
            "Chúng tôi nhận được yêu cầu đặt lại mật khẩu của bạn.\n\n"
            f"Mở liên kết này trong 30 phút: {reset_url}\n\n"
            "Liên kết chỉ dùng một lần. Nếu bạn không yêu cầu, hãy bỏ qua email này."
        )
        msg.add_alternative(
            "<p>Chúng tôi nhận được yêu cầu đặt lại mật khẩu.</p>"
            f'<p><a href="{reset_url}">Đặt lại mật khẩu</a> (hiệu lực 30 phút, 1 lần)</p>',
            subtype="html",
        )
        self._send(msg)


def create_mailer(config: Any) -> ConsoleMailer | SmtpMailer:
    if str(config.get("MAIL_BACKEND", "console")).lower() == "smtp":
        return SmtpMailer(
            host=str(config["SMTP_HOST"]),
            port=int(config["SMTP_PORT"]),
            username=str(config["SMTP_USERNAME"]),
            password=str(config["SMTP_PASSWORD"]),
            sender=str(config["MAIL_FROM"]),
            use_ssl=bool(config["SMTP_USE_SSL"]),
            starttls=bool(config["SMTP_STARTTLS"]),
        )
    return ConsoleMailer()
