import enum
from typing import Optional, Any, List, Dict
from pydantic.main import BaseModel
from datetime import datetime


class SensiBrokerResModel(BaseModel):
    token: str
    symbol: str
    underlying: Optional[str] = None
    instrument_type: Optional[str] = None
    expiry: Optional[str] = None
    strike: Optional[float] = 0

    def build_underlying_db_model(self):
        """builds underlying db model from response model"""
        from data_adapter.sensi_data import SensiUnderlying
        res_dict = self.dict(exclude_unset=True)
        res_dict['expiry'] = None if not res_dict.get('expiry') else res_dict.get('expiry')
        return SensiUnderlying(**res_dict)

    def build_derivative_db_model(self, underlying_id: int):
        """builds derivative db model from response model"""
        from data_adapter.sensi_data import SensiDerivative
        res_dict = self.dict(exclude_unset=True)
        res_dict['underlying_id'] = underlying_id
        res_dict['expiry'] = None if not res_dict.get('expiry') else res_dict.get('expiry')
        return SensiDerivative(**res_dict)


class SensiBase(SensiBrokerResModel):
    """Base model for all sensi data models"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_deleted: bool
    expiry: Optional[Any] = None

    class Config:
        orm_mode = True


class SensiUnderlyingModel(SensiBase):
    """Sensi underlying model"""
    pass


class SensiDerivativeModel(SensiBase):
    """Sensi derivative model"""
    price: Optional[float] = 0
    underlying_id: int
    underlying_data: SensiUnderlyingModel


class UnderlyingCacheModel(BaseModel):
    """Sensi underlying cache model"""
    token: str
    id: int

    def build_cache_data(self):
        """builds cache data from response model"""
        return f"{self.token}::{self.id}"

    @classmethod
    def parse_cache_data(cls, cache_data: str):
        """builds cache data from response model"""
        token, id = cache_data.split("::")
        return cls(token=token, id=int(id))


class BrokerWSCommands(str, enum.Enum):
    """Broker websocket commands"""
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PING = "ping"
    ERROR = "error"


class BrokerWSDataTypes(str, enum.Enum):
    """Broker websocket data types"""
    PING = "ping"
    QUOTE = "quote"
    ERROR = "error"


class BrokerWSOutgoingMessage(BaseModel):
    """Broker websocket command model"""
    msg_command: BrokerWSCommands
    data_type: str = "quote"
    tokens: List[int] = []


class BrokerWSIncomingMsgToken(BaseModel):
    token: Optional[str] = None
    price: Optional[float] = None


class BrokerWSIncomingMessage(BaseModel):
    """Broker websocket incoming message model"""
    data_type: BrokerWSDataTypes
    payload: Optional[Any] = {}
