import hashlib
import secrets
import re
import html

def hash_password(password: str, salt: str = None) -> tuple:
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.sha256()
    h.update((password + salt).encode("utf-8"))
    return h.hexdigest(), salt

def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    h = hashlib.sha256()
    h.update((password + salt).encode("utf-8"))
    return h.hexdigest() == stored_hash

def sanitize_html(value: str) -> str:
    if not isinstance(value, str):
        return str(value) if value is not None else ""
    return html.escape(value, quote=True)

def sanitize_dict(data: dict) -> dict:
    safe = {}
    for k, v in data.items():
        if isinstance(v, str):
            safe[k] = sanitize_html(v)
        elif isinstance(v, dict):
            safe[k] = sanitize_dict(v)
        elif isinstance(v, list):
            safe[k] = [sanitize_html(item) if isinstance(item, str) else item for item in v]
        else:
            safe[k] = v
    return safe

def generate_token() -> str:
    return secrets.token_hex(32)

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip())) if email else True

def validate_phone(phone: str) -> bool:
    if not phone:
        return True
    digits_only = re.sub(r'[\s\-\+\(\)]', '', phone)
    return digits_only.isdigit() and len(digits_only) >= 7

def sanitize_filename(filename: str) -> str:
    clean = re.sub(r'[^\w\-_. ]', '', filename)
    clean = clean.strip().replace(' ', '_')
    return clean or 'unnamed'
