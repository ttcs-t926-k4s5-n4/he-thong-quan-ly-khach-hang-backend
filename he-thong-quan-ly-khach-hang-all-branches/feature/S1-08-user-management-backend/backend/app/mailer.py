import smtplib
import ssl
from email.message import EmailMessage
from typing import Any, Protocol


class ActivationMailer(Protocol):
    def send_activation(
        self,
        recipient: str,
        full_name: str,
        temporary_password: str,
        activation_url: str,
    ) -> None: ...


class ConsoleMailer:
    def send_activation(
        self,
        recipient: str,
        full_name: str,
        temporary_password: str,
        activation_url: str,
    ) -> None:
        print("\n" + "=" * 72)
        print("EMAIL KÍCH HOẠT - HỆ THỐNG QUẢN LÝ KHÁCH HÀNG")
        print(f"Tới: {recipient}")
        print(f"Xin chào {full_name}")
        print(f"Mật khẩu tạm: {temporary_password}")
        print(f"Liên kết kích hoạt: {activation_url}")
        print("=" * 72 + "\n")


class SmtpMailer:
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
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender
        self.use_ssl = use_ssl
        self.starttls = starttls

    def send_activation(
        self,
        recipient: str,
        full_name: str,
        temporary_password: str,
        activation_url: str,
    ) -> None:
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = recipient
        message["Subject"] = "Kích hoạt tài khoản - Hệ thống quản lý khách hàng"

        message.set_content(
            f"Xin chào {full_name},\n\n"
            "Tài khoản CRM của bạn đã được tạo.\n"
            f"Mật khẩu tạm: {temporary_password}\n"
            f"Liên kết kích hoạt: {activation_url}\n\n"
            "Vui lòng kích hoạt tài khoản và đổi mật khẩu sau khi đăng nhập."
        )

        message.add_alternative(
            f"<p>Xin chào <strong>{full_name}</strong>,</p>"
            "<p>Tài khoản CRM của bạn đã được tạo.</p>"
            f"<p>Mật khẩu tạm: <strong>{temporary_password}</strong></p>"
            f'<p><a href="{activation_url}">Kích hoạt tài khoản</a></p>'
            "<p>Vui lòng đổi mật khẩu sau khi đăng nhập.</p>",
            subtype="html",
        )

        if self.use_ssl:
            with smtplib.SMTP_SSL(self.host, self.port, timeout=20) as server:
                self._authenticate_and_send(server, message)
            return

        with smtplib.SMTP(self.host, self.port, timeout=20) as server:
            server.ehlo()
            if self.starttls:
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
            self._authenticate_and_send(server, message)

    def _authenticate_and_send(
        self,
        server: smtplib.SMTP,
        message: EmailMessage,
    ) -> None:
        if self.username:
            server.login(self.username, self.password)
        server.send_message(message)


def create_mailer(config: Any) -> ActivationMailer:
    if str(config["MAIL_BACKEND"]).lower() == "smtp":
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
