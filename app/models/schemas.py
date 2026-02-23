from typing import List, Optional

from pydantic import BaseModel, Field


class ThumbnailMetadata(BaseModel):
    id: str = Field(..., description="Identifier used to retrieve the thumbnail")
    url: str = Field(..., description="URL to fetch the thumbnail")
    width: int
    height: int
    preset: Optional[str] = Field(
        None, description="Name of the preset used, if any"
    )
    is_preset: bool = Field(
        False, description="True if generated from a named preset size"
    )


class ImageThumbnails(BaseModel):
    original_filename: str
    content_type: str
    thumbnails: List[ThumbnailMetadata]


class UploadThumbnailsResponse(BaseModel):
    items: List[ImageThumbnails]

