"""Challenge metadata helpers shared by imports and student views."""


def flag_specs(challenge: dict) -> list[dict]:
    """Return normalized flag records, strictly using the multi-flag layout."""
    raw_flags = challenge.get("flags") or []
    specs = []
    for item in raw_flags:
        if isinstance(item, dict) and isinstance(item.get("flag"), str):
            specs.append({
                "flag": item["flag"],
                "description": str(item.get("description", "")),
                "hints": item.get("hints", []) if isinstance(item.get("hints", []), list) else [],
                "points": _positive_int(item.get("points"), 100),
                "max_attempts": _positive_int(item.get("max_attempts"), 3),
            })
    return specs


def _positive_int(value, default: int) -> int:
    """Return a positive metadata value while keeping existing imports usable."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number > 0 else default


def total_points(challenge: dict) -> int:
    return sum(spec["points"] for spec in flag_specs(challenge))


def flag_values(challenge: dict, dynamic_flag: str | None = None) -> list[str]:
    flags = [spec["flag"] for spec in flag_specs(challenge)]
    if dynamic_flag:
        flags.append(dynamic_flag)
    return flags
