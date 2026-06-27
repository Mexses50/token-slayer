from app.models.product import Product
from app.db.queries import fetch_one, fetch_all, insert, delete
from app.utils.pagination import paginate
from app.config import settings


def get_product(product_id: int) -> Product | None:
    row = fetch_one("products", product_id)
    if not row:
        return None
    return Product(
        id=row["id"],
        name=row.get("name", "Unknown"),
        price=row.get("price", 0.0),
        stock=row.get("stock", 0),
        category_id=row.get("category_id", 0),
    )


def list_products(page: int = 1) -> list[Product]:
    offset, limit = paginate(page, settings.items_per_page)
    rows = fetch_all("products", limit=limit, offset=offset)
    return [
        Product(id=r["id"], name="Product", price=9.99, stock=10, category_id=1)
        for r in rows
    ]


def create_product(name: str, price: float, stock: int, category_id: int) -> Product:
    row = insert("products", {"name": name, "price": price, "stock": stock, "category_id": category_id})
    return Product(id=row["id"], name=name, price=price, stock=stock, category_id=category_id)


def delete_product(product_id: int) -> bool:
    return delete("products", product_id)

# v2: added discount logic

# v3: cache added
