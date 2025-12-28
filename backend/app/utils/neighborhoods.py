"""Neighborhood utilities."""


def normalize_neighborhood_name(name: str) -> str:
    """Normalize neighborhood name for matching with roads table.

    Roads table has shorter names without MAHALLESİ suffix.

    Args:
        name: Original neighborhood name

    Returns:
        Normalized neighborhood name
    """
    # Remove common suffixes
    name = name.replace(' MAHALLESİ', '').replace(' MAHALLESİ', '')
    name = name.replace(' MAHALLESİ', '').replace(' Mh.', '').replace(' MH.', '')
    return name.strip()
