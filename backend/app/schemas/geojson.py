"""GeoJSON Pydantic models."""

from pydantic import BaseModel


class GeoJSONFeature(BaseModel):
    """GeoJSON Feature."""

    type: str = "Feature"
    geometry: dict
    properties: dict


class GeoJSONFeatureCollection(BaseModel):
    """GeoJSON FeatureCollection."""

    type: str = "FeatureCollection"
    features: list[GeoJSONFeature]
