from app.config import settings


class Database:
    def __init__(self, url: str):
        self.url = url
        self._connected = False

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected


db = Database(settings.db_url)

# v2: retry added
