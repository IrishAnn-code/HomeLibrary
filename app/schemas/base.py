"""
Базовые схемы и валидаторы для всех Pydantic моделей
"""
from pydantic import BaseModel, model_validator
from typing import Any


class BaseSchema(BaseModel):
    """
    Базовая схема, которая автоматически удаляет пробелы по краям строк
    из входного словаря данных перед основной валидацией.
    """
    @model_validator(mode="before")
    @classmethod
    def strip_all_strings(cls, data: Any) -> Any:
        if isinstance(data, dict):
            new_data = {}
            for k, v in data.items():
                if isinstance(v, str):
                    new_data[k] = v.strip()
                else:
                    new_data[k] = v
            return new_data
        return data

    class Config:
        from_attributes = True