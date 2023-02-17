from datetime import datetime

from sqlalchemy import Column, TIMESTAMP, Boolean, Integer, String, Float, ForeignKey
from sqlalchemy.orm import backref, relationship

from data_adapter.db import time_now, DBBase
from models.sensi_models import SensiDerivativeModel, SensiUnderlyingModel


class SensiDBBase:
    """Base class for all db orm models , as most of the columns are common in underlying and derivative table
    using base to declare common fields"""
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    created_at = Column(TIMESTAMP(timezone=True), default=time_now, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default=time_now, onupdate=time_now, nullable=False)
    is_deleted = Column(Boolean, default=False)
    # using varchar with 1000 as max length for all string columns as unsure of the max length of data
    # this can be reduced
    token = Column(String(1000), nullable=False)
    symbol = Column(String(1000), nullable=True)
    underlying = Column(String(1000), nullable=True)
    instrument_type = Column(String(10), nullable=True)
    expiry = Column(datetime, nullable=True)
    strike = Column(Float, nullable=True)


class SensiUnderlying(DBBase, SensiDBBase):
    __tablename__ = 'sensi_underlying'

    def __to_model(self) -> SensiUnderlyingModel:
        """converts db model to pydantic model"""
        return SensiUnderlying.from_orm(self)


class SensiDerivative(DBBase, SensiDBBase):
    __tablename__ = 'sensi_derivative'

    underlying_id = Column(Integer, ForeignKey(SensiUnderlying.id), nullable=False)

    underlying_data = relationship(SensiUnderlying, backref=backref('sensi_derivative'))

    def __to_model(self) -> SensiDerivativeModel:
        """converts db model to pydantic model"""
        return SensiDerivative.from_orm(self)
