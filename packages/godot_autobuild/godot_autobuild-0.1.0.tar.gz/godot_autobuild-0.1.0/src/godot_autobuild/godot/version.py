from enum import StrEnum
from typing import Type, Optional, Union, SupportsInt
from os import PathLike
from functools import total_ordering


class VersionStatus(StrEnum):
    """Represents the status of a version."""

    STABLE = "stable"
    RC = "rc"  # Release Candidate
    BETA = "beta"
    ALPHA = "alpha"
    DEV = "dev"  # Development version


class VersionRange:
    """Represents a range of versions."""

    def __init__(
        self, major: SupportsInt, minor: SupportsInt, allow_prerelease: bool = False
    ):
        # TODO: Max prerelease range
        self.major = major
        self.minor = minor
        self.allow_prerelease = allow_prerelease

    def __str__(self) -> str:
        return f"{self.major}.{self.minor} (Prerelease: {'Yes' if self.allow_prerelease else 'No'})"

    def is_compatible(self, version: "Version") -> bool:
        if not self.allow_prerelease and version.prerelease != VersionStatus.STABLE:
            return False

        return self.major == version.major and self.minor == version.minor

    @classmethod
    def parse(cls, range: str, allow_prerelease: bool = False) -> "VersionRange":
        list = range.split(".")
        if len(list) != 2:
            raise ValueError(f"Invalid version range format: {range}")

        return cls(
            major=int(list[0]), minor=int(list[1]), allow_prerelease=allow_prerelease
        )


@total_ordering
class Version:
    """Represents a version of Godot Engine."""

    def __init__(
        self,
        major: SupportsInt,
        minor: SupportsInt,
        patch: SupportsInt = 0,
        prerelease: VersionStatus = VersionStatus.STABLE,
        build: SupportsInt = 0,
    ):
        self._major = major
        self._minor = minor
        self._patch = patch
        self._prerelease = prerelease
        self._build = build

    def __str__(self) -> str:
        """Returns the version string in the format 'X.Y.Z-status' or 'X.Y'."""
        return (
            f"{self.major}.{self.minor}"
            + (f".{self.patch}" if self.patch != 0 else "")
            + (
                f"-{self.prerelease}"
                if self.prerelease is not None
                else ""  # TODO: give a choice
            )
            + (f"{self.build}" if self.build != 0 else "")
        )

    def __eq__(self, value):
        if (
            isinstance(value, Version)
            and value.prerelease is not None
            and self.prerelease is not None
        ):
            return (
                self.major,
                self.minor,
                self.patch,
                self.prerelease,
                self.build,
            ) == (value.major, value.minor, value.patch, value.prerelease, value.build)
        return NotImplemented

    def __lt__(self, value):
        if (
            isinstance(value, Version)
            and value.prerelease is not None
            and self.prerelease is not None
        ):
            return (self.major, self.minor, self.patch, self.prerelease, self.build) < (
                value.major,
                value.minor,
                value.patch,
                value.prerelease,
                value.build,
            )
        return NotImplemented

    # === Properties ===

    @property
    def major(self) -> int:
        """Major version number. (Readonly)"""
        return self._major

    @major.setter
    def major(self, value):
        raise AttributeError("attribute 'major' is readonly")

    @property
    def minor(self) -> int:
        """Minor version number. (Readonly)"""
        return self._minor

    @minor.setter
    def minor(self, value):
        raise AttributeError("attribute 'minor' is readonly")

    @property
    def patch(self) -> int:
        """Patch version number. (Readonly)"""
        return self._patch

    @patch.setter
    def patch(self, value):
        raise AttributeError("attribute 'patch' is readonly")

    @property
    def prerelease(self) -> VersionStatus:
        """Prerelease version string. (Readonly)"""
        return self._prerelease

    @prerelease.setter
    def prerelease(self, value):
        raise AttributeError("attribute 'prerelease' is readonly")

    @property
    def build(self) -> int:
        """Build version number. (Readonly)"""
        return self._build

    @build.setter
    def build(self, value):
        raise AttributeError("attribute 'build' is readonly")

    # === Properties end ===

    @classmethod
    def parse(cls: Type["Version"], ver: str) -> "Version":
        """Parses a version string into a Version object.
        The version string can be in the format of:
        - "[v]X.Y[.Z]"
        - "[v]X.Y[.Z]-status" """

        # Strip leading 'v' or 'V' if present
        ver = ver.strip("vV")
        array = ver.split(".")

        from string import digits

        if not array[-1].isdigit():
            last = array[-1].split("-")
            pre = last[-1]
            last[-1] = pre.rstrip(digits)

            pre_ver = pre[len(last[-1]) :]
            if pre_ver != "":
                last.append(pre_ver)

            array.pop()

            array += last

        if len(array) < 2:
            raise ValueError(f"Invalid version string: {ver}")

        major = int(array[0])
        minor = int(array[1])

        if len(array) > 2 and array[2].isdigit():
            patch = int(array[2])
            prerelease = array[3] if len(array) > 3 else VersionStatus.STABLE
        else:
            patch = 0
            prerelease = array[2] if len(array) > 2 else VersionStatus.STABLE

        # TODO: raise an exception here when catch versions like "4.0-dev" (without build status version)
        build = (
            int(array[-1])
            if prerelease != VersionStatus.STABLE and array[-1].isdigit()
            else 0
        )

        return cls(
            major=major, minor=minor, patch=patch, prerelease=prerelease, build=build
        )

    def is_compatible(self, ver: "Version") -> bool:
        """An alias to equals."""
        return self == ver


@total_ordering
class GodotInstance:
    def __init__(
        self,
        version: Union[Version, str],
        mono: bool = False,
        path: Optional[PathLike] = None,
    ):
        if isinstance(version, str):
            version = Version.parse(version)

        if not isinstance(version, Version):
            raise TypeError("version must be a Version object or a string")

        self._version = version
        self._mono = mono
        self._path = path

    def __str__(self) -> str:
        """Returns the string representation of the Godot instance."""
        return f"Godot {self.version} (Mono: {'Yes' if self.mono else 'No'})"

    def __eq__(self, value):
        if isinstance(value, GodotInstance):
            return (self.version, self.mono) == (value.version, value.mono)
        return NotImplemented

    def __lt__(self, value):
        if isinstance(value, GodotInstance):
            return self.version < value.version

    @property
    def version(self) -> Version:
        return self._version

    @version.setter
    def version(self, value):
        raise AttributeError("attribute 'version' is readonly")

    @property
    def mono(self) -> bool:
        return self._mono

    @mono.setter
    def mono(self, value):
        raise AttributeError("attribute 'mono' is readonly")

    @property
    def path(self) -> Optional[PathLike]:
        return self._path

    @path.setter
    def path(self, value: PathLike):
        if not isinstance(value, (str, PathLike)):
            raise TypeError("path must be a string or PathLike object")
        self._path = value
