import ast
import os
import hashlib
from collections import defaultdict
from rich.console import Console


class Prefixer(ast.NodeTransformer):
    """
    Transforms AST to:
    1. Prefix symbols that need prefixing
    2. Remove import statements for local modules
    3. Update references to imported symbols
    """

    def __init__(self, file_path, global_rename_map, symbol_origins, declared_symbols):
        self.file_path = file_path
        self.global_rename_map = global_rename_map
        self.symbol_origins = symbol_origins.get(file_path, {})
        self.declared_symbols = declared_symbols
        self.local_symbols = declared_symbols.get(file_path, set())

    def visit_Name(self, node):
        """Transform name references based on symbol origins and global rename map."""
        name = node.id

        # Check if this name is imported from another file
        if name in self.symbol_origins:
            origin_file, original_name = self.symbol_origins[name]
            # Check if the symbol was renamed in the origin file
            if (
                origin_file in self.global_rename_map
                and original_name in self.global_rename_map[origin_file]
            ):
                new_name = self.global_rename_map[origin_file][original_name]
                node.id = new_name
                return node

        # Check if this is a local symbol that should be prefixed
        if (
            name in self.local_symbols
            and self.file_path in self.global_rename_map
            and name in self.global_rename_map[self.file_path]
        ):
            new_name = self.global_rename_map[self.file_path][name]
            node.id = new_name
            return node

        return node

    def visit_FunctionDef(self, node):
        """Handle function definitions - prefix if needed."""
        if (
            node.name in self.local_symbols
            and self.file_path in self.global_rename_map
            and node.name in self.global_rename_map[self.file_path]
        ):
            new_name = self.global_rename_map[self.file_path][node.name]
            node.name = new_name

        # Transform function arguments
        for arg in node.args.args:
            self.visit_arg(arg)

        # Transform annotations
        if node.returns:
            node.returns = self._visit_annotation(node.returns)

        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        return self.visit_FunctionDef(node)

    def visit_arg(self, node):
        if node.annotation:
            node.annotation = self._visit_annotation(node.annotation)
        return node

    def visit_AnnAssign(self, node):
        if node.annotation:
            node.annotation = self._visit_annotation(node.annotation)
        return self.generic_visit(node)

    def _visit_annotation(self, node):
        """Handle type annotations which may reference symbols."""
        if isinstance(node, ast.Name):
            name = node.id
            # Check if this annotation refers to an imported symbol
            if name in self.symbol_origins:
                origin_file, original_name = self.symbol_origins[name]
                if (
                    origin_file in self.global_rename_map
                    and original_name in self.global_rename_map[origin_file]
                ):
                    new_name = self.global_rename_map[origin_file][original_name]
                    node.id = new_name
            # Check if this annotation refers to a local symbol
            elif (
                name in self.local_symbols
                and self.file_path in self.global_rename_map
                and name in self.global_rename_map[self.file_path]
            ):
                new_name = self.global_rename_map[self.file_path][name]
                node.id = new_name
        elif hasattr(node, "__dict__"):
            # Recursively visit other node types
            for field, value in ast.iter_fields(node):
                if isinstance(value, ast.AST):
                    setattr(node, field, self._visit_annotation(value))
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, ast.AST):
                            value[i] = self._visit_annotation(item)
        return node

    def visit_ClassDef(self, node):
        """Handle class definitions - prefix if needed."""
        if (
            node.name in self.local_symbols
            and self.file_path in self.global_rename_map
            and node.name in self.global_rename_map[self.file_path]
        ):
            new_name = self.global_rename_map[self.file_path][node.name]
            node.name = new_name
        return self.generic_visit(node)

    def visit_Global(self, node):
        """Handle global statements - update names if they were prefixed."""
        new_names = []
        for name in node.names:
            if (
                name in self.local_symbols
                and self.file_path in self.global_rename_map
                and name in self.global_rename_map[self.file_path]
            ):
                new_name = self.global_rename_map[self.file_path][name]
                new_names.append(new_name)
            else:
                new_names.append(name)
        node.names = new_names
        return node

    def visit_Import(self, node):
        """Remove local imports."""
        return None

    def visit_ImportFrom(self, node):
        """Remove local imports."""
        return None


