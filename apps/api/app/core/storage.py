import os
import hashlib
from typing import Optional
from app.core.config import settings

class StorageProvider:
    """
    Abstract Storage Interface for Private Cloudflare R2 / Local Storage.
    Enforces quarantine prefixing, verified storage paths, and safe unlinking.
    """
    def save(self, workspace_id: str, filename: str, data: bytes, is_quarantined: bool = True) -> str:
        raise NotImplementedError

    def read(self, storage_path: str) -> bytes:
        raise NotImplementedError

    def delete(self, storage_path: str) -> bool:
        raise NotImplementedError

    def promote_from_quarantine(self, storage_path: str) -> str:
        raise NotImplementedError

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
        os.rename(storage_path, verified_path)
        return verified_path

class CloudflareR2StorageProvider(StorageProvider):
    """
    Cloudflare R2 private bucket storage using S3 compatible SDK.
    """
    def __init__(self):
        self.bucket = settings.R2_BUCKET_NAME
        self.endpoint_url = settings.R2_ENDPOINT_URL or (
            f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com" if settings.R2_ACCOUNT_ID else None
        )
        self._s3_client = None
        if settings.R2_ACCESS_KEY_ID and settings.R2_SECRET_ACCESS_KEY and self.endpoint_url:
            try:
                import boto3
                self._s3_client = boto3.client(
                    "s3",
                    endpoint_url=self.endpoint_url,
                    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
                    region_name="auto"
                )
            except Exception:
                self._s3_client = None

    def save(self, workspace_id: str, filename: str, data: bytes, is_quarantined: bool = True) -> str:
        prefix = "quarantine" if is_quarantined else "verified"
        key = f"{prefix}/{workspace_id}/{filename}"
        if self._s3_client:
            self._s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType="application/octet-stream"
            )
            return f"r2://{self.bucket}/{key}"
        # Fallback to local if client not initialized
        return LocalStorageProvider(settings.STORAGE_DIR).save(workspace_id, filename, data, is_quarantined)

    def read(self, storage_path: str) -> bytes:
        if storage_path.startswith("r2://") and self._s3_client:
            key = storage_path.replace(f"r2://{self.bucket}/", "")
            response = self._s3_client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        return LocalStorageProvider(settings.STORAGE_DIR).read(storage_path)

    def delete(self, storage_path: str) -> bool:
        if storage_path.startswith("r2://") and self._s3_client:
            try:
                key = storage_path.replace(f"r2://{self.bucket}/", "")
                self._s3_client.delete_object(Bucket=self.bucket, Key=key)
                return True
            except Exception:
                return False
        return LocalStorageProvider(settings.STORAGE_DIR).delete(storage_path)

    def promote_from_quarantine(self, storage_path: str) -> str:
        if storage_path.startswith("r2://") and self._s3_client:
            old_key = storage_path.replace(f"r2://{self.bucket}/", "")
            if old_key.startswith("quarantine/"):
                new_key = old_key.replace("quarantine/", "verified/", 1)
                self._s3_client.copy_object(
                    Bucket=self.bucket,
                    CopySource={"Bucket": self.bucket, "Key": old_key},
                    Key=new_key
                )
                self._s3_client.delete_object(Bucket=self.bucket, Key=old_key)
                return f"r2://{self.bucket}/{new_key}"
        return LocalStorageProvider(settings.STORAGE_DIR).promote_from_quarantine(storage_path)

def get_storage() -> StorageProvider:
    if settings.R2_BUCKET_NAME and (settings.R2_ACCESS_KEY_ID or settings.R2_ENDPOINT_URL):
        return CloudflareR2StorageProvider()
    return LocalStorageProvider(settings.STORAGE_DIR)

storage = get_storage()
