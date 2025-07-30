# 5. The package registry

This is a continuation of [4. Creating Packages](4_create_packages.md). If you are too lazy to read that, at least go through the philosophy:

## Philosophy

DishPy has a somewhat simple but possibly unfamiliar methodology for its package management. There are a few key things to understand:

* **Packages in DishPy are also regular projects.** All packages also have a `main.py` file, and you can upload a package project to the brain using `uvx dishpy mu`. There are a few commands that have changed meaning in a project which has a package (namely, `uvx dishpy add` has different behavior), but they are otherwise the same commands.
* **When you add a package to a project, only that package's code is copied.** If my package is called `add_two_nums`, its source code will live at `src/add_two_nums/__init__.py` (and `__init__.py` can reference other Python files in `src/add_two_nums/`). When you add `add_two_nums` to another project, only the files in `package_project/src/add_two_nums` will be copied into `my_project/src/add_two_nums` -- `package_project/src/main.py` and other files are not copied.
* **Packages maintain decentralized metadata.** If you are used to Python development, you typically install packages from the Python Package Index (PyPI). PyPI is an example of a **centralized** index, where a central server (or group of servers, whatever) has a database of every registered command. In contrast, PROS and DishPy use an approach where the `dishpy.toml` metadata file of each package project also contains information about the package in that project. Then, when you publish your project to GitHub or another provider, when DishPy fetches that project, it reads the `dishpy.toml` to get the important information about the package.
* **DishPy also maintains a local registry.** Think of this as a PyPI that lives on your computer. You can use DishPy to "fetch" packages, whether from a Git repository, local project, or ZIP file, and Dishpy will then index the project based on the aforementioned metadata and cache it on your hard drive (or SSD, whatever floats your boat). Then, when you ask to add a package to a project, DishPy finds that package in your local cache/registry and installs it into the current project.

This may seem more complex than the centralized PyPI solution, but it actually isn't much harder. Even `uv add` (think `pip` alternative) maintains a "warm cache" of recently fetched packages from PyPI. It also saves me (Aadish) from all of the costs and investment of running my own centralized registry.

## Adding packages to your project

**Make sure you are on version 0.6 before continuing.**

Now that we have a package from Part 4, we can publish it and add it to a new project. Keep these points from the philosophy in mind:

* When you add a package to a project, only that package's code is copied
* DishPy also maintains a local registry

As noted in the philosophy, DishPy caches packages you register in a local folder on your computer. This makes installing a package a two-step process:

1. Running `uvx dishpy package register <package>` to get a package's contents and save them.
2. Running `uvx dishpy add <package>` inside a project to add that project as a dependency and install it.

## Part 1: the registry

There are actually 3 ways to host your project.

### Local

The simplest one is just to register the entire package-project folder. Assuming you are in the `Add Two Numbers` folder from part 4:

```bash
Add Two Numbers $ cd ..
$ uvx dishpy package register "Add Two Numbers"
✨ Registered package add_two_nums:0.1.0
```

Great! That was very simple.
Under the hood, DishPy is

* reading the `dishpy.toml` of the package project to get the package name and version.
* compressing the contents of the package code (not all of `src`, just `src/add_two_nums`) and saving it locally.

### Git

