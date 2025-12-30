import secrets
import string


def generate_password(
    length: int = 16,
    use_upper: bool = True,
    use_lower: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True
) -> str:
    if length < 8:
        raise ValueError("Password length must be at least 8")

    charset = ""

    if use_upper:
        charset += string.ascii_uppercase
    if use_lower:
        charset += string.ascii_lowercase
    if use_digits:
        charset += string.digits
    if use_symbols:
        charset += "!@#$%^&*()-_=+[]{};:,.<>?"

    if not charset:
        raise ValueError("At least one character set must be enabled")

    return "".join(secrets.choice(charset) for _ in range(length))
