import secrets


def generate_secure_otp() -> str:
    """
    Generates a cryptographically secure 6-digit OTP
    """
    return str(secrets.randbelow(900000) + 100000)