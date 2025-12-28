"""Road model."""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.models.base import Base


class Road(Base):
    """Road model mapping to roads table."""

    __tablename__ = "roads"

    road_id = Column(Integer, primary_key=True, autoincrement=True)
    road_name = Column(String(200), nullable=True)
    neighborhood = Column(String(100), nullable=True, index=True)
    neighborhood_id = Column(Integer, ForeignKey("neighborhoods.neighborhood_id"), nullable=True)
    length_m = Column(Numeric(10, 2), nullable=True)
    width_m = Column(Numeric(10, 2), nullable=True)
    land_value = Column(Numeric(15, 2), nullable=True)
    road_line = Column(Geometry(geometry_type='LINESTRING', srid=4326), nullable=True)
    times_used = Column(Integer, default=0)
    last_visited = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    neighborhood_rel = relationship("Neighborhood", back_populates="roads")

    def __repr__(self) -> str:
        return f"<Road(id={self.road_id}, name='{self.road_name}', length={self.length_m}m)>"
