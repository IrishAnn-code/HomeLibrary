from starlette.requests import Request


def flash(request: Request, message: str, category: str = "info"):
    """
    Добавить flash-сообщение.

    Args:
        request: HTTP запрос
        message: Текст сообщения
        category: Тип (success, error, warning, info)
    """
    if "_messages" not in request.session:
        request.session["_messages"] = []

    request.session["_messages"].append({"message": message, "category": category})


def get_flashed_messages(request: Request) -> list:
    """
    Получить и удалить все flash-сообщения.

    Returns:
        list: Список словарей {"message": "...", "category": "..."}
    """
    return request.session.pop("_messages", [])
