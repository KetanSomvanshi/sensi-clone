from typing import Optional, Any
from pydantic.main import BaseModel
from datetime import datetime

from pydantic.types import constr


class SensiBase(BaseModel):
    """Base model for all sensi data models"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_deleted: bool
    token: str
    symbol: str
    underlying: Optional[str] = None
    instrument_type: Optional[str] = None
    expiry: Optional[datetime] = None
    strike: Optional[float] = 0

    class Config:
        orm_mode = True


class SensiUnderlyingModel(SensiBase):
    """Sensi underlying model"""
    pass


class SensiDerivativeModel(SensiBase):
    """Sensi derivative model"""
    underlying_id: int
    underlying_data: SensiUnderlyingModel
