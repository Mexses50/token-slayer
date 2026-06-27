from dataclasses import dataclass, field
from app.models.product import Product
from app.models.user import User


@dataclass
class OrderItem:
    product: Product
    quantity: int

    @property
    def subtotal(self) -> float:
        return self.product.price * self.quantity


@dataclass
class Order:
    id: int
    user: User
    items: list[OrderItem] = field(default_factory=list)
    status: str = "pending"

    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self.items)

    def add_item(self, product: Product, quantity: int) -> None:
        self.items.append(OrderItem(product=product, quantity=quantity))

    def cancel(self) -> None:
        self.status = "cancelled"
