"""
Print the local files a Python entry point imports, transitively.

Used by check.ts to find the code a Python service actually runs. Static (ast),
so it sees every import statement, including ones inside functions; it resolves
modules relative to the entry point's directory, following symlinks, and ignores
third-party packages. Usage: python3 python-import-closure.py <entry.py>
"""
import ast
import os
import sys

def resolve(module: str, base: str) -> list[str]:
    parts = module.split(".")
    found = []
    for i in range(len(parts), 0, -1):
        stem = os.path.join(base, *parts[:i])
        for cand in (stem + ".py", os.path.join(stem, "__init__.py")):
            if os.path.isfile(cand):
                found.append(cand)
        if found:
            break
    return found

def closure(entry: str) -> list[str]:
    base = os.path.dirname(os.path.abspath(entry))
    seen, stack = set(), [os.path.abspath(entry)]
    while stack:
        path = stack.pop()
        real = os.path.realpath(path)
        if real in seen:
            continue
        seen.add(real)
        tree = ast.parse(open(path, encoding="utf-8").read(), path)
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
            for name in names:
                for f in resolve(name, base):
                    stack.append(f)
                    # Importing a package runs its __init__ too.
                    pkg_init = os.path.join(base, name.split(".")[0], "__init__.py")
                    if os.path.isfile(pkg_init):
                        stack.append(pkg_init)
    return sorted(seen)

for f in closure(sys.argv[1]):
    print(f)
