"""
Whole-database backups for DISHA MIS.

A backup is one gzipped JSON file holding every row of every table
(see store.dump_tables). Attachments are not inside it: they already live
in Backblaze B2 and the backup keeps their file names and paths.

Backups are saved in the B2 bucket under backups/ and kept for
KEEP_DAYS days (the newest MIN_KEEP are never deleted).
"""
import gzip
import json
import logging
from datetime import datetime, timedelta, timezone

import b2
import store
from store import StoreError

log = logging.getLogger("disha.backup")

KEEP_DAYS = 30
MIN_KEEP = 7


def build():
    """(filename, gzipped bytes, row counts) for a fresh backup."""
    payload = store.dump_tables()
    counts = store.validate_backup(payload)
    name = f"disha-backup-{datetime.now(timezone.utc):%Y-%m-%d-%H%M%S}.json.gz"
    data = gzip.compress(json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"))
    return name, data, counts


def parse(data):
    """Backup payload from an uploaded or downloaded file (.json or .json.gz)."""
    try:
        if data[:2] == b"\x1f\x8b":
            data = gzip.decompress(data)
        payload = json.loads(data.decode("utf-8"))
    except Exception:
        raise StoreError("This file could not be read. Choose a DISHA MIS backup file "
                         "(disha-backup-….json.gz).")
    store.validate_backup(payload)
    return payload


def save_to_b2(label=""):
    """Make a backup, upload it to B2 and delete old ones. Returns (name, counts)."""
    if not b2.ENABLED:
        raise StoreError("Backblaze B2 is not set up, so backups cannot be stored online. "
                         "You can still download a backup to your computer.")
    name, data, counts = build()
    if label:
        name = name.replace(".json.gz", f"-{label}.json.gz")
    try:
        b2.put(b2.BACKUP_PREFIX + name, data, "application/gzip")
        prune()
    except b2.B2Error as e:
        raise StoreError(str(e))
    log.info("Backup %s saved (%s)", name, counts)
    return name, counts


def list_backups():
    if not b2.ENABLED:
        return []
    try:
        items = b2.list_objects(b2.BACKUP_PREFIX)
    except b2.B2Error as e:
        raise StoreError(str(e))
    for o in items:
        o["name"] = o["key"][len(b2.BACKUP_PREFIX):]
    return [o for o in items if o["name"].startswith("disha-backup-")]


def load_from_b2(name):
    if "/" in name or not name.startswith("disha-backup-"):
        raise StoreError("Unknown backup.")
    try:
        return b2.get(b2.BACKUP_PREFIX + name)
    except b2.B2Error as e:
        raise StoreError(str(e))


def prune():
    """Delete backups older than KEEP_DAYS, always keeping the newest MIN_KEEP."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=KEEP_DAYS)
    for o in list_backups()[MIN_KEEP:]:
        if o["modified"] < cutoff:
            b2.delete(o["key"])
            log.info("Deleted old backup %s", o["name"])


def restore(payload):
    """Save a safety backup of the current data first, then restore."""
    safety = None
    if b2.ENABLED:
        safety, _ = save_to_b2(label="before-restore")
    counts = store.restore_tables(payload)
    return counts, safety
