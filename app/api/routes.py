import asyncio
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import Response, StreamingResponse

from app.core.errors import InvalidImageError
from app.models.schemas import UploadThumbnailsResponse
from app.services.thumbnail_service import InputImage, ThumbnailService
from app.storage.local import LocalThumbnailStorage


router = APIRouter()

_storage = LocalThumbnailStorage()


def get_thumbnail_service() -> ThumbnailService:
    return ThumbnailService(storage=_storage)


@router.post(
    "/thumbnails",
    response_model=UploadThumbnailsResponse,
    status_code=201,
)
async def create_thumbnails(
    files: List[UploadFile] = File(...),
    presets: Optional[List[str]] = Query(
        default=None,
        description="Optional list of preset sizes to generate (e.g., small,medium)",
    ),
    width: Optional[int] = Query(
        default=None,
        gt=0,
        description="Optional custom target width",
    ),
    height: Optional[int] = Query(
        default=None,
        gt=0,
        description="Optional custom target height",
    ),
    service: ThumbnailService = Depends(get_thumbnail_service),
) -> UploadThumbnailsResponse:
    if not files:
        raise InvalidImageError("At least one file must be uploaded")

    inputs: list[InputImage] = []
    for f in files:
        data = await f.read()
        inputs.append(
            InputImage(
                filename=f.filename,
                data=data,
                content_type=f.content_type or "application/octet-stream",
            )
        )

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: service.generate_thumbnails(
            images=inputs,
            presets=presets,
            width=width,
            height=height,
        ),
    )


@router.get("/thumbnails/{thumbnail_id}")
async def get_thumbnail(
    thumbnail_id: str,
    service: ThumbnailService = Depends(get_thumbnail_service),
) -> Response:
    loop = asyncio.get_event_loop()
    data, content_type = await loop.run_in_executor(
        None,
        lambda: service.get_thumbnail_content(thumbnail_id),
    )
    return StreamingResponse(
        iter([data]),
        media_type=content_type,
    )

