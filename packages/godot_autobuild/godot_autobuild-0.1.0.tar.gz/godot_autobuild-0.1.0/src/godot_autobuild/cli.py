from pathlib import Path
from typing import Optional
from typing_extensions import Annotated
from rich import print
from . import version as package_version
from . import is_current_version_compatible
from .godot import local as godot_local
from .builder import BuilderFactory, BuilderEnvironment
from .godot.builder import GodotBuilder
import os
import typer

app = typer.Typer()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    print(__package__, package_version)

    # Provide a simple alias for the build command if no subcommand is provided.
    if ctx.invoked_subcommand is None:
        build()


@app.command()
def build(path: Annotated[Optional[Path], typer.Option()] = "./autobuild.toml"):
    if not os.path.exists(path):
        raise typer.BadParameter(f"Manifest path '{path}' does not exist.")

    # If the path is a directory, assume the manifest file is named "autobuild.toml" inside that directory.
    if os.path.isdir(path):
        path = os.path.join(path, "autobuild.toml")

    # Convert to absolute path to ensure consistency.
    path = os.path.abspath(path)

    # Loading manifest.
    print(f"\nLoading manifest: [magenta]{path}[/magenta]\n")

    from .manifest import Manifest

    manifest = Manifest.load(path)

    if not is_current_version_compatible(manifest.minimum_version):
        raise typer.Exit(
            f"Current version is not compatible with the manifest minimum version: {manifest.minimum_version}"
        )

    godot = godot_local.get_matched_instance(
        manifest.editor_settings.version, mono=manifest.editor_settings.mono
    )

    if godot is None:
        raise typer.Exit(
            f"No compatible Godot instance found for version: {manifest.editor_settings.version}"
        )

    print(
        f"Using Godot instance: [green]{godot.version}[/green] (Mono: {'Yes' if godot.mono else 'No'})"
    )
    print("Path:", godot.path, "\n")

    env = BuilderEnvironment(godot)

    factory = BuilderFactory(env)
    factory.register(GodotBuilder)

    factory.build_all(manifest)


if __name__ == "__main__":
    app()
