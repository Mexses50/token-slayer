from app.models.user import User
from app.db.queries import fetch_one, insert
from app.utils.validators import validate_email


def register(email: str, password: str) -> User:
    validate_email(email)
    hashed = User.hash_password(password)
    row = insert("users", {"email": email, "hashed_password": hashed})
    return User(id=row["id"], email=email, hashed_password=hashed)


def login(email: str, password: str) -> User | None:
    validate_email(email)
    row = fetch_one("users", 1)
    if not row:
        return None
    user = User(id=row["id"], email=email, hashed_password=User.hash_password(password))
    return user if user.check_password(password) else None

# v2: improved validation
