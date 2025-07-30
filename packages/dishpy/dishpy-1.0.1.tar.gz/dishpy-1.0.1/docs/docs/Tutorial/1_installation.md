# 1. Installation

## System Requirements

DishPy requires several system tools for downloading and managing VEX components. The requirements vary by operating system:

### Linux/macOS
- `curl` - for downloading files
- `unzip` - for extracting archives
- `bsdtar` - for advanced archive operations
- `git` - for cloning repositories
- `bash` - for running installation scripts

Most Linux distributions and macOS include these tools by default. If any are missing, install them using your system's package manager:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install curl unzip libarchive-tools git bash
```

**macOS (using Homebrew):**
```bash
brew install curl unzip libarchive git
```

### Windows
**⚠️ Important:** DishPy requires Unix-like tools and bash scripts that are not available natively on Windows. **Windows users must use WSL (Windows Subsystem for Linux).**

**Install WSL:**
1. Open PowerShell as Administrator
2. Run: `wsl --install`
3. Restart your computer
4. Set up your Linux distribution (Ubuntu recommended)
5. Install the required tools in WSL:
   ```bash
   sudo apt update
   sudo apt install curl unzip libarchive-tools git bash
   ```

## Python Environment Setup

Make sure you have [uv](https://github.com/astral-sh/uv) installed.



**If you are installing a version of DishPy pre-1.0, which you probably should not be doing,** add the following to your `.zshrc`, `.bashrc`, etc.:
```bash
export UV_INDEX_STRATEGY="unsafe-best-match"
export UV_EXTRA_INDEX_URL="https://test.pypi.org/simple/"
```

Open a new terminal to apply changes, and then run dishpy:
```bash
$ uv tool run dishpy
# or
$ uvx dishpy
# or, for an old version
$ uvx dishpy==0.5.0
# outputs something like
╭─────────────────────────────────── Help ────────────────────────────────────╮
│ dishpy 1.0 - VEX Competition Development Tool                             │
│                                                                             │
│ Commands:                                                                   │
│ create    Create new directory and initialize project                       │
│                 Options: --name <name> (required) --slot --package          │
│ add       Add a previously registered package to a project                  │
│                 Options: package                                            │
│ mu        Build and upload project to VEX V5 brain                          │
│                 Options: --verbose                                          │
│ build     Build project to out directory                                    │
│                 Options: --verbose                                          │
│ upload    Upload project to VEX V5 brain                                    │
│                 Options: path                                               │
│ vexcom    Run vexcom with specified arguments (auto-installs if needed)     │
│                 Options: args                                               │
│ debug     debug DishPy CLI internals                                        │
│ package   Package management commands                                       │
│   list         List all available packages that have been registered with   │
│ DishPy                                                                      │
│   register     Register a package with DishPy                               │
│                 Options: package_path                                       │
│                                                                             │
╰─────────────────────────────────────────────────────────────────────────────╯

```

## First Run

When you first run DishPy commands that require VEXcom tools (like `mu` for uploading), DishPy will automatically download and install the necessary VEX tools. This process may take a few minutes and requires an internet connection.

The tools are cached in your system's cache directory and only need to be downloaded once.
