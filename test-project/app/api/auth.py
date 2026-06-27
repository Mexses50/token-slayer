from app.services.auth_service import register, login


def handle_register(email: str, password: str) -> dict:
    try:
        user = register(email, password)
        return {"user_id": user.id, "email": user.email}
    except ValueError as e:
        return {"error": str(e)}


def handle_login(email: str, password: str) -> dict:
    user = login(email, password)
    if not user:
        return {"error": "Invalid credentials"}
    return {"user_id": user.id, "email": user.email, "token": "fake-jwt-token"}
