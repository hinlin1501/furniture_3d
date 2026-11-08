import re
import unicodedata


def slugify(value: str) -> str:
    """URL slug that also handles Vietnamese diacritics (đ/Đ included)."""
    value = value.replace("đ", "d").replace("Đ", "D")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value


def escape_like(value: str, escape: str = "\\") -> str:
    """Escape LIKE wildcards so user input is matched literally."""
    return (
        value.replace(escape, escape * 2).replace("%", escape + "%").replace("_", escape + "_")
    )


def normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
