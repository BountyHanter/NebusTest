from typing import List

from pydantic import BaseModel


class OrganizationRequestSchema(BaseModel):
    id: int
    name: str
    phone_numbers: List[str]
    activities: List[str]
    address: str
    latitude: float  # Широта
    longitude: float  # Долгота

    class Config:
        from_attributes = True  # Автоматическое преобразование из SQLAlchemy-объектов

