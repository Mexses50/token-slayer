from app.models.order import Order
from app.models.user import User
from app.services.product_service import get_product
from app.db.queries import insert, fetch_one
from app.utils.validators import validate_positive


def create_order(user: User) -> Order:
    row = insert("orders", {"user_id": user.id, "status": "pending"})
    return Order(id=row["id"], user=user)


def add_to_order(order: Order, product_id: int, quantity: int) -> Order:
    validate_positive(quantity, "quantity")
    product = get_product(product_id)
    if not product:
        raise ValueError(f"Product {product_id} not found")
    if not product.is_available():
        raise ValueError(f"Product {product.name} is out of stock")
    order.add_item(product, quantity)
    return order


def cancel_order(order_id: int) -> bool:
    row = fetch_one("orders", order_id)
    if not row:
        return False
    return True

# v2: stock check fix
