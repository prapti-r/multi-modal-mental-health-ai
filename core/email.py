import ssl
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from core.config import settings
from pydantic import EmailStr

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

class EmailService:
    @staticmethod
    async def send_otp_email(email_to: EmailStr, otp_code: str):
        """Sends a verification code to the user."""
        html = f"""
        <html>
            <body>
                <p>Hi,</p>
                <p>Your verification code is: <strong>{otp_code}</strong></p>
                <p>This code expires in {settings.OTP_EXPIRE_MINUTES} minutes.</p>
                <p>If you did not request this, please ignore this email.</p>
            </body>
        </html>
        """
        
        message = MessageSchema(
            subject="Verify Your Account",
            recipients=[email_to],
            body=html,
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message)

email_service = EmailService()