def _get_local_module_map(project_dir, verbose=False):
    """Create a mapping from module name to file path for all local Python files."""
    local_module_map = {}

    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                abs_path = os.path.abspath(file_path)
                rel_path = os.path.relpath(abs_path, project_dir)
                module_path = rel_path.replace(os.sep, ".").replace(".py", "")

                # Handle __init__.py files
                if module_path.endswith(".__init__"):
                    module_path = module_path[:-9]  # Remove .__init__

                local_module_map[module_path] = abs_path
                if verbose:
                    print(f"DEBUG: Module '{module_path}' -> {rel_path}")

    return local_module_map


def _analyze_project(entry_file, local_module_map, verbose=False):
    """
    Analyzes the project to understand symbol-level dependencies.
    Returns a dependency graph where each symbol depends on other symbols.
    """
    if verbose:
        print(f"DEBUG: Starting project analysis from entry file: {entry_file}")

    symbol_deps = defaultdict(set)  # symbol -> set of symbols it depends on
    declared_symbols = defaultdict(set)  # file -> set of symbols declared in that file
    symbol_to_file = {}  # symbol -> file where it's declared
    symbol_origins = defaultdict(dict)  # file -> {symbol: (origin_file, original_name)}
    external_imports = set()

    files_to_scan = [os.path.abspath(entry_file)]
    scanned_files = set()

    while files_to_scan:
        current_file = files_to_scan.pop(0)
        if current_file in scanned_files:
            continue
        scanned_files.add(current_file)

        if verbose:
            print(f"DEBUG: Scanning file: {current_file}")

        try:
            with open(current_file, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content, filename=current_file)
        except Exception as e:
            if verbose:
                print(f"DEBUG: Error reading/parsing {current_file}: {e}")
            continue

        # Find declared symbols
        for i, node in enumerate(tree.body):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                symbol_name = f"{current_file}::{node.name}"
                declared_symbols[current_file].add(node.name)
                symbol_to_file[symbol_name] = current_file
                if verbose:
                    print(
                        f"DEBUG: Found {type(node).__name__} '{node.name}' in {os.path.basename(current_file)}"
                    )
            elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
                for target in targets:
                    if isinstance(target, ast.Name):
                        symbol_name = f"{current_file}::{target.id}"
                        declared_symbols[current_file].add(target.id)
                        symbol_to_file[symbol_name] = current_file
                        if verbose:
                            print(
                                f"DEBUG: Found variable '{target.id}' in {os.path.basename(current_file)}"
                            )
            elif current_file == entry_file and isinstance(node, ast.Expr):
                # Handle top-level expressions only in the main entry file
                expr_name = f"__expr_{i}"
                symbol_name = f"{current_file}::{expr_name}"
                declared_symbols[current_file].add(expr_name)
                symbol_to_file[symbol_name] = current_file
                if verbose:
                    print(
                        f"DEBUG: Found top-level expression '{expr_name}' in {os.path.basename(current_file)}"
                    )

        # Find imports and dependencies
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if verbose:
                        print(
                            f"DEBUG: Found import '{alias.name}' in {os.path.basename(current_file)}"
                        )
                    if alias.name == "vex" or alias.name.startswith("vex."):
                        external_imports.add(ast.unparse(node))
                    elif alias.name in local_module_map:
                        dep_path = local_module_map[alias.name]
                        if dep_path not in scanned_files:
                            files_to_scan.append(dep_path)
                    else:
                        external_imports.add(ast.unparse(node))

            elif isinstance(node, ast.ImportFrom):
                module_name = node.module
                if verbose:
                    print(
                        f"DEBUG: Found 'from {module_name} import ...' in {os.path.basename(current_file)}"
                    )

                if module_name == "vex" or (
                    module_name and module_name.startswith("vex.")
                ):
                    external_imports.add(ast.unparse(node))
                else:
                    is_local = module_name in local_module_map
                    origin_file = None

                    if is_local:
                        origin_file = local_module_map[module_name]
                    else:
                        # Try package-relative imports
                        current_rel_path = os.path.relpath(
                            current_file, os.path.dirname(os.path.dirname(current_file))
                        )
                        current_module_path = current_rel_path.replace(
                            os.sep, "."
                        ).replace(".py", "")
                        if current_module_path.endswith(".__init__"):
                            current_module_path = current_module_path[:-9]

                        package_parts = current_module_path.split(".")
                        for i in range(len(package_parts)):
                            package_prefix = ".".join(
                                package_parts[: len(package_parts) - i]
                            )
                            if package_prefix:
                                potential_module = f"{package_prefix}.{module_name}"
                                if potential_module in local_module_map:
                                    origin_file = local_module_map[potential_module]
                                    is_local = True
                                    break

                    if is_local and origin_file:
                        if origin_file not in scanned_files:
                            files_to_scan.append(origin_file)

                        for alias in node.names:
                            if alias.name == "*":
                                symbol_origins[current_file]["__WILDCARD_FROM__"] = (
                                    origin_file
                                )
                            else:
                                symbol_origins[current_file][alias.name] = (
                                    origin_file,
                                    alias.name,
                                )
                    elif node.level == 0:
                        external_imports.add(ast.unparse(node))

    # Handle wildcard imports
    for file_path, origins in symbol_origins.items():
        if "__WILDCARD_FROM__" in origins:
            wildcard_source = origins["__WILDCARD_FROM__"]
            del origins["__WILDCARD_FROM__"]
            for symbol in declared_symbols.get(wildcard_source, set()):
                origins[symbol] = (wildcard_source, symbol)

    # Build symbol-level dependency graph
    for file_path in scanned_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content, filename=file_path)
        except Exception:
            continue

        # Find which symbols each declared symbol depends on
        for i, node in enumerate(tree.body):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                symbol_name = f"{file_path}::{node.name}"
                deps = _find_symbol_dependencies(
                    node,
                    symbol_origins.get(file_path, {}),
                    declared_symbols.get(file_path, set()),
                    file_path,
                )
                symbol_deps[symbol_name].update(deps)
            elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
                for target in targets:
                    if isinstance(target, ast.Name):
                        symbol_name = f"{file_path}::{target.id}"
                        # For assignments, we need to look at the value being assigned
                        if isinstance(node, ast.Assign):
                            deps = _find_symbol_dependencies(
                                node.value,
                                symbol_origins.get(file_path, {}),
                                declared_symbols.get(file_path, set()),
                                file_path,
                            )
                        elif isinstance(node, ast.AnnAssign) and node.value:
                            deps = _find_symbol_dependencies(
                                node.value,
                                symbol_origins.get(file_path, {}),
                                declared_symbols.get(file_path, set()),
                                file_path,
                            )
                        else:
                            deps = _find_symbol_dependencies(
                                node,
                                symbol_origins.get(file_path, {}),
                                declared_symbols.get(file_path, set()),
                                file_path,
                            )
                        symbol_deps[symbol_name].update(deps)
            elif file_path == entry_file and isinstance(node, ast.Expr):
                # Handle top-level expressions only in the main entry file
                expr_name = f"__expr_{i}"
                symbol_name = f"{file_path}::{expr_name}"
                deps = _find_symbol_dependencies(
                    node,
                    symbol_origins.get(file_path, {}),
                    declared_symbols.get(file_path, set()),
                    file_path,
                )
                symbol_deps[symbol_name].update(deps)

    return (
        symbol_deps,
        declared_symbols,
        symbol_origins,
        external_imports,
        scanned_files,
        symbol_to_file,
    )


