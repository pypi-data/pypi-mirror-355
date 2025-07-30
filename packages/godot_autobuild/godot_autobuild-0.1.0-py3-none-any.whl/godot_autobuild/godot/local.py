from .version import Version, VersionRange, GodotInstance
import subprocess
import os
from os import PathLike


def get_matched_instance(
    ver: Version | VersionRange, mono: bool = False
) -> GodotInstance:
    """
    Get the matched Godot version from the local environment.
    """

    if ver is None:
        raise ValueError("Version cannot be None.")

    # Check if the GODOT environment variable is set
    if "GODOT" in os.environ:
        instance = _get_envvar_godot_version()
        if ver.is_compatible(instance.version):
            return _get_envvar_godot_version()

    # Check if the GodotEnv is installed
    godotenv_versions = _get_godotenv_versions()
    godotenv_versions.sort()
    if godotenv_versions:
        for instance in godotenv_versions:
            # Check if the version is compatible and if the mono flag matches.
            # The mono flag of the instance is tested only if the mono parameter is True.
            if ver.is_compatible(instance.version) and (
                not mono or instance.mono == mono
            ):
                instance.path = _get_godotenv_godot_path(instance)
                return instance

    # If no matches found, return None.
    return None


def _get_envvar_godot_version() -> GodotInstance:
    path = os.environ.get("GODOT")
    if path is None:
        raise EnvironmentError("GODOT environment variable is not set.")

    return _get_version_from_path(path)


def _get_godotenv_versions() -> list[GodotInstance]:
    """
    Get all Godot versions installed from the GodotEnv.
    """

    try:
        output = subprocess.check_output(["godotenv", "godot", "list"], text=True)
    except FileNotFoundError:
        return []

    versions_raw = output.splitlines()

    versions = []
    for i in versions_raw:
        splited = i.split()
        if splited[-1] == "*":
            splited.pop()  # Remove the '*' character if present

        version = splited[0]
        mono = True if splited[1] == "mono" else False

        versions.append(GodotInstance(version, mono=mono))

    return versions


def _get_godotenv_godot_path(godot: GodotInstance):
    raise NotImplementedError


def _get_version_from_path(path: PathLike) -> GodotInstance:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"'{path}' is not exists.")

    # Run the provided path with --version to get the version information
    output = subprocess.check_output([path, "--version"], text=True)

    instance = _parse_stdout(output)
    instance.path = path

    return instance


def _parse_stdout(stdout: str) -> GodotInstance:
    """
    Convert the stdout from the Godot executable to a Version object.
    """
    parts = stdout.split(".")

    # TODO: Handle custom builds.
    official_index = parts.index("official") if "official" in parts else -1
    if official_index == -1:
        raise ValueError("Invalid version format: 'official' not found in output.")

    # Check if the version is mono or not
    mono = True if "mono" in parts else False
    if mono:
        parts.remove("mono")

    # Extract the version parts before the 'official' index
    version_list = parts[:official_index]

    prerelease = version_list.pop()

    version = "-".join([".".join(version_list), prerelease])

    return GodotInstance(version, mono=mono)
