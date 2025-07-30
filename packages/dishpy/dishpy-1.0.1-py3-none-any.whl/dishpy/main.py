import sys
import os
import shutil
import argparse
from pathlib import Path
from . import __version__
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from .vexcom import run_vexcom, get_vexcom_cache_dir
from .amalgamator import combine_project
from .utils import get_url_file_type, dir_path
import tomllib
import tomli_w
import textcase
import validators
import hashlib
import subprocess
from copy import copy

console = Console()


class Project:
    def __init__(self, path: Path, name: str, slot: int):
        self.path = path
        self.src = path / "src"
        self.main_file = path / "src" / "main.py"
        self.vex_dir = path / "src" / "vex"
        self.vex_init = path / "src" / "vex" / "__init__.py"
        self.out_dir = path / ".out"

        self.name = name
        self.slot = slot

        for i in [self.src, self.main_file, self.vex_dir, self.vex_init, self.out_dir]:
            if not i.exists():
                raise FileNotFoundError()

    @staticmethod
    def scaffold(
        path: Path | None = None, name: str | None = None, slot: int | None = None
    ):
        if not path:
            path = Path.cwd()
        if not name:
            name = "My DishPy Project"
        if not slot:
            slot = 1
        with open(path / "dishpy.toml", "w") as f:
            f.write(f'[project]\nname = "{name}"\nslot = {slot}\n')
        src = path / "src"
        main_file = path / "src" / "main.py"
        vex_dir = path / "src" / "vex"
        vex_init = path / "src" / "vex" / "__init__.py"
        out_dir = path / ".out"

        name = name
        slot = slot

        for i in [src, vex_dir, out_dir]:
            if not i.exists():
                i.mkdir()

        script_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(script_dir, "resources", "template.py")
        vex_path = os.path.join(script_dir, "resources", "vex.py")

        # Copy template to src/main.py
        shutil.copy2(template_path, main_file)
        shutil.copy2(vex_path, vex_init)

    def upload(self, path: Path):
        run_vexcom("--name", self.name, "--slot", str(self.slot), "--write", str(path))

    def build(self, verbose=False):
        combine_project(self.main_file, self.out_dir / "main.py", verbose)

    def add(self, package: str, path_to_go: Path | None = None):
        package_path = get_vexcom_cache_dir() / "packages" / f"{package}.zip"
        # this *will* panic if the package is not found, but we try `list` first so it's not a huge deal
        name, version = package.split(":")
        if not path_to_go:
            path_to_go = self.src
        path_to_go = path_to_go / name
        subprocess.run(
            [
                "unzip",
                "-o",  # overwrite existing files without prompting
                str(package_path),
                "-d",
                str(path_to_go),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        with open(self.path / "dishpy.toml", "rb") as f:
            config = tomllib.load(f)
        if "dependencies" not in config:
            config["dependencies"] = {}
        config["dependencies"][name] = version
        with open(self.path / "dishpy.toml", "wb") as f:
            tomli_w.dump(config, f)
        console.print(
            f"✨ [green]Added package [bold cyan]{package}[/bold cyan][/green]"
        )


class Package(Project):
    def __init__(
        self, path: Path, name: str, slot: int, package_name: str, version: str
    ):
        Project.__init__(self, path, name, slot)
        self.package_name = package_name
        self.version = version

    @staticmethod
    def scaffold(
        path: Path | None = None,
        name: str | None = None,
        slot: int | None = None,
        package_name: int | None = None,
    ):
        if not path:
            path = Path.cwd()
        if not name:
            name = "My DishPy Project"
        if not slot:
            slot = 1
        if not package_name:
            package_name = textcase.snake(name)
        Project.scaffold(path, name, slot)
        with open(path / "dishpy.toml", "rb") as f:
            project_config = tomllib.load(f)
        project_config["package"] = {}
        project_config["package"]["package_name"] = textcase.snake(package_name)
        project_config["package"]["version"] = "0.1.0"
        with open(path / "dishpy.toml", "wb") as f:
            tomli_w.dump(project_config, f)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        pkg_template = os.path.join(script_dir, "resources", "pkg_template.py")
        pkg_init = path / "src" / package_name / "__init__.py"
        pkg_path = path / "src" / package_name
        if not pkg_path.exists():
            pkg_path.mkdir()

        shutil.copy2(pkg_template, pkg_init)

    def register(self):
        packages_path = get_vexcom_cache_dir() / "packages"
        if not packages_path.exists():
            packages_path.mkdir()
        zip_path = packages_path / f"{self.package_name + ':' + self.version}.zip"
        if zip_path.exists():
            zip_path.unlink()
        package_path = self.src / self.package_name
        if not package_path.exists():
            raise Exception(
                f"Package '{self.package_name}' in {package_path} not found"
            )
        subprocess.run(
            [
                "zip",
                "-r",
                str(zip_path),
                ".",
            ],
            cwd=self.src / self.package_name,
            check=True,
            capture_output=True,
            text=True,
        )
        console.print(
            f"✨ [green]Registered package [bold cyan]{self.package_name + ':' + self.version}[/bold cyan][/green]"
        )

    @staticmethod
    def list() -> list[str]:
        packages_path = get_vexcom_cache_dir() / "packages"
        if not packages_path.exists():
            packages_path.mkdir()
        pkgs = []
        for i in packages_path.iterdir():
            if i.suffix == ".zip":
                pkgs.append(i.name[:-4])
        return pkgs

    @staticmethod
    def generate_path(package: str) -> tuple[Path, callable]:
        package_hashed = copy(package)
        # package will soon become a Path
        if Path(package).exists():
            return Path(package), lambda: None
        package_path = Path(hashlib.md5(package.encode()).hexdigest()[:8])
        while package_path.exists():
            package_hashed += hashlib.md5(package.encode()).hexdigest()[:8]
            package_path = Path(hashlib.md5(package_hashed.encode()).hexdigest()[:8])
        package_path.mkdir()
        if validators.url(package) and "application/zip" in get_url_file_type(package):
            # This is a zip file, download & unzip
            subprocess.run(
                ["curl", "-s", "-L", package, "-o", str(package_path / "pkg.zip")],
                check=True,
            )
            subprocess.run(
                [
                    "bsdtar",
                    "--strip-components=1",
                    "-xvf",
                    str(package_path / "pkg.zip"),
                    "-C",
                    str(package_path),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            # This is a git repo, clone
            subprocess.run(
                ["git", "clone", str(package), str(package_path), "-q"], check=True, text=True
            )
        return package_path, lambda: shutil.rmtree(package_path)

    def add(self, package: str):
        console.print(
            f"✨ [yellow]This project is a package, adding package [bold cyan]{package}[/bold cyan] [i]into the package directory[/i] to avoid conflicts when importing package {self.package_name} into other projects[/yellow]"
        )
        super().add(package, self.src / self.package_name)


class DishPy:
    def __init__(self, path: Path):
        self.path = path
        config_path = self.path / "dishpy.toml"
        if not config_path.exists():
            raise FileNotFoundError("Cannot find 'dishpy.toml' in current directory")
        with open(config_path, "rb") as f:
            self.config = tomllib.load(f)
        if (
            (project := self.config.get("project"))
            and (name := project.get("name"))
            and (slot := project.get("slot"))
        ):
            try:
                if (
                    (package := self.config.get("package"))
                    and (package_name := package.get("package_name"))
                    and (version := package.get("version"))
                ):
                    self.instance = Package(
                        self.path, name, slot, package_name, version
                    )
                else:
                    self.instance = Project(self.path, name, slot)
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Project '{self.config['project']['name']}' not found"
                )
        else:
            raise FileNotFoundError("Malformed 'dishpy.toml' file")


class Cli:
    COMMANDS = {
        "create": {
            "help": "Create new directory and initialize project",
            "arguments": [
                {"name": "--name", "required": True, "help": "Project name (required)"},
                {"name": "--slot", "type": int, "help": "Project slot number"},
                {
                    "name": "--package",
                    "nargs": "?",
                    "const": True,
                    "default": False,
                    "help": "Create as a package (optionally specify package name)",
                },
            ],
        },
        "add": {
            "help": "Add a previously registered package to a project",
            "arguments": [
                {
                    "name": "package",
                    "help": "Package name in name:version format (required)",
                },
            ],
        },
        "mu": {
            "help": "Build and upload project to VEX V5 brain",
            "arguments": [
                {
                    "name": "--verbose",
                    "action": "store_true",
                    "help": "Enable verbose output",
                }
            ],
        },
        "build": {
            "help": "Build project to out directory",
            "arguments": [
                {
                    "name": "--verbose",
                    "action": "store_true",
                    "help": "Enable verbose output",
                }
            ],
        },
        "upload": {
            "help": "Upload project to VEX V5 brain",
            "arguments": [
                {
                    "name": "path",
                    "help": "Path to file to upload",
                }
            ],
        },
        "vexcom": {
            "help": "Run vexcom with specified arguments (auto-installs if needed)",
            "arguments": [
                {
                    "name": "args",
                    "nargs": argparse.REMAINDER,
                    "help": "Arguments to pass to vexcom (accepts anything after 'vexcom')",
                }
            ],
        },
        "debug": {
            "help": "debug DishPy CLI internals",
            "arguments": [],
        },
        "package": {
            "help": "Package management commands",
            "subcommands": {
                "list": {
                    "help": "List all available packages that have been registered with DishPy",
                    "arguments": [],
                },
                "register": {
                    "help": "Register a package with DishPy",
                    "arguments": [
                        {
                            "name": "package_path",
                            "type": "dir_path",
                            "help": "Path to package directory. Can also be a git repo or link to azip file",
                        }
                    ],
                },
            },
        },
    }

    @staticmethod
    def show_help():
        """Display help information"""
        help_text = Text()
        help_text.append(f"dishpy {__version__}", style="bold magenta")
        help_text.append(" - VEX Competition Development Tool\n\n", style="white")
        help_text.append("Commands:\n", style="bold white")

        for cmd_name, cmd_info in Cli.COMMANDS.items():
            help_text.append(f"{cmd_name:<10}", style="bold cyan")
            help_text.append(f"{cmd_info['help']}\n", style="white")

            # Handle subcommands
            if "subcommands" in cmd_info:
                for sub_name, sub_info in cmd_info["subcommands"].items():
                    help_text.append(f"  {sub_name:<13}", style="cyan")
                    help_text.append(f"{sub_info['help']}\n", style="white")
                    if sub_info["arguments"]:
                        help_text.append("\t\t", style="cyan")
                        options = []
                        for arg in sub_info["arguments"]:
                            if arg["name"]:
                                if arg.get("required"):
                                    options.append(
                                        f"{arg['name']} <{arg['name'].removeprefix('--')}> (required)"
                                    )
                                elif arg.get("action") == "store_true":
                                    options.append(arg["name"])
                                else:
                                    options.append(f"{arg['name']}")
                        if options:
                            help_text.append(
                                f"Options: {' '.join(options)}\n", style="dim white"
                            )
            elif cmd_info["arguments"]:
                help_text.append("\t\t", style="bold cyan")
                options = []
                for arg in cmd_info["arguments"]:
                    if arg["name"]:
                        if arg.get("required"):
                            options.append(
                                f"{arg['name']} <{arg['name'].removeprefix('--')}> (required)"
                            )
                        elif arg.get("action") == "store_true":
                            options.append(arg["name"])
                        else:
                            options.append(f"{arg['name']}")
                if options:
                    help_text.append(
                        f"Options: {' '.join(options)}\n", style="dim white"
                    )

        panel = Panel(
            help_text, title="[bold blue]Help[/bold blue]", border_style="blue"
        )
        console.print(panel)

    @staticmethod
    def parse_args():
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(
            description="DishPy - VEX Competition Development Tool", add_help=False
        )
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        for cmd_name, cmd_info in Cli.COMMANDS.items():
            cmd_parser = subparsers.add_parser(cmd_name, help=cmd_info["help"])

            # Handle subcommands
            if "subcommands" in cmd_info:
                sub_subparsers = cmd_parser.add_subparsers(
                    dest="subcommand", help="Available subcommands"
                )
                for sub_name, sub_info in cmd_info["subcommands"].items():
                    sub_parser = sub_subparsers.add_parser(
                        sub_name, help=sub_info["help"]
                    )
                    for arg in sub_info["arguments"]:
                        arg_kwargs = {k: v for k, v in arg.items() if k != "name"}
                        if arg_kwargs.get("type") == "dir_path":
                            arg_kwargs["type"] = dir_path
                        sub_parser.add_argument(arg["name"], **arg_kwargs)
            else:
                for arg in cmd_info["arguments"]:
                    arg_kwargs = {k: v for k, v in arg.items() if k != "name"}
                    if arg_kwargs.get("type") == "dir_path":
                        arg_kwargs["type"] = dir_path
                    cmd_parser.add_argument(arg["name"], **arg_kwargs)

        return parser

    def __init__(self):
        self.console = console

    def list(self):
        try:
            packages = Package.list()
            if packages:
                console.print(
                    "✨ [green]Found the following packages registered with DishPy: "
                    + f"{', '.join(Package.list())} [/green]"
                )
            else:
                console.print("❌ [red]No packages registered with DishPy[/red]")
        except Exception as e:
            self.console.print(f"❌ [red]Error: {e}[/red]")

    def add(self, args):
        try:
            assert args.package in Package.list()
        except Exception:
            self.console.print(
                f"❌ [red]Error: {args.package} is not a registered package[/red]"
            )
            self.console.print(
                "[red]Run `dishpy package list` to see a list of registered packages[/red]"
            )
            return
        instance = DishPy(Path())
        try:
            instance.instance.add(args.package)
        except Exception as e:
            self.console.print(f"❌ [red]Error: {e}[/red]")

    def create(self, args):
        path = Path() / args.name
        path.mkdir()
        if not args.package:
            Project.scaffold(path, args.name, args.slot)
            console.print(
                f"✨ [green]Created and initialized project in[/green] [bold cyan]{path}/[/bold cyan]"
            )
        else:
            pkg_name = args.package if isinstance(args.package, str) else args.name
            pkg_name = textcase.snake(pkg_name)
            Package.scaffold(path, args.name, args.slot, pkg_name)
            package_path = path / "src" / pkg_name
            console.print(
                f"✨ [green]Created and initialized project in [bold cyan]{path}/[/bold cyan]"
                + f" with package[/green] [bold cyan]{str(package_path) + '/'}[/bold cyan]"
            )

    def register(self, args):
        try:
            path, cleanup = Package.generate_path(args.package_path)
            dishpy = DishPy(path)
            # cannot do isinstance(dishpy.instance, Project) because inheritance :P
            if not isinstance(dishpy.instance, Package):
                raise Exception(f"{path} is a DishPy project, not a package")
            dishpy.instance.register()
            cleanup()
        except Exception as e:
            console.print(f"❌ [red]Error: {e}[/red]")
            return

    def route(self):
        if len(sys.argv) <= 1 or sys.argv[1] in ["-h", "--help", "help"]:
            self.show_help()
            return
        parser = self.parse_args()
        try:
            args = parser.parse_args()
        except SystemExit:
            self.show_help()
            return
        match args.command:
            case "debug":
                print("cache dir:", get_vexcom_cache_dir())
            case "package":
                match args.subcommand:
                    case "register":
                        self.register(args)
                    case "list":
                        self.list()
                    case _:
                        self.show_help()
            case "create":
                self.create(args)
            case "mu":
                try:
                    instance = DishPy(Path())
                    instance.instance.build(args.verbose)
                    instance.instance.upload(instance.instance.out_dir / "main.py")
                except Exception as e:
                    self.console.print(f"❌ [red]Error: {e}[/red]")
            case "build":
                try:
                    instance = DishPy(Path())
                    instance.instance.build(args.verbose)
                except Exception as e:
                    self.console.print(f"❌ [red]Error: {e}[/red]")
            case "upload":
                try:
                    instance = DishPy(Path())
                    instance.instance.upload(Path(args.path))
                except Exception as e:
                    self.console.print(f"❌ [red]Error: {e}[/red]")
            case "vexcom":
                run_vexcom(*args.args)
            case "add":
                self.add(args)
            case _:
                self.show_help()


def main():
    Cli().route()


if __name__ == "__main__":
    main()
