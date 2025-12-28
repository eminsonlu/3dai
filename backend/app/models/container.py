"""Container model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography

from app.models.base import Base


class Container(Base):
    """Container model mapping to containers table."""

    __tablename__ = "containers"

    container_id = Column(Integer, primary_key=True, autoincrement=True)
    neighborhood_id = Column(Integer, ForeignKey("neighborhoods.neighborhood_id"), nullable=True, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=True)
    vehicle_type = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    neighborhood = relationship("Neighborhood", back_populates="containers")

    def __repr__(self) -> str:
        return f"<Container(id={self.container_id}, lat={self.latitude}, lon={self.longitude})>"
