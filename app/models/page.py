from typing import Optional, List, Type, TypeVar, Any, Dict, Union
from pydantic import BaseModel, ConfigDict, field_validator
import json

class ImageItem(BaseModel):
    url: str
    caption: Optional[str] = None

class GifItem(BaseModel):
    url: str

class VideoItem(BaseModel):
    url: str

M = TypeVar("M", ImageItem, GifItem, VideoItem)

def _coerce_media_list(value: Any, ItemModel: Type[M]) -> Optional[List[M]]:
    if value is None or value == "":
        return None

    # Si c'est une chaîne: soit JSON, soit URL simple
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            # Probablement une URL simple
            return [ItemModel(url=value)]

    # Si c'est un dict: encapsuler en liste
    if isinstance(value, dict):
        return [ItemModel(**value)]

    # Si c'est déjà une liste: normaliser chaque élément
    if isinstance(value, list):
        normalized: List[M] = []
        for el in value:
            if el is None or el == "":
                continue
            if isinstance(el, str):
                # Essayer de parser comme JSON, sinon considérer comme URL
                try:
                    parsed = json.loads(el)
                    if isinstance(parsed, dict):
                        normalized.append(ItemModel(**parsed))
                    elif isinstance(parsed, str):
                        normalized.append(ItemModel(url=parsed))
                except json.JSONDecodeError:
                    normalized.append(ItemModel(url=el))
            elif isinstance(el, dict):
                normalized.append(ItemModel(**el))
            else:
                # Types non attendus -> on ignore
                continue
        return normalized or None

    # Type non géré -> None (ou lève si tu veux être strict)
    return None

class PageItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    breadcrumbs: Optional[List[str]] = None
    images: Optional[List[ImageItem]] = None
    gifs: Optional[List[GifItem]] = None
    videos: Optional[List[VideoItem]] = None
    content: Optional[str] = None

    @field_validator("images", mode="before")
    @classmethod
    def _val_images(cls, v):
        return _coerce_media_list(v, ImageItem)

    @field_validator("gifs", mode="before")
    @classmethod
    def _val_gifs(cls, v):
        return _coerce_media_list(v, GifItem)

    @field_validator("videos", mode="before")
    @classmethod
    def _val_videos(cls, v):
        return _coerce_media_list(v, VideoItem)
