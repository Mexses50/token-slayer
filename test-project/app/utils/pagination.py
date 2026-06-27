def paginate(page: int, per_page: int) -> tuple[int, int]:
    if page < 1:
        page = 1
    offset = (page - 1) * per_page
    return offset, per_page


def total_pages(total_items: int, per_page: int) -> int:
    if per_page <= 0:
        raise ValueError("per_page must be positive")
    return max(1, -(-total_items // per_page))
