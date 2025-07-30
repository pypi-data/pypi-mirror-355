from typing import Optional

from pydantic import BaseModel


class GeometriaPayloadSchema(BaseModel):
    id_entidade: str
    entidade: str
    coords: str
    representacao: Optional[str] = None
    tipo_geom: str
    zoom: Optional[int] = None


class GeometriaResponseSchema(GeometriaPayloadSchema):
    id: str
    suuid: str
    coords: Optional[dict] = None


class SGLFeature(BaseModel):
    id: str
    suuid: str
    coords: Optional[dict] = None
    entity: str
    entityId: str
    geomType: str
    representation: Optional[str] = None
    zoom: Optional[str] = None
