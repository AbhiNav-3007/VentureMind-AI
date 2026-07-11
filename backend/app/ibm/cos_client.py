"""
VentureMind AI — IBM Cloud Object Storage Client
Uploads generated PDF reports and other assets to IBM COS.
"""

from __future__ import annotations

import io
from functools import lru_cache

import ibm_boto3
from ibm_botocore.client import Config

from app.core.config import settings
from app.core.exceptions import IBMServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)


class COSClient:
    """Thin wrapper around ibm_boto3 for IBM Cloud Object Storage."""

    def __init__(self) -> None:
        self.bucket = settings.IBM_COS_BUCKET_NAME
        self._client = ibm_boto3.client(
            "s3",
            ibm_api_key_id=settings.IBM_COS_API_KEY,
            ibm_service_instance_id=settings.IBM_COS_INSTANCE_CRN,
            ibm_auth_endpoint=settings.IBM_COS_AUTH_ENDPOINT,
            config=Config(signature_version="oauth"),
            endpoint_url=settings.IBM_COS_ENDPOINT,
        )

    def upload_bytes(self, key: str, data: bytes, content_type: str = "application/pdf") -> str:
        """
        Upload raw bytes to COS and return the public URL.

        Args:
            key: Object key (e.g. "reports/abc123.pdf").
            data: Raw bytes to upload.
            content_type: MIME type.

        Returns:
            URL string pointing to the uploaded object.
        """
        try:
            self._client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=io.BytesIO(data),
                ContentType=content_type,
            )
            url = f"{settings.IBM_COS_ENDPOINT}/{self.bucket}/{key}"
            logger.info("COS upload complete", key=key, bytes=len(data))
            return url
        except Exception as exc:
            raise IBMServiceError(f"COS upload failed for key={key}", {"error": str(exc)}) from exc

    def download_bytes(self, key: str) -> bytes:
        """Download an object from COS and return as bytes."""
        try:
            response = self._client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except Exception as exc:
            raise IBMServiceError(f"COS download failed for key={key}", {"error": str(exc)}) from exc

    def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Generate a pre-signed URL for temporary access."""
        try:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expiration,
            )
        except Exception as exc:
            raise IBMServiceError("Presigned URL generation failed", {"error": str(exc)}) from exc


@lru_cache(maxsize=1)
def get_cos_client() -> COSClient:
    """Return a singleton COS client."""
    return COSClient()
