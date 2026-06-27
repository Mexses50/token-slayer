def format_price(amount: float, currency: str = "USD") -> str:
    return f"{currency} {amount:.2f}"


def format_order_status(status: str) -> str:
    return status.replace("_", " ").title()


def truncate(text: str, max_len: int = 100) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
