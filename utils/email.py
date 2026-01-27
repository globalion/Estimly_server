from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from decouple import config

conf = ConnectionConfig(
    MAIL_USERNAME=config("MAIL_USERNAME"),
    MAIL_PASSWORD=config("MAIL_PASSWORD"),
    MAIL_FROM=config("MAIL_FROM"),
    MAIL_PORT=config("MAIL_PORT", cast=int),
    MAIL_SERVER=config("MAIL_SERVER"),
    MAIL_STARTTLS=config("MAIL_STARTTLS", cast=bool),  # False for SSL
    MAIL_SSL_TLS=config("MAIL_SSL_TLS", cast=bool),    # True for SSL
    USE_CREDENTIALS=config("USE_CREDENTIALS", cast=bool),
)

async def send_reset_email(email: str, reset_link: str):
    message = MessageSchema(
        subject="Reset your password",
        recipients=[email],
        body=f"""
        <p>You requested a password reset.</p>
        <p><a href="{reset_link}">Click here to reset your password</a></p>
        <p>This link expires in 30 minutes.</p>
        """,
        subtype="html",
    )

    fm = FastMail(conf)
    await fm.send_message(message)
