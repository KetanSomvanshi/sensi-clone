from datetime import datetime
from typing import List

from sqlalchemy import Column, TIMESTAMP, Boolean, Integer, String, Float, ForeignKey, DATE
from sqlalchemy.orm import backref, relationship

from controller.context_manager import get_db_session
from data_adapter.db import time_now, DBBase
from models.sensi_models import SensiDerivativeModel, SensiUnderlyingModel, SensiResModel


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
    expiry = Column(DATE, nullable=True)
    strike = Column(Float, nullable=True)


class SensiUnderlying(DBBase, SensiDBBase):
    __tablename__ = 'sensi_underlying'

    def __to_model(self) -> SensiUnderlyingModel:
        """converts db model to pydantic model"""
        return SensiUnderlyingModel.from_orm(self)

    @classmethod
    def get_all_underlying(cls) -> List[SensiResModel]:
        """returns all underlying data"""
        db = get_db_session()
        return [underlying.__to_model().build_res_model() for underlying in db.query(cls).all()]

    @classmethod
    def get_all_underlyings(cls) -> List[SensiUnderlyingModel]:
        """returns all underlying data"""
        db = get_db_session()
        return [underlying.__to_model() for underlying in db.query(cls).all()]

    @classmethod
    def insert_underlyings(cls, underlyings):
        db = get_db_session()
        db.add_all(underlyings)
        db.flush()


class SensiDerivative(DBBase, SensiDBBase):
    __tablename__ = 'sensi_derivative'

    underlying_id = Column(Integer, ForeignKey(SensiUnderlying.id), nullable=False)

    underlying_data = relationship(SensiUnderlying, backref=backref('sensi_derivative'))

    def __to_model(self) -> SensiDerivativeModel:
        """converts db model to pydantic model"""
        return SensiDerivativeModel.from_orm(self)

    @classmethod
    def get_all_derivative_by_underlying_symbol(cls, symbol: str) -> List[SensiResModel]:
        """returns all derivative data for a given underlying symbol"""
        db = get_db_session()
        return [derivative.__to_model().build_res_model() for derivative in
                db.query(cls).join(SensiUnderlying).filter(SensiUnderlying.symbol == symbol).all()]

    @classmethod
    def insert_derivatives(cls, derivatives):
        db = get_db_session()
        db.add_all(derivatives)
        db.flush()

    @classmethod
    def get_all_derivatives_by_underlying_token(cls, token: str) -> List[SensiDerivativeModel]:
        """returns all derivative data for a given underlying token"""
        db = get_db_session()
        return [derivative.__to_model() for derivative in
                db.query(cls).join(SensiUnderlying).filter(SensiUnderlying.token == token).all()]