If you host your package project on GitHub or another similar provider (that the Git CLI supports), you can also pass in that. I host a simple package (the same as `Add Two Numbers`) [here](https://github.com/aadishv/dishpy-example-package), so I can just run

```bash
$ uvx dishpy package register https://github.com/aadishv/dishpy-example-package
# or
$ uvx dishpy package register https://github.com/aadishv/dishpy-example-package.git
# outputs
✨ Registered package add_two_nums:0.1.0
```
Under the hood, this:

* clones the repository into a temporary directory,
* runs the same analysis on that directory as detailed above to save the package,
* and deletes the temporary directory.

### Git releases

If you are a power user and want to have better version control for your package, you can tag a commit with a version number, create a GitHub (or GitLab, etc.) release with that version, and publish it. GitHub (I am not sure about other providers) automatically zips your code, so you don't need to build your own binary!

I won't go through the full process for tagging a commit and creating a release here, but it shouldn't be too difficult to find a tutorial online.

An example release is [available in the same repository](https://github.com/aadishv/dishpy-example-package/releases/tag/v0.1.0). Now if you want to install the package at that specific release, you can do so using the link to the source code ZIP:

```bash
$ uvx dishpy package register https://github.com/aadishv/dishpy-example-package/archive/refs/tags/v0.1.0.zip
✨ Registered package add_two_nums:0.1.0
```

### Output

Feel free to skip this section, it doesn't really matter for beginner users.

You might be wondering where DishPy saves your packages. Luckily this isn't too hard to find! DishPy ships with a `debug` command to show information about where the cache is.

```bash
$ uvx dishpy debug
cache dir: /Users/aadishverma/Library/Caches/dishpy
$ cd /Users/aadishverma/Library/Caches/dishpy
~/Library/Caches/dishpy $ ls
packages	vexcom
```

The cache directory will be different depending on system and user, but you should find both a `packages` and `vexcom` directory. (This is assuming that you have using a vexcom command such as `dishpy mu` before, and that you have registered a package.)

Let's see what is in `packages`:
```bash
~/Library/Caches/dishpy $ ls packages
add_two_nums:0.1.0.zip
```
Oh, there's our package! It contains the contents of our package (shocker).
```bash
~/Library/Caches/dishpy $ unzip -l packages/add_two_nums:0.1.0.zip
Archive:  packages/add_two_nums:0.1.0.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
       71  06-15-2025 12:13   __init__.py
---------                     -------
       71                     1 file
```
When we add a package, it just pulls the ZIP file from here to get the source code.

Now that you know how packages are registered and stored locally, let's see how you can actually add them to your own projects.

## Part 2. Adding to a project

Now that we have registered the `add_two_nums` package, let's create a new project and add it as a dependency.

### Listing available packages

First, let's see what packages we have available in our local registry:

```bash
$ uvx dishpy package list
✨ Found the following packages registered with DishPy: add_two_nums:0.1.0
```

Perfect! Our package is there and ready to be used.

### Creating a new project

Let's create a new project to demonstrate adding packages:

```bash
$ uv run dishpy create --name Calculator
✨ Created and initialized project in Calculator/
$ cd Calculator
Calculator $ tree
.
├── dishpy.toml
└── src
    ├── main.py
    └── vex
        └── __init__.py

3 directories, 3 files
```

### Adding a package

Now we can add our `add_two_nums` package to this project. Note that you must specify the package in `package:version` format:

```bash
Calculator $ uv run dishpy add add_two_nums:0.1.0
✨ Added package add_two_nums:0.1.0
```

Let's see what happened to our project structure:

```bash
Calculator $ tree
.
├── dishpy.toml
└── src
    ├── add_two_nums
    │   └── __init__.py
    ├── main.py
    └── vex
        └── __init__.py

4 directories, 4 files
```

As you can see, DishPy created a new `add_two_nums` directory in `src/` and extracted the package contents there. Let's also check what changed in our `dishpy.toml`:

```bash
Calculator $ cat dishpy.toml
[project]
name = "Calculator"
slot = 1

[dependencies]
add_two_nums = "0.1.0"
```

Great! DishPy automatically added the dependency to our configuration file. Now we can use the package in our `main.py`:

```python
from add_two_nums import add_two_numbers
from vex import Brain
brain = Brain()
brain.screen.print(str("10 + 3 = ") + str(add_two_numbers(10, 3)))
```

### Adding packages to package projects

There's a special behavior when you add packages to a project that is itself a package. Let's create a new package project to demonstrate this:

```bash
Calculator $ cd ..
$ uv run dishpy create --name "Math Utils" --package
✨ Created and initialized project in Math Utils/ with package Math Utils/src/math_utils/
$ cd "Math Utils"
Math Utils $ uv run dishpy add add_two_nums:0.1.0
✨ This project is a package, adding package add_two_nums:0.1.0 into the package directory
to avoid conflicts when importing package math_utils into other projects
✨ Added package add_two_nums:0.1.0
```

Let's see where the package was installed:

```bash
Math Utils $ tree
.
├── dishpy.toml
└── src
    ├── main.py
    ├── math_utils
    │   ├── __init__.py
    │   └── add_two_nums
    │       └── __init__.py
    └── vex
        └── __init__.py

5 directories, 5 files
```

Notice that instead of installing `add_two_nums` directly in `src/`, it was installed inside `src/math_utils/`. This is intentional! When you're developing a package and you add dependencies, those dependencies become part of your package. This way, when someone else installs your `math_utils` package, they don't need to separately install `add_two_nums` – it's already bundled in.

Let's check the `dishpy.toml`:

```bash
Math Utils $ cat dishpy.toml
[project]
name = "Math Utils"
version = "0.1.0"

[package]
name = "math_utils"

[dependencies]
add_two_nums = "0.1.0"
```

Now you can use the dependency in your package code:

```python
# src/math_utils/__init__.py
from .add_two_nums import add_two_nums

def add_and_multiply(a, b, multiplier):
    """Add two numbers and then multiply by a multiplier."""
    sum_result = add_two_nums(a, b)
    return sum_result * multiplier
```

### Key points to remember

1. **Package format**: Always specify packages in `package:version` format when adding them.
2. **Registry first**: You can only add packages that you've previously registered using `uvx dishpy package register`.
3. **Use `list` to check**: Run `uvx dishpy package list` to see all available packages in your local registry.
4. **Different behavior for package projects**: When adding packages to a package project, they get installed into the package directory to avoid dependency conflicts.
5. **Automatic configuration**: DishPy automatically updates your `dishpy.toml` with the new dependency.

This approach ensures that your packages are self-contained and don't create complex dependency trees when shared with others!
