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
            })
    return specs


def flag_values(challenge: dict, dynamic_flag: str | None = None) -> list[str]:
    return [spec["flag"] for spec in flag_specs(challenge)]

