import os
import json
import shutil
import threading
import datetime

from backend.logger import setup_logger

logger = setup_logger("json_storage")

BACKUPS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "backups")
os.makedirs(BACKUPS_DIR, exist_ok=True)

_file_locks = {}

def _get_lock(path: str) -> threading.RLock:
    if path not in _file_locks:
        _file_locks[path] = threading.RLock()
    return _file_locks[path]

def read_json(file_path: str) -> dict:
    lock = _get_lock(file_path)
    with lock:
        if not os.path.exists(file_path):
            logger.warning(f"JSON file not found at {file_path}, creating default")
            default = {"products": [], "transactions": [], "config": {}, "suppliers": [], "customers": []}
            write_json(file_path, default)
            return default
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted JSON at {file_path}: {e}. Attempting recovery from backup...")
            recovered = _recover_from_backup(file_path)
            if recovered is not None:
                return recovered
            logger.critical(f"No valid backup found. Creating empty dataset.")
            default = {"products": [], "transactions": [], "config": {}, "suppliers": [], "customers": []}
            write_json(file_path, default)
            return default
        except Exception as e:
            logger.exception(f"Unexpected error reading {file_path}: {e}")
            raise

def write_json(file_path: str, data: dict):
    lock = _get_lock(file_path)
    with lock:
        _backup(file_path)
        tmp_path = file_path + ".tmp." + datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, file_path)
        except Exception as e:
            logger.exception(f"Failed atomic write to {file_path}: {e}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

def _backup(file_path: str):
    if not os.path.exists(file_path):
        return
    try:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{os.path.basename(file_path)}.{ts}.bak"
        backup_path = os.path.join(BACKUPS_DIR, backup_name)
        shutil.copy2(file_path, backup_path)
        _cleanup_old_backups()
    except Exception as e:
        logger.warning(f"Backup failed for {file_path}: {e}")

def _cleanup_old_backups(max_backups: int = 50):
    try:
        backups = sorted([
            os.path.join(BACKUPS_DIR, f) for f in os.listdir(BACKUPS_DIR)
            if f.endswith(".bak")
        ], key=os.path.getmtime)
        while len(backups) > max_backups:
            old = backups.pop(0)
            os.remove(old)
            logger.debug(f"Removed old backup: {old}")
    except Exception as e:
        logger.warning(f"Backup cleanup failed: {e}")

def update_json(file_path: str, updater):
    """Atomically read, modify, and write JSON under a single lock.
    `updater` receives a dict and must return the modified dict (or None for no change)."""
    lock = _get_lock(file_path)
    with lock:
        data = read_json(file_path)
        result = updater(data)
        if result is not None:
            write_json(file_path, result)
        return data

def _recover_from_backup(file_path: str):
    try:
        backups = sorted([
            os.path.join(BACKUPS_DIR, f) for f in os.listdir(BACKUPS_DIR)
            if f.startswith(os.path.basename(file_path)) and f.endswith(".bak")
        ], key=os.path.getmtime, reverse=True)
        for backup in backups:
            try:
                with open(backup, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info(f"Recovered from backup: {backup}")
                return data
            except (json.JSONDecodeError, Exception):
                continue
    except Exception as e:
        logger.error(f"Backup recovery failed: {e}")
    return None
