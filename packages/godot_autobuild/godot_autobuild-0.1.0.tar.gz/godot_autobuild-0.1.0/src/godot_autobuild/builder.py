from abc import ABC, abstractmethod
from os import PathLike
import os.path
from typing import Type
from .manifest import Target, Manifest
from .godot.version import GodotInstance
from rich import print


class Builder(ABC):
    builder_env: "BuilderEnvironment" = None

    @abstractmethod
    def build(self, target: Target):
        pass

    @abstractmethod
    def can_build(self, target: Target) -> bool:
        """
        Check if this builder can build the given target.
        """
        pass

    def env(self, builder_env: "BuilderEnvironment"):
        """
        Set the builder environment for this builder.
        This is called by the BuilderFactory when registering the builder.
        """
        self.builder_env = builder_env


class BuilderFactory:
    builders: list[Builder] = []
    builder_env: "BuilderEnvironment"

    def __init__(self, builder_env: "BuilderEnvironment"):
        self.builder_env = builder_env

    def register(self, type: Type[Builder]):
        builder = type()
        builder.env(self.builder_env)

        self.builders.append(builder)

    def build(self, target: Target):
        for builder in self.builders:
            if builder.can_build(target):
                print("Building", target.id, f"({target.path})")
                return builder.build(target)

    def build_all(self, manifest: Manifest):
        for target in manifest.targets:
            self.build(target)

    # TODO: Process requirements of the target before building.


class BuilderEnvironment:
    godot: GodotInstance
    build_path: PathLike = "./build"

    def __init__(self, godot: GodotInstance, build_path: PathLike = "./build"):
        self.godot = godot
        if build_path is not None:
            self.build_path = build_path

        self.build_path = os.path.abspath(self.build_path)
