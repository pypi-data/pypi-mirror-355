# godot-autobuild

[godot-autobuild](https://github.com/nofuncoding/godot-autobuild) is a tool for building godot projects automatically
written in Python.

## Get started

Install [godot-autobuild](https://github.com/nofuncoding/godot-autobuild) with [uv](https://github.com/astral-sh/uv) is recommended.
Alternatively, you can also use `pipx` or `pip`.

```bash
uv tool install godot_autobuild # Recommended
uvx godot_autobuild # Directly

pipx install godot_autobuild
pip install godot_autobuild
```

After installing it, create a new file named `autobuild.toml` besides your godot project's directory. Here's an example:

```toml
autobuild = "0.1" # Minimal version of godot autobuild

[editor]
version = "4.4" # Godot editor version used during build

[target.dodge_the_creeps]
path = "./dodge_the_creeps" # Path to your project, relative to manifest
default = true # Build this target by default
```

And then you can start building easily:

```bash
gdbuild
gdbuild build # Options in this sub-command
```

## Development

This project is developed using [uv](https://github.com/astral-sh/uv) in Python 3.11+.

Commits and PRs are welcome!

To run the tests, run

```bash
uv pip install -e .
uv run pytest
```

To build the package, run

```bash
hatch build
```

## License

[godot-autobuild](https://github.com/nofuncoding/godot-autobuild) is licensed under the MIT license.