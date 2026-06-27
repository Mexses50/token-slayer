from app.db.connection import db
from app.api.products import handle_list_products
from app.api.orders import handle_create_order
from app.api.auth import handle_register, handle_login


def startup() -> None:
    db.connect()
    print("Database connected")


def shutdown() -> None:
    db.disconnect()
    print("Database disconnected")


if __name__ == "__main__":
    startup()
    print(handle_list_products())
    shutdown()
