import rich.panel
import typer
from ..builder import Builder
from rich import print
import rich
import subprocess
import os.path
import platform


class GodotBuilder(Builder):
    def build(self, target):
        godot = self.builder_env.godot
        out_path = self.get_out_path(self.builder_env.build_path, target)

        # Ensure the output directory exists
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        # Build the target using the Godot instance
        proc = subprocess.run(
            [
                godot.path,
                "--path",
                target.path,
                "--headless",
                "--export-debug",
                "Windows Desktop",
                out_path,
            ],
            stderr=subprocess.PIPE,
            encoding="utf-8",
        )

        # Check if the build was successful
        if proc.returncode != 0:
            print("\n[red]Build failed.[/red] Caused by:")
            rich.console.Console().print(
                rich.panel.Panel(proc.stderr, title="Stderr", title_align="left")
            )

            # TODO: parse error
            raise typer.Exit(proc.returncode, f"Build failed for target: {target.id}")

        print(f"\n[green]Build successful![/green] Output: {out_path}")

    def can_build(self, target):
        return target.type == "godot"

    def get_out_path(self, path, target) -> str:
        match platform.system():
            case "Windows":
                return os.path.join(path, f"{target.id}.exe")
            case "Linux":
                return os.path.join(path, f"{target.id}")
            case "Darwin":
                return os.path.join(path, f"{target.id}.app")
            case _:
                raise NotImplementedError(f"Unsupported platform: {platform.system()}")
