"""
Backblaze B2 file storage for DISHA MIS (through B2's S3-compatible API).

Used for report attachments and for database backups. The bucket is
private: files are never public, the app hands out short-lived signed
links to logged-in users only.

Configured with four environment variables (all from the Backblaze
"Application Keys" and "Buckets" pages):
  B2_KEY_ID     keyID
  B2_APP_KEY    applicationKey (shown only once when the key is created)
  B2_BUCKET     bucket name
  B2_ENDPOINT   the bucket's S3 endpoint, e.g. s3.us-east-005.backblazeb2.com
"""
import logging
import os

log = logging.getLogger("disha.b2")

KEY_ID = os.environ.get("B2_KEY_ID", "").strip()
APP_KEY = os.environ.get("B2_APP_KEY", "").strip()
BUCKET = os.environ.get("B2_BUCKET", "").strip()
ENDPOINT = os.environ.get("B2_ENDPOINT", "").strip()
if ENDPOINT and not ENDPOINT.startswith("http"):
    ENDPOINT = "https://" + ENDPOINT

ATTACHMENT_PREFIX = "attachments/"
BACKUP_PREFIX = "backups/"

_client = None
ENABLED = bool(KEY_ID and APP_KEY and BUCKET and ENDPOINT)


class B2Error(Exception):
    pass


def client():
    global _client
    if _client is None:
        import boto3
        from botocore.config import Config
        # Region is the second part of the endpoint: s3.<region>.backblazeb2.com
        host = ENDPOINT.split("//", 1)[-1]
        parts = host.split(".")
        region = parts[1] if host.endswith("backblazeb2.com") and len(parts) > 3 else "us-east-005"
        _client = boto3.client(
            "s3", endpoint_url=ENDPOINT, region_name=region,
            aws_access_key_id=KEY_ID, aws_secret_access_key=APP_KEY,
            config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
        )
    return _client


def put(key, content, content_type="application/octet-stream"):
    try:
        client().put_object(Bucket=BUCKET, Key=key, Body=content, ContentType=content_type)
    except Exception as e:
        log.exception("B2 upload failed")
        raise B2Error(f"Could not upload to Backblaze B2: {e}")


def get(key):
    try:
        return client().get_object(Bucket=BUCKET, Key=key)["Body"].read()
    except Exception as e:
        log.exception("B2 download failed")
        raise B2Error(f"Could not download from Backblaze B2: {e}")


def delete(key):
    try:
        client().delete_object(Bucket=BUCKET, Key=key)
    except Exception as e:
        log.exception("B2 delete failed")
        raise B2Error(f"Could not delete from Backblaze B2: {e}")


def list_objects(prefix):
    """[{key, size, modified}] under prefix, newest first."""
    try:
        out, token = [], None
        while True:
            kw = {"Bucket": BUCKET, "Prefix": prefix}
            if token:
                kw["ContinuationToken"] = token
            res = client().list_objects_v2(**kw)
            for o in res.get("Contents", []):
                out.append({"key": o["Key"], "size": o["Size"], "modified": o["LastModified"]})
            if not res.get("IsTruncated"):
                break
            token = res.get("NextContinuationToken")
        return sorted(out, key=lambda o: o["modified"], reverse=True)
    except Exception as e:
        log.exception("B2 list failed")
        raise B2Error(f"Could not list Backblaze B2 files: {e}")


def signed_url(key, filename=None, expires=600):
    """A link that works for `expires` seconds, then stops working."""
    params = {"Bucket": BUCKET, "Key": key}
    if filename:
        safe = filename.replace('"', "")
        params["ResponseContentDisposition"] = f'inline; filename="{safe}"'
    return client().generate_presigned_url("get_object", Params=params, ExpiresIn=expires)
