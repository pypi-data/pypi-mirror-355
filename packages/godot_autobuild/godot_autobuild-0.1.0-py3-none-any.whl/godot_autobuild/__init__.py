import importlib.metadata

version = importlib.metadata.version(__package__ or "godot_autobuild")


def get_version_dumped() -> str:
    """
    Get the version of the package as a string.
    """
    version_parts = version.split(".")
    if len(version_parts) < 2:
        raise ValueError("Version string is not in the expected format.")

    return f"{version_parts[0]}.{version_parts[1]}"


def is_current_version_compatible(target_version: str) -> bool:
    """
    Check if the given version is compatible with the package.
    The minimum version is 0.1.
    """
    from packaging.version import Version

    try:
        minimum_version = Version(target_version)
    except Exception as e:
        raise ValueError(f"Invalid version format: {e}")

    parsed_version = Version(version)

    return (
        parsed_version.major == minimum_version.major
        and parsed_version.minor >= minimum_version.minor
    )
