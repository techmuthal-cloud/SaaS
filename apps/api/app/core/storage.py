import os
import json
import logging
import urllib.request
import urllib.error
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class StorageProvider:
    """
    Abstract Storage Interface for Private Supabase Storage & Local Development Storage.
    Enforces quarantine workflows (quarantine/... -> verified/...), tenant isolation, and safe cleanup.
    """
    def save(self, workspace_id: str, filename: str, data: bytes, is_quarantined: bool = True) -> str:
        raise NotImplementedError

    def read(self, storage_path: str) -> bytes:
        raise NotImplementedError

    def delete(self, storage_path: str) -> bool:
        raise NotImplementedError

    def promote_from_quarantine(self, storage_path: str) -> str:
        raise NotImplementedError

    def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> Optional[str]:
        raise NotImplementedError

class SupabaseStorageProvider(StorageProvider):
    """
    Supabase Storage Provider using Supabase Storage REST API.
    Uses Service Role key for private server-side bucket access.
    """
    def __init__(self):
        self.supabase_url = (settings.SUPABASE_URL or "").rstrip("/")
        self.service_key = settings.SUPABASE_SERVICE_ROLE_KEY
        self.bucket = settings.SUPABASE_STORAGE_BUCKET

        if settings.ENVIRONMENT == "production" and (not self.supabase_url or not self.service_key):
            raise RuntimeError("FATAL: Supabase Storage configuration missing in production environment!")

    def _get_headers(self, content_type: str = "application/octet-stream") -> dict:
        return {
            "Authorization": f"Bearer {self.service_key}",
            "apiKey": self.service_key,
            "Content-Type": content_type
        }

    def save(self, workspace_id: str, filename: str, data: bytes, is_quarantined: bool = True) -> str:
        prefix = "quarantine" if is_quarantined else "verified"
        path = f"{prefix}/{workspace_id}/{filename}"
        
        # If in test/offline environment without active credentials, fall back safely
        if not self.supabase_url or not self.service_key:
            return LocalStorageProvider(settings.STORAGE_DIR).save(workspace_id, filename, data, is_quarantined)

        url = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{path}"
        headers = self._get_headers()
        headers["x-upsert"] = "true"

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status in (200, 201):
                    return f"supabase://{self.bucket}/{path}"
        except Exception as e:
            logger.warning(f"Supabase Storage direct upload failed: {e}. Falling back to local storage.")
            return LocalStorageProvider(settings.STORAGE_DIR).save(workspace_id, filename, data, is_quarantined)

        return f"supabase://{self.bucket}/{path}"

    def read(self, storage_path: str) -> bytes:
        if storage_path.startswith("supabase://"):
            path = storage_path.replace(f"supabase://{self.bucket}/", "")
            url = f"{self.supabase_url}/storage/v1/object/authenticated/{self.bucket}/{path}"
            headers = self._get_headers()
            req = urllib.request.Request(url, headers=headers, method="GET")
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    return resp.read()
            except Exception as e:
                logger.error(f"Failed to read from Supabase Storage path {storage_path}: {e}")
                raise
        return LocalStorageProvider(settings.STORAGE_DIR).read(storage_path)

    def delete(self, storage_path: str) -> bool:
        if storage_path.startswith("supabase://"):
            path = storage_path.replace(f"supabase://{self.bucket}/", "")
            url = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{path}"
            headers = self._get_headers()
            req = urllib.request.Request(url, headers=headers, method="DELETE")
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return resp.status in (200, 204)
            except Exception:
                return False
        return LocalStorageProvider(settings.STORAGE_DIR).delete(storage_path)

    def promote_from_quarantine(self, storage_path: str) -> str:
        if storage_path.startswith("supabase://"):
            old_path = storage_path.replace(f"supabase://{self.bucket}/", "")
            if old_path.startswith("quarantine/"):
                new_path = old_path.replace("quarantine/", "verified/", 1)
                url = f"{self.supabase_url}/storage/v1/object/move"
                payload = json.dumps({
                    "bucketId": self.bucket,
                    "sourceKey": old_path,
                    "destinationKey": new_path
                }).encode("utf-8")
                headers = self._get_headers(content_type="application/json")
                req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
                try:
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        if resp.status == 200:
                            return f"supabase://{self.bucket}/{new_path}"
                except Exception as e:
                    logger.warning(f"Supabase Storage move failed: {e}")
        return LocalStorageProvider(settings.STORAGE_DIR).promote_from_quarantine(storage_path)

    def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> Optional[str]:
        if storage_path.startswith("supabase://"):
            path = storage_path.replace(f"supabase://{self.bucket}/", "")
            url = f"{self.supabase_url}/storage/v1/object/sign/{self.bucket}/{path}"
            payload = json.dumps({"expiresIn": expires_in}).encode("utf-8")
            headers = self._get_headers(content_type="application/json")
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    signed_url_path = data.get("signedURL")
                    if signed_url_path:
                        return f"{self.supabase_url}/storage/v1{signed_url_path}"
            except Exception as e:
                logger.error(f"Failed to generate Supabase signed URL: {e}")
        return None

class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def save(self, workspace_id: str, filename: str, data: bytes, is_quarantined: bool = True) -> str:
        prefix = "quarantine" if is_quarantined else "verified"
        target_dir = os.path.join(self.base_dir, prefix, workspace_id)
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, filename)
        with open(file_path, "wb") as f:
            f.write(data)
        return file_path

    def read(self, storage_path: str) -> bytes:
        with open(storage_path, "rb") as f:
            return f.read()

    def delete(self, storage_path: str) -> bool:
        try:
            if os.path.exists(storage_path):
                os.remove(storage_path)
                return True
        except Exception:
            pass
        return False

    def promote_from_quarantine(self, storage_path: str) -> str:
        if "quarantine" not in storage_path:
            return storage_path
        verified_path = storage_path.replace("quarantine", "verified")
        os.makedirs(os.path.dirname(verified_path), exist_ok=True)
        if os.path.exists(storage_path):
            os.rename(storage_path, verified_path)
            return verified_path
        return storage_path

    def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> Optional[str]:
        return f"/api/v1/storage/download?path={storage_path}"

def get_storage() -> StorageProvider:
    if settings.STORAGE_PROVIDER == "supabase" or (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY):
        return SupabaseStorageProvider()
    return LocalStorageProvider(settings.STORAGE_DIR)

storage = get_storage()
