from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from decouple import config

conf = ConnectionConfig(
    MAIL_USERNAME=config("MAIL_USERNAME"),
    MAIL_PASSWORD=config("MAIL_PASSWORD"),
    MAIL_FROM=config("MAIL_FROM"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,   # <-- use this instead of MAIL_TLS
    MAIL_SSL_TLS=False,   # <-- use this instead of MAIL_SSL
    USE_CREDENTIALS=True
)

async def send_reset_email(email: str, reset_link: str):
    message = MessageSchema(
        subject="Reset your password",
        recipients=[email],
        body=f"""
        <p>You requested a password reset.</p>
        <p>
            <a href="{reset_link}">
                Click here to reset your password
            </a>
        </p>
        <p>This link expires in 30 minutes.</p>
        """,
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)
