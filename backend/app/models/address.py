"""Address model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, BigInteger, Float, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship

from app.models.base import Base


class Address(Base):
    """Address/Building model mapping to addresses table."""

    __tablename__ = "addresses"

    address_id = Column(Integer, primary_key=True, autoincrement=True)
    neighborhood_id = Column(Integer, ForeignKey("neighborhoods.neighborhood_id"), nullable=True, index=True)
    city = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    street = Column(String(200), nullable=True)
    street_id = Column(Integer, nullable=True)
    street_latitude = Column(Float, nullable=True)
    street_longitude = Column(Float, nullable=True)
    building_number = Column(String(50), nullable=True)
    building_id = Column(BigInteger, nullable=True)
    uavt_code = Column(BigInteger, nullable=True)
    building_latitude = Column(Float, nullable=True, index=True)
    building_longitude = Column(Float, nullable=True, index=True)
    coordinate_source = Column(String(50), nullable=True)
    block_name = Column(String(200), nullable=True)
    site_name = Column(String(200), nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    neighborhood = relationship("Neighborhood", back_populates="addresses")

    def __repr__(self) -> str:
        return f"<Address(id={self.address_id}, street='{self.street}', building_number='{self.building_number}')>"
