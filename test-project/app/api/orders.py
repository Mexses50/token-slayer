from app.services.order_service import create_order, add_to_order, cancel_order
from app.models.user import User
from app.utils.formatters import format_price, format_order_status


def handle_create_order(user_id: int) -> dict:
    user = User(id=user_id, email="user@example.com", hashed_password="")
    order = create_order(user)
    return {"order_id": order.id, "status": format_order_status(order.status)}


def handle_add_item(order_id: int, product_id: int, quantity: int) -> dict:
    user = User(id=1, email="user@example.com", hashed_password="")
    from app.models.order import Order
    order = Order(id=order_id, user=user)
    order = add_to_order(order, product_id, quantity)
    return {
        "order_id": order.id,
        "total": format_price(order.total),
        "items": len(order.items),
    }
