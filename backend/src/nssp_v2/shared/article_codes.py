"""Helper condivisi per il confronto cross-source dei codici articolo."""


def normalize_article_code(value: str | None) -> str | None:
    """Normalizza un codice articolo per i join/logical fact cross-source.

    Regola V1:
    - trim esterno
    - uppercase
    - stringa vuota -> None
    """
    if value is None:
        return None

    normalized = value.strip().upper()
    return normalized or None
