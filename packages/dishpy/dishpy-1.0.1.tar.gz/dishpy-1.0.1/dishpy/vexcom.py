import platform
import sys
import subprocess
import os
from pathlib import Path
from platformdirs import user_cache_dir
from rich.console import Console

console = Console()


def get_platform() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        if machine in ("arm", "armv7l"):
            return "linux-arm32"
        elif machine in ("aarch64", "arm64"):
            return "linux-arm64"
        else:
            return "linux-x64"
    elif system == "darwin":
        return "osx"
    elif system == "windows":
        return "win32"
    else:
        # Fallback based on architecture
        if sys.maxsize > 2**32:
            return "linux-x64"
        else:
            return "linux-arm32"


def get_vexcom_cache_dir() -> Path:
    """Get the platform-specific cache directory for vexcom tools"""
    cache_dir = Path(user_cache_dir("dishpy", "DishPy"))
    return cache_dir


def get_vexcom_executable() -> Path:
    """Get the path to the vexcom executable for this platform"""
    cache_dir = get_vexcom_cache_dir()
    platform_name = get_platform()

    if platform_name == "win32":
        return cache_dir / "vexcom" / platform_name / "vexcom.exe"
    else:
        return cache_dir / "vexcom" / platform_name / "vexcom"


def is_vexcom_installed() -> bool:
    """Check if vexcom is installed and executable"""
    vexcom_exe = get_vexcom_executable()
    return vexcom_exe.exists() and os.access(vexcom_exe, os.X_OK)


def install_vexcom():
    """Install vexcom tools using the bundled download script"""
    console.print(
        "🔧 [yellow]VEXcom tools not found. Installing (this might take a few minutes)...[/yellow]"
    )

    # Get the script path from the package
    script_dir = Path(__file__).parent
    download_script = script_dir / "download_vexcom.sh"

    if not download_script.exists():
        console.print("❌ [red]Download script not found in package[/red]")
        raise FileNotFoundError(f"Download script not found: {download_script}")

    # Get target directory
    cache_dir = get_vexcom_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Run the download script with the cache directory
        subprocess.run(
            ["bash", str(download_script), str(cache_dir)],
            check=True,
            capture_output=True,
            text=True,
        )

        # Make the executable actually executable on Unix-like systems
        vexcom_exe = get_vexcom_executable()
        if vexcom_exe.exists() and platform.system() != "Windows":
            os.chmod(vexcom_exe, 0o755)

        console.print("✅ [green]VEXcom tools installed successfully[/green]")

    except subprocess.CalledProcessError as e:
        console.print(f"❌ [red]Failed to install VEXcom tools: {e.stderr}[/red]")
        raise
    except Exception as e:
        console.print(f"❌ [red]Error installing VEXcom tools: {e}[/red]")
        raise


def run_vexcom(*args):
    """Run vexcom with the given arguments, installing if necessary"""
    # Check if vexcom is installed, install if not
    if not is_vexcom_installed():
        install_vexcom()

    # Verify installation was successful
    if not is_vexcom_installed():
        console.print("❌ [red]VEXcom installation failed[/red]")
        return subprocess.CompletedProcess(args=[], returncode=1)

    vexcom_exe = get_vexcom_executable()
    return subprocess.run([str(vexcom_exe)] + list(args))
