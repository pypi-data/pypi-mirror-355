# 4. Creating packages

DishPy 0.5.0 shipped with a beta (extremely experimental) version of package management through a registry-based system (somewhat similar to PROS' approach, but much simpler and more limited in scope).

v1.0 finally stabilizes the API for those commands, so we can begin writing tutorials!

## Philosophy

DishPy has a somewhat simple but possibly unfamiliar methodology for its package management. There are a few key things to understand:

* **Packages in DishPy are also regular projects.** All packages also have a `main.py` file, and you can upload a package project to the brain using `uvx dishpy mu`. There are a few commands that have changed meaning in a project which has a package (namely, `uvx dishpy add` has different behavior), but they are otherwise the same commands.
* **When you add a package to a project, only that package's code is copied.** If my package is called `add_two_nums`, its source code will live at `src/add_two_nums/__init__.py` (and `__init__.py` can reference other Python files in `src/add_two_nums/`). When you add `add_two_nums` to another project, only the files in `package_project/src/add_two_nums` will be copied into `my_project/src/add_two_nums` -- `package_project/src/main.py` and other files are not copied.
* **Packages maintain decentralized metadata.** If you are used to Python development, you typically install packages from the Python Package Index (PyPI). PyPI is an example of a **centralized** index, where a central server (or group of servers, whatever) has a database of every registered command. In contrast, PROS and DishPy use an approach where the `dishpy.toml` metadata file of each package project also contains information about the package in that project. Then, when you publish your project to GitHub or another provider, when DishPy fetches that project, it reads the `dishpy.toml` to get the important information about the package.
* **DishPy also maintains a local registry.** Think of this as a PyPI that lives on your computer. You can use DishPy to "fetch" packages, whether from a Git repository, local project, or ZIP file, and Dishpy will then index the project based on the aforementioned metadata and cache it on your hard drive (or SSD, whatever floats your boat). Then, when you ask to add a package to a project, DishPy finds that package in your local cache/registry and installs it into the current project.

This may seem more complex than the centralized PyPI solution, but it actually isn't much harder. Even `uv add` (think `pip` alternative) maintains a "warm cache" of recently fetched packages from PyPI. It also saves me (Aadish) from all of the costs and investment of running my own centralized registry.

## Creating your first package

Let's actually start working. As we go, keep these points from the philosophy in mind:

* Packages in DishPy are also regular projects
* Packages maintain decentralized metadata

Recall the `create` command:

> `uvx dishpy create --name "my-robot"`

> You can also specify which slot on the V5 brain your program should use (defaults to slot 1):

> `uvx dishpy create --name "my-robot" --slot 2`

One option we didn't mention before is the `--package` option. You can use it as a flag, which will initialize the project with a package whose name is the project name converted to snake case, or pass a string as the package name.

```bash
# create a project "DP Test Project" with package "dp_test_project"
uvx dishpy create --name "my-robot" --package
# create a project "DP Test Project" with package "add_two_nums"
uvx dishpy create --name "my-robot" --package "add_two_nums"
# create a project "Add Two Numbers" with package "add_two_nums" that uploads to slot 2
uvx dishpy create --name "Add Two Numbers" --package "add_two_nums" --slot 2
```

Let's run the last option.

```bash
$ uv run dishpy create --name "Add Two Numbers" --package add_two_nums --slot 2
✨ Created and initialized project in Add Two Numbers/ with package Add Two Numbers/src/add_two_nums/
$ tree "Add Two Numbers/"
Add Two Numbers/
├── dishpy.toml
└── src
    ├── add_two_nums
    │   └── __init__.py
    ├── main.py
    └── vex
        └── __init__.py

4 directories, 4 files
```

Great. Most of this looks familiar, but there are two changed files to look out for.

### `dishpy.toml`
```toml
[project]
name = "Add Two Numbers"
slot = 2

[package]
package_name = "add_two_nums"
version = "0.1.0"
```

The project section is nearly identical, but now there is an all-new `package` section. This is the "decentralized metadata," which DishPy ues to get information about a package when fetching it.

* The `package_name` is the just the subdirectory of `src` where the code is. In this case, all of the package code resides in `Add Two Numbers/src/add_two_nums/`.
* The `version` isn't necessarily a version. DishPy doesn't enforce SemVer or anything. It's really just a unique identifier of a specific snapshot of your repository. You could have `version = "latest"` or `version = 'prerelease'` and DishPy wouldn't care.

### `src/add_two_nums/__init__.py`

As previous noted, your package will live in `src/add_two_nums`. `__init__.py` is the entrypoint for your package. If you write

```python
import add_two_nums
```

in `main.py`, that's basically shorthand for

```python
import "add_two_nums/__init__.py" as add_two_nums
```

Right now, your `__init__.py` just looks like this:

```python
"Put your package code!"


def add_two_numbers(a, b):
    return a + b
```

which is honestly pretty boring, but a good starting point. Now, in your `main.py`, you can write code such as

```python
from add_two_nums import add_two_numbers
from vex import Brain
brain = Brain()
brain.screen.print(str("10 + 3 = ") + str(add_two_numbers(10, 3)))
```

to import the function from your package and call it.

Your package doesn't only have to be one file! Using the multifile capabilities of DishPy, you can have extra files (`src/add_two_nums/validation.py`) or even submodules (`src/add_two_nums/some_submodule/__init__.py`). Just make sure your `src/add_two_nums/__init__.py` imports those so it is available to whoever imports `add_two_nums`.

Anything in the `add_two_nums` directory is part of the source code of your package and will be copied into projects that import it.
