import hashlib
import hmac


def verify_github_signature(
    *,
    secret: str,
    body: bytes,
    signature_header: str,
) -> bool:
    prefix = "sha256="
    if not signature_header.startswith(prefix):
        return False

    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    supplied = signature_header[len(prefix) :]
    return hmac.compare_digest(expected, supplied)

