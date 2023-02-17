from typing import Optional, Any

from pydantic.main import BaseModel


class GenericResponseModel(BaseModel):
    """Generic response model for all usecase and controller responses"""
    success: bool = True
    payload: Optional[Any] = None
