import uuid

import httpx

from app.core.config import settings

BUCKET = "product-photos"


async def upload_product_photo(file_bytes: bytes, content_type: str = "image/jpeg") -> str:
    """Uploads a photo to the Supabase Storage 'product-photos' bucket and
    returns its permanent public URL."""
    filename = f"{uuid.uuid4().hex}.jpg"
    upload_url = f"{settings.supabase_url}/storage/v1/object/{BUCKET}/{filename}"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            upload_url,
            content=file_bytes,
            headers={
                "apikey": settings.supabase_service_key,
                "Authorization": f"Bearer {settings.supabase_service_key}",
                "Content-Type": content_type,
            },
        )
        response.raise_for_status()

    return f"{settings.supabase_url}/storage/v1/object/public/{BUCKET}/{filename}"