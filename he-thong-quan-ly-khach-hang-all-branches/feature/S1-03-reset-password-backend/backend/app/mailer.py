import smtplib
import ssl
from email.message import EmailMessage
from typing import Any, Protocol


class PasswordResetMailer(Protocol):
    def send_password_reset(self, recipient: str, reset_url: str) -> None: ...


class ConsoleMailer:
    def send_password_reset(self, recipient: str, reset_url: str) -> None:
        print("\n" + "=" * 72)
        print("EMAIL DEMO - HỆ THỐNG QUẢN LÝ KHÁCH HÀNG")
        print(f"Tới: {recipient}")
        print("Chủ đề: Đặt lại mật khẩu")
        print(f"Liên kết có hiệu lực 30 phút và chỉ dùng một lần: {reset_url}")
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

    def send_password_reset(self, recipient: str, reset_url: str) -> None:
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = recipient
        message["Subject"] = "Đặt lại mật khẩu - Hệ thống quản lý khách hàng"
        message.set_content(
            "Chúng tôi đã nhận yêu cầu đặt lại mật khẩu của bạn.\n\n"
            f"Mở liên kết này trong vòng 30 phút: {reset_url}\n\n"
            "Liên kết chỉ dùng được một lần.\n"
            "Nếu bạn không yêu cầu đặt lại mật khẩu, hãy bỏ qua email này."
        )
        message.add_alternative(
            "<p>Chúng tôi đã nhận yêu cầu đặt lại mật khẩu của bạn.</p>"
            f'<p><a href="{reset_url}">Đặt lại mật khẩu</a></p>'
            "<p>Liên kết có hiệu lực trong 30 phút và chỉ dùng được một lần.</p>",
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


def create_mailer(config: Any) -> PasswordResetMailer:
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
