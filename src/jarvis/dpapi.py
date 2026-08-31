"""Windows DPAPI secret encryption (zero-dependency, ctypes).

Encrypts a plaintext secret with the Windows Data Protection API
(CryptProtectData / CryptUnprotectData) so it is only decryptable by
the same Windows user on the same machine. Values are stored with a
``dpapi:`` prefix followed by base64 — plaintext values without the
prefix pass through unchanged (migration-friendly).

Used by settings.py to stop storing API keys in the clear.

Caveats:
- Encrypted blobs are bound to (user, machine). Moving settings.json to
  another machine/user makes the values undecryptable → decrypt_secret
  returns "" so callers degrade to empty, never crash.
- Only for secrets that are consumed by this process. Do NOT use for
  cross-process bearer tokens (e.g. alerts MCP token, Hermes bridge key)
  unless every reader can decrypt.
"""

from __future__ import annotations

import base64
import ctypes
import ctypes.wintypes

PREFIX = "dpapi:"


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


def _blob_from_bytes(data: bytes) -> _DATA_BLOB:
    buf = ctypes.create_string_buffer(data)
    return _DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))


def _bytes_from_blob(blob: _DATA_BLOB) -> bytes:
    if not blob.pbData or not blob.cbData:
        return b""
    raw = ctypes.string_at(blob.pbData, blob.cbData)
    return bytes(raw)


def _crypt(data: bytes, protect: bool) -> bytes:
    if not data:
        return b""
    in_blob = _blob_from_bytes(data)
    out_blob = _DATA_BLOB()
    fn = ctypes.windll.crypt32.CryptProtectData if protect else ctypes.windll.crypt32.CryptUnprotectData
    ok = fn(
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    )
    if not ok:
        raise ctypes.WinError()
    try:
        return _bytes_from_blob(out_blob)
    finally:
        if out_blob.pbData:
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)


def encrypt_secret(plain: str) -> str:
    """Encrypt a plaintext secret → ``dpapi:<base64>``. Plaintext passthrough if empty or already prefixed."""
    if not plain:
        return plain
    if plain.startswith(PREFIX):
        return plain
    try:
        enc = _crypt(plain.encode("utf-8"), protect=True)
    except OSError:
        # Non-Windows or DPAPI unavailable — fall back to plaintext rather than brick the settings.
        return plain
    return PREFIX + base64.b64encode(enc).decode("ascii")


def decrypt_secret(token: str) -> str:
    """Decrypt a ``dpapi:`` value back to plaintext. Non-prefixed values pass through unchanged."""
    if not token:
        return token
    if not token.startswith(PREFIX):
        return token
    try:
        raw = base64.b64decode(token[len(PREFIX):])
        return _crypt(raw, protect=False).decode("utf-8")
    except Exception:  # noqa: BLE001 — moved machine / tampered → degrade empty
        return ""
