from os import PathLike
from enum import StrEnum
from typing import Optional
from . import get_version_dumped
from .godot.version import Version, VersionRange


class Manifest:
    minimum_version: str = get_version_dumped()
    editor_settings: "EditorSettings"
    targets: list["Target"] = []

    def __init__(self, editor_settings: "EditorSettings", minimum_version: str = None):
        if minimum_version is not None:
            self.minimum_version = minimum_version

        self.editor_settings = editor_settings

    @classmethod
    def load(cls, path: PathLike) -> "Manifest":
        """
        Load the manifest from the specified path.
        """
        import tomllib

        try:
            with open(path, "rb") as file:
                data = tomllib.load(file)
                return cls._parse_toml(data)
        except FileNotFoundError:
            raise FileNotFoundError(f"Manifest file '{path}' not found.")
        except tomllib.TOMLDecodeError as e:
            raise ValueError(f"Error decoding TOML file: {e}")

    @classmethod
    def _parse_toml(cls, data: dict) -> "Manifest":
        """
        Parse the TOML data and return a Manifest instance.
        """

        # Check the format of TOML first.
        if "autobuild" not in data:
            raise ValueError("Manifest must contain 'autobuild' field.")

        if "editor" not in data:
            raise ValueError("Manifest must contain 'editor' section.")

        minimum_version = data.get("autobuild", cls.minimum_version)
        editor_settings = EditorSettings.parse(data.get("editor"))

        instance = cls(editor_settings, minimum_version=minimum_version)

        if "target" not in data:
            raise ValueError("Manifest must contain 'target' section.")

        targets_dict: dict = data["target"]

        for i in targets_dict:
            target = Target.parse(i, targets_dict[i])
            instance.targets.append(target)

        return instance


class TargetType(StrEnum):
    GODOT = "godot"


class Target:
    id: str
    type: TargetType = TargetType.GODOT
    path: PathLike
    default: bool = False
    editor: Optional["EditorSettings"] = None

    def __init__(
        self,
        id: str,
        path: PathLike,
        default: bool = False,
        editor: Optional["EditorSettings"] = None,
    ):
        self.id = id
        self.path = path
        self.default = default
        self.editor = editor

    @classmethod
    def parse(cls, id: str, data: dict) -> "Target":
        """
        Parse a target from the given data.
        """
        if "path" not in data:
            raise ValueError("Target must contain 'path' field.")

        path = data["path"]
        default = data.get("default", False)

        editor_data = data.get("editor")
        editor = None

        # TODO
        if editor_data and False:
            editor = EditorSettings.parse(editor_data)

        return cls(id=id, path=path, default=default, editor=editor)


class EditorSettings:
    version: Version | VersionRange
    mono: bool = False

    def __init__(self, version: Version | VersionRange, mono: bool = False):
        if not isinstance(version, (Version, VersionRange)):
            raise TypeError("version must be a Version object")

        self.version = version
        self.mono = mono

    @classmethod
    def parse(cls, data: dict) -> "EditorSettings":
        if "version" not in data:
            raise ValueError("Editor settings must contain 'version' field.")

        version_str = data["version"]

        try:
            version = VersionRange.parse(version_str)
        except ValueError:
            version = Version.parse(version_str)

        mono = data.get("mono", False)

        return cls(version=version, mono=mono)
