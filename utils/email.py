from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from decouple import config
import random

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


async def send_account_restored_email(email: str):
    # Example: send an email notifying the account has been restored
    from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
    conf = ConnectionConfig(
        MAIL_USERNAME="your_email@example.com",
        MAIL_PASSWORD="your_password",
        MAIL_FROM="your_email@example.com",
        MAIL_PORT=587,
        MAIL_SERVER="smtp.example.com",
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
    )

    message = MessageSchema(
        subject="Account Restored",
        recipients=[email],
        body=f"""
        <p>Hello,</p>
        <p>Your account has been restored successfully.</p>
        <br>
        <p>Regards,<br>Team</p>
        """,
        subtype="html",
    )

    fm = FastMail(conf)
    await fm.send_message(message)


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



async def send_invite_email(email: str, invite_link: str, role: str, full_name: str):

    message = MessageSchema(
        subject="You're Invited to Join",
        recipients=[email],
        body=f"""
        <p>Hello {full_name},</p>

        <p>You have been invited to join our platform as <strong>{role}</strong>.</p>

        <p>
            <a href="{invite_link}" 
               style="padding:10px 15px;background-color:#2563eb;color:white;
               text-decoration:none;border-radius:5px;">
               Accept Invitation
            </a>
        </p>

        <p>This link will expire in 48 hours.</p>

        <br>
        <p>Regards,<br>Team</p>
        """,
        subtype="html",
    )

    fm = FastMail(conf)
    await fm.send_message(message)




def generate_otp():
    return str(random.randint(100000, 999999))


async def send_verification_otp(email: str, otp: str):

    message = MessageSchema(
        subject="Verify Your Email",
        recipients=[email],
        body=f"""
        <p>Your email verification OTP is:</p>

        <h2 style="letter-spacing:3px;">{otp}</h2>

        <p>This OTP will expire in 5 minutes.</p>

        <br>
        <p>If you did not request this, please ignore this email.</p>
        """,
        subtype="html",
    )

    fm = FastMail(conf)
    await fm.send_message(message)