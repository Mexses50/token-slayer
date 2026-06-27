from dataclasses import dataclass, field


@dataclass
class Product:
    id: int
    name: str
    price: float
    stock: int
    category_id: int
    tags: list[str] = field(default_factory=list)

    def is_available(self) -> bool:
        return self.stock > 0

    def apply_discount(self, percent: float) -> float:
        return self.price * (1 - percent / 100)

# updated
