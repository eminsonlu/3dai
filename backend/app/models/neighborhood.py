"""Neighborhood model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship

from app.models.base import Base


class Neighborhood(Base):
    """Neighborhood model mapping to neighborhoods table."""

    __tablename__ = "neighborhoods"

    neighborhood_id = Column(Integer, primary_key=True, autoincrement=True)
    neighborhood_name = Column(String(200), unique=True, nullable=False)
    neighborhood_name_normalized = Column(String(200), nullable=False, index=True)
    neighborhood_id_external = Column(Integer, nullable=True)
    population = Column(Integer, nullable=True)
    neighborhood_type = Column(String(50), nullable=True)
    garbage_truck_type = Column(String(100), nullable=True)
    days_collected_per_week = Column(Integer, nullable=True)
    collection_days = Column(String(200), nullable=True)
    uses_crane = Column(Boolean, default=False)
    crane_rotation_days = Column(Integer, default=0)
    underground_containers = Column(Integer, default=0)
    container_770lt = Column(Integer, default=0)
    container_400lt = Column(Integer, default=0)
    plastic_containers = Column(Integer, default=0)
    total_containers = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    addresses = relationship("Address", back_populates="neighborhood")
    containers = relationship("Container", back_populates="neighborhood")
    roads = relationship("Road", back_populates="neighborhood")

    def __repr__(self) -> str:
        return f"<Neighborhood(id={self.neighborhood_id}, name='{self.neighborhood_name}')>"