def _find_symbol_dependencies(node, symbol_origins, local_symbols, file_path):
    """Find what symbols a given AST node depends on."""
    dependencies = set()

    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
            name = child.id
            if name in symbol_origins:
                origin_file, original_name = symbol_origins[name]
                dependencies.add(f"{origin_file}::{original_name}")
            elif name in local_symbols:
                # This is a reference to a local symbol in the same file
                dependencies.add(f"{file_path}::{name}")

    return dependencies


def _topological_sort_symbols(symbol_deps, symbol_to_file):
    """Topologically sort symbols based on their dependencies."""
    sorted_symbols = []
    visited = set()
    visiting = set()  # To detect cycles

    def visit(symbol):
        if symbol in visited:
            return
        if symbol in visiting:
            # Cycle detected - just add it and continue
            sorted_symbols.append(symbol)
            return

        visiting.add(symbol)

        for dep in symbol_deps.get(symbol, set()):
            if dep in symbol_to_file:  # Only visit dependencies that are in our project
                visit(dep)

        visiting.remove(symbol)
        visited.add(symbol)
        sorted_symbols.append(symbol)

    # Process all symbols
    all_symbols = set(symbol_to_file.keys())
    for deps in symbol_deps.values():
        all_symbols.update(deps)

    for symbol in sorted(all_symbols):
        if symbol in symbol_to_file:  # Only process symbols that are in our project
            visit(symbol)

    return sorted_symbols


