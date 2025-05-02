import uuid, mimetypes, requests
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

def _safe_ext(content_type: str) -> str:
    ext = mimetypes.guess_extension(content_type.split(";")[0].strip()) or ".mp3"
    return ext.lstrip(".")

def save_remote_file(url: str, prefix: str) -> str:
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    ext = _safe_ext(resp.headers.get("Content-Type", "audio/mpeg"))
    name = f"{prefix}/{uuid.uuid4()}.{ext}"
    default_storage.save(name, ContentFile(resp.content))
    return default_storage.url(name)
