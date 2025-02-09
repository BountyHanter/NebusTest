from fastapi import HTTPException
from pydantic import BaseModel
from typing import Generic, Optional, TypeVar, Any, Dict


def success_response(*, message: str, data: Optional[Any] = None, extras: Optional[Dict[str, Any]] = None) -> dict[str, Any]:
    return {
        "status": "success",
        "message": message,
        "data": data,
        "extras": extras,
    }


def error_response(*, message: str, status_code, data: Optional[Any] = None) -> Any:
    raise HTTPException(
        status_code=status_code,
        detail={
            "status": "error",
            "message": message,
            "data": data,
        }
    )


T = TypeVar("T")  # Типизатор для обобщённого поля `data`


class BaseResponse(BaseModel, Generic[T]):  # Сначала BaseModel, затем Generic
    status: str
    message: str
    data: Optional[T] = None
    extras: Optional[Dict[str, Any]] = None