def combine_project(main_file, output_file, verbose=False):
    """
    Combines and prefixes a multi-file Python project into a single script,
    ordering symbols by their dependencies rather than grouping by file.
    """
    console = Console()
    try:
        ast.unparse
    except AttributeError:
        print("Error: This script requires Python 3.9 or newer.")
        return

    main_file_abs = os.path.abspath(main_file)
    project_dir = os.path.dirname(main_file_abs)

    # Analyze the project
    if verbose:
        print(f"DEBUG: Starting analysis of project at {project_dir}")
    local_module_map = _get_local_module_map(project_dir, verbose)
    analysis_result = _analyze_project(main_file_abs, local_module_map, verbose)
    (
        symbol_deps,
        declared_symbols,
        symbol_origins,
        external_imports,
        scanned_files,
        symbol_to_file,
    ) = analysis_result

    if verbose:
        print("DEBUG: Found symbols:")
        for file_path, symbols in declared_symbols.items():
            rel_path = os.path.relpath(file_path, project_dir)
            print(f"  {rel_path}: {symbols}")

        print("DEBUG: Symbol origins:")
        for file_path, origins in symbol_origins.items():
            rel_path = os.path.relpath(file_path, project_dir)
            print(f"  {rel_path}: {origins}")

        print("DEBUG: Symbol dependencies:")
        for symbol, deps in symbol_deps.items():
            print(f"  {symbol} depends on: {deps}")

    # Create global rename map
    if verbose:
        print("DEBUG: Creating global rename map...")
    global_rename_map = defaultdict(dict)
    for file_path, symbols in declared_symbols.items():
        relative_path = os.path.relpath(file_path, project_dir)
        if file_path == main_file_abs:
            continue
        file_hash = hashlib.md5(relative_path.encode()).hexdigest()[:8]
        prefix = f"mod_{file_hash}"
        for symbol in symbols:
            new_name = f"{prefix}_{symbol}"
            global_rename_map[file_path][symbol] = new_name

    # Sort symbols topologically
    if verbose:
        print("DEBUG: Sorting symbols topologically...")
    sorted_symbols = _topological_sort_symbols(symbol_deps, symbol_to_file)
    if verbose:
        print(
            f"DEBUG: Sorted symbol order: {[s.split('::')[-1] for s in sorted_symbols]}"
        )

    # Extract and transform symbols
    if verbose:
        print("DEBUG: Extracting and transforming symbols...")

    symbol_code = {}
    file_trees = {}

    # Parse all files and extract their ASTs
    for file_path in scanned_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            file_trees[file_path] = ast.parse(content, filename=file_path)
        except Exception as e:
            if verbose:
                print(f"DEBUG: Error parsing {file_path}: {e}")
            continue

    # Extract individual symbols
    for file_path, tree in file_trees.items():
        transformer = Prefixer(
            file_path, global_rename_map, symbol_origins, declared_symbols
        )

        for i, node in enumerate(tree.body):
            symbol_key = None
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                symbol_key = f"{file_path}::{node.name}"
            elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
                for target in targets:
                    if isinstance(target, ast.Name):
                        symbol_key = f"{file_path}::{target.id}"
                        break
            elif file_path == main_file_abs and isinstance(node, ast.Expr):
                # Handle top-level expressions only in the main entry file
                expr_name = f"__expr_{i}"
                symbol_key = f"{file_path}::{expr_name}"

            if symbol_key:
                # Transform the node
                transformed_node = transformer.visit(node)
                ast.fix_missing_locations(transformed_node)
                symbol_code[symbol_key] = ast.unparse(transformed_node)

    # Write the final script
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(
            "# This script was generated by combining and prefixing multiple files.\n\n"
        )
        f.write("# --- Combined External Imports ---\n")
        if external_imports:
            for imp in sorted(list(external_imports)):
                f.write(f"{imp}\n")
        else:
            f.write("# No external imports found.\n")
        f.write("\n")

        # Write symbols in dependency order
        written_symbols = set()
        for symbol in sorted_symbols:
            if symbol in symbol_code and symbol not in written_symbols:
                f.write(f"{symbol_code[symbol]}\n")
                written_symbols.add(symbol)
                if verbose:
                    file_path = symbol_to_file[symbol]
                    symbol_name = symbol.split("::")[-1]
                    print(
                        f"DEBUG: Wrote {symbol_name} from {os.path.basename(file_path)}"
                    )

        f.write("\n# --- End of combined script ---")

    console.print(
        f"✅ [green]Project combined successfully into[/green] [bold cyan]{output_file}[/bold cyan]"
    )
