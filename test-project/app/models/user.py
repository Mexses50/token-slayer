from dataclasses import dataclass
import hashlib


@dataclass
class User:
    id: int
    email: str
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        return self.hashed_password == self.hash_password(password)
