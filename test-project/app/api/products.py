from app.services.product_service import list_products, get_product, create_product, delete_product
from app.utils.formatters import format_price


def handle_list_products(page: int = 1) -> dict:
    products = list_products(page)
    return {
        "items": [
            {"id": p.id, "name": p.name, "price": format_price(p.price), "available": p.is_available()}
            for p in products
        ],
        "page": page,
    }


def handle_get_product(product_id: int) -> dict | None:
    product = get_product(product_id)
    if not product:
        return None
    return {"id": product.id, "name": product.name, "price": format_price(product.price)}


def handle_create_product(data: dict) -> dict:
    product = create_product(
        name=data["name"],
        price=data["price"],
        stock=data["stock"],
        category_id=data.get("category_id", 1),
    )
    return {"id": product.id, "name": product.name}
