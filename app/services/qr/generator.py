"""Crockford Base32 token generation with checksum (Phase 4)."""

import secrets
import uuid

# Crockford Base32: 0-9, A-Z excluding I, L, O, U (32 chars)
_CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_CHECKSUM_EXTRA = "*~$=U"  # for remainder 32-36


def _encode_crockford(value: int, with_checksum: bool = False) -> str:
    """Encode non-negative integer to Crockford Base32 string."""
    if value < 0:
        raise ValueError("value must be non-negative")
    if value == 0:
        out = "0"
    else:
        out = ""
        while value:
            out = _CROCKFORD_ALPHABET[value % 32] + out
            value //= 32
    if with_checksum:
        rem = sum(_CROCKFORD_ALPHABET.index(c) for c in out) % 37
        if rem < 32:
            out += _CROCKFORD_ALPHABET[rem]
        else:
            out += _CHECKSUM_EXTRA[rem - 32]
    return out


def _decode_crockford(s: str) -> int:
    """Decode Crockford Base32 string to integer (case-insensitive, no checksum char)."""
    s = s.upper().replace("O", "0").replace("I", "1").replace("L", "1")
    n = 0
    for c in s:
        if c in _CHECKSUM_EXTRA:
            break
        idx = _CROCKFORD_ALPHABET.find(c)
        if idx < 0:
            raise ValueError(f"invalid character: {c}")
        n = n * 32 + idx
    return n


def validate_checksum(token: str) -> bool:
    """Validate Crockford checksum: token format NS-CODE-CHECK or CODE-CHECK."""
    try:
        if "-" in token:
            parts = token.split("-")
            # NS-CODE-CHECK -> code is parts[1], check is parts[2]; or CODE-CHECK -> parts[0], parts[1]
            if len(parts) == 3:
                code_part, check_part = parts[1], parts[2]
            elif len(parts) == 2:
                code_part, check_part = parts[0], parts[1]
            else:
                code_part = "".join(parts[:-1])
                check_part = parts[-1] if parts else ""
        else:
            if len(token) < 2:
                return False
            code_part = token[:-1]
            check_part = token[-1]
        value = _decode_crockford(code_part)
        expected_full = _encode_crockford(value, with_checksum=True)
        return expected_full[-1] == check_part.upper()
    except (ValueError, IndexError):
        return False


def decode_crockford_checksum(s: str) -> int | None:
    """Decode string with optional checksum; returns numeric value or None if invalid."""
    s = s.strip().upper().replace("-", "")
    if not s:
        return None
    try:
        if s[-1] in _CHECKSUM_EXTRA or s[-1] in _CROCKFORD_ALPHABET:
            code = s[:-1]
            if not code:
                return None
            if not validate_checksum(s):
                return None
            return _decode_crockford(code)
        return _decode_crockford(s)
    except ValueError:
        return None


def generate_token(namespace: str, length: int = 8) -> str:
    """Generate NS-CODE-CHECK format token. Code is random Crockford Base32 with checksum."""
    num = secrets.randbelow(32**length) or 1
    code = _encode_crockford(num)
    with_check = _encode_crockford(num, with_checksum=True)
    check_char = with_check[-1]
    return f"{namespace.upper()}-{code}-{check_char}"
