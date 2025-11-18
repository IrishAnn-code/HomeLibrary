import re
from datetime import datetime
from unidecode import unidecode  # хорошая библиотека для латинизации


def make_slug(s: str, unique: bool = False) -> str:
    """Создает slug для URL или поиска (латинизирует, убирает лишнее)."""
    s = unidecode(s.strip().lower())
    s = re.sub(r"[^a-z0-9]+", "-", s)
    slug = s.strip("-")
    if unique:
        # Добавляем timestamp или UUID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        slug = f"{slug}-{timestamp}"
        # Или: slug = f"{slug}-{uuid.uuid4().hex[:8]}"
    return slug


def normalize_author_name(s: str) -> dict:
    """Разделяет строку 'Имя Фамилия' на отдельные части."""
    parts = s.strip().split()
    if len(parts) == 1:
        return {"first_name": parts[0], "last_name": ""}
    return {"first_name": parts[0], "last_name": " ".join(parts[1:])}
