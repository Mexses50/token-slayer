import re

EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


def validate_email(email: str) -> None:
    if not EMAIL_RE.match(email):
        raise ValueError(f"Invalid email: {email}")


def validate_positive(value: int | float, name: str = "value") -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def validate_non_empty(value: str, name: str = "value") -> None:
    if not value or not value.strip():
        raise ValueError(f"{name} must not be empty")

# updated
