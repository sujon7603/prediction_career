"""Login / signup logic. Uses only the Python standard library.

- Users and sessions are stored in a small SQLite file: data/users.db
- Passwords are never stored. Only a salted PBKDF2 hash is saved.
- A login creates a random session token. The browser keeps it in an
  HttpOnly cookie, and only a hash of the token is stored in the database.
"""
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "users.db")

SESSION_DAYS = 7
SESSION_SECONDS = SESSION_DAYS * 24 * 3600
PBKDF2_ROUNDS = 310_000

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthError(Exception):
    """Raised with a message that is safe to show to the user."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   email TEXT NOT NULL UNIQUE,
                   password_hash TEXT NOT NULL,
                   created_at INTEGER NOT NULL
               )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS sessions (
                   token_hash TEXT PRIMARY KEY,
                   user_id INTEGER NOT NULL,
                   expires_at INTEGER NOT NULL,
                   FOREIGN KEY (user_id) REFERENCES users(id)
               )"""
        )


# ---------- passwords ----------

def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
    return "pbkdf2_sha256$%d$%s$%s" % (PBKDF2_ROUNDS, salt.hex(), digest.hex())


def verify_password(password, stored):
    try:
        _, rounds, salt_hex, digest_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(rounds)
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False


# ---------- validation ----------

def clean_email(email):
    email = (email or "").strip().lower()
    if len(email) > 254 or not EMAIL_RE.match(email):
        raise AuthError("Please enter a valid email address.")
    return email


def clean_name(name):
    name = " ".join((name or "").split())
    if len(name) < 2:
        raise AuthError("Please enter your name (at least 2 characters).")
    return name[:60]


def check_password(password):
    password = password or ""
    if len(password) < 8:
        raise AuthError("Password must be at least 8 characters.")
    if len(password) > 128:
        raise AuthError("Password is too long (maximum 128 characters).")
    return password


# ---------- brute-force protection (in memory) ----------

_failures = {}          # key -> list of timestamps
MAX_FAILURES = 5
WINDOW_SECONDS = 300


def _recent_failures(key):
    now = time.time()
    items = [t for t in _failures.get(key, []) if now - t < WINDOW_SECONDS]
    _failures[key] = items
    return items


def check_not_locked(key):
    if len(_recent_failures(key)) >= MAX_FAILURES:
        raise AuthError("Too many failed attempts. Please wait 5 minutes and try again.", 429)


def record_failure(key):
    _recent_failures(key).append(time.time())


def clear_failures(key):
    _failures.pop(key, None)


# ---------- users ----------

def create_user(name, email, password):
    name = clean_name(name)
    email = clean_email(email)
    password = check_password(password)
    with db() as conn:
        exists = conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
        if exists:
            raise AuthError("An account with this email already exists. Please log in.", 409)
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (name, email, hash_password(password), int(time.time())),
        )
        return {"id": cur.lastrowid, "name": name, "email": email}


def authenticate(email, password):
    """Return the user dict, or None when the email/password is wrong."""
    email = (email or "").strip().lower()
    with db() as conn:
        row = conn.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
    if row is None:
        # Do the same amount of work so timing does not reveal if the email exists
        verify_password(password or "", hash_password("dummy-password"))
        return None
    if not verify_password(password or "", row["password_hash"]):
        return None
    return {"id": row["id"], "name": row["name"], "email": row["email"]}


# ---------- sessions ----------

def _token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(user_id):
    token = secrets.token_urlsafe(32)
    now = int(time.time())
    with db() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (_token_hash(token), user_id, now + SESSION_SECONDS),
        )
    return token


def get_user_by_token(token):
    if not token:
        return None
    with db() as conn:
        row = conn.execute(
            """SELECT u.id, u.name, u.email
                 FROM sessions s JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = ? AND s.expires_at > ?""",
            (_token_hash(token), int(time.time())),
        ).fetchone()
    return dict(row) if row else None


def delete_session(token):
    if not token:
        return
    with db() as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))
