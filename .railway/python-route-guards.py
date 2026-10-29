"""
Print, as a JSON list, every way a Python service breaks the INTERNAL_API_KEY route rule.

Used by check.ts; `find_problems` is its API (the tests load this file by path). Each
service serves `uvicorn api:app`, so the rule pins that one object and allows only
uses of it that this scan can verify:

- `app` is bound exactly once, at module level, by `app = FastAPI(...)`, and no other
  FastAPI app is built;
- every use of `app` is a module-level route decorator `@app.<verb>("<literal path>")`
  or one of ALLOWED_APP_ATTRIBUTES (middleware and lifecycle hooks). Anything else
  (`app.router`, `app.dependency_overrides`, `app.mount`, an alias, `getattr(app, ...)`)
  is a problem;
- every route but GET /health takes `Depends(verify_internal_api_key)` as a parameter
  default, and `verify_internal_api_key` is bound exactly once, by an assignment.

Static (ast), so comments, strings and docstrings never count. A file with no routes
is a problem too. An empty list means the file passes.
Usage: python3 python-route-guards.py <entry.py>
"""
import ast
import json
import sys

APP = "app"
VERIFIER = "verify_internal_api_key"
DECORATOR_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}
ALLOWED_APP_ATTRIBUTES = {"add_middleware", "on_event", "exception_handler", "middleware"}
PUBLIC_ROUTES = {("GET", "/health")}


def is_fastapi_constructor(node: ast.AST, aliases: set) -> bool:
    """Whether `node` builds a FastAPI app: `FastAPI(...)`, an alias of it, or `<module>.FastAPI(...)`."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (isinstance(func, ast.Name) and func.id in aliases) or (
        isinstance(func, ast.Attribute) and func.attr == "FastAPI"
    )


def find_app_problems(tree: ast.Module) -> list:
    """`app` must be bound once, at module level, by `app = FastAPI(...)`; no other app may exist."""
    aliases = {"FastAPI"} | {
        alias.asname
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
        if alias.name == "FastAPI" and alias.asname
    }
    problems = []
    plain = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == APP
        and is_fastapi_constructor(node.value, {"FastAPI"})
    ]
    if len(plain) != 1:
        problems.append(f"must bind `{APP}` exactly once, at module level, with `{APP} = FastAPI(...)`")
    allowed_constructor = plain[0].value if len(plain) == 1 else None
    for node in ast.walk(tree):
        if is_fastapi_constructor(node, aliases) and node is not allowed_constructor:
            problems.append("builds a FastAPI app other than the module-level `app`, which this check cannot verify")
        if isinstance(node, ast.Name) and node.id == APP and isinstance(node.ctx, (ast.Store, ast.Del)):
            if not (plain and node is plain[0].targets[0]):
                problems.append(f"rebinds `{APP}`, which this check cannot verify")
    return problems


def find_verifier_problems(tree: ast.Module) -> list:
    """`verify_internal_api_key` is bound exactly once, by an assignment (the shared verifier line)."""
    bindings = [
        node
        for node in ast.walk(tree)
        if (isinstance(node, ast.Name) and node.id == VERIFIER and isinstance(node.ctx, ast.Store))
        or (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == VERIFIER)
        or (isinstance(node, ast.alias) and (node.asname or node.name) == VERIFIER)
    ]
    if len(bindings) != 1 or not isinstance(bindings[0], ast.Name):
        return [f"must bind `{VERIFIER}` exactly once, by assigning the shared verifier"]
    return []


def is_guarded(handler: ast.AST) -> bool:
    """Whether a route handler takes `Depends(verify_internal_api_key)` as a parameter default."""
    return any(
        isinstance(default, ast.Call)
        and isinstance(default.func, ast.Name)
        and default.func.id == "Depends"
        and len(default.args) == 1
        and isinstance(default.args[0], ast.Name)
        and default.args[0].id == VERIFIER
        for default in [*handler.args.defaults, *handler.args.kw_defaults]
    )


def find_route_problems(tree: ast.Module) -> list:
    """Every use of `app` must be a verified route decorator or an allowed attribute."""
    problems = []
    verified = set()
    routes = 0
    for handler in tree.body:
        if not isinstance(handler, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in handler.decorator_list:
            func = decorator.func if isinstance(decorator, ast.Call) else decorator
            if not (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == APP):
                continue
            if func.attr in ALLOWED_APP_ATTRIBUTES:
                verified.add(id(func.value))
                continue
            if func.attr not in DECORATOR_METHODS or not isinstance(decorator, ast.Call):
                continue
            verified.add(id(func.value))
            routes += 1
            first = decorator.args[0] if decorator.args else None
            if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
                problems.append(f"route on {handler.name} has no literal path")
            elif (func.attr.upper(), first.value) not in PUBLIC_ROUTES and not is_guarded(handler):
                problems.append(f"route {func.attr.upper()} {first.value} must take `_: None = Depends({VERIFIER})`")

    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute) or not isinstance(node.value, ast.Name) or node.value.id != APP:
            continue
        if id(node.value) in verified:
            continue
        if node.attr in ALLOWED_APP_ATTRIBUTES and isinstance(node.ctx, ast.Load):
            verified.add(id(node.value))
            continue
        problems.append(f"uses `{APP}.{node.attr}` outside a module-level route decorator, which this check cannot verify")
        verified.add(id(node.value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == APP and isinstance(node.ctx, ast.Load) and id(node) not in verified:
            problems.append(f"uses `{APP}` directly (an alias, an argument, getattr), which this check cannot verify")
    if routes == 0:
        problems.append("has no routes to check")
    return problems


def find_problems(source: str) -> list:
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return [f"does not parse: {error}"]
    return [*find_app_problems(tree), *find_verifier_problems(tree), *find_route_problems(tree)]


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as handle:
        print(json.dumps(find_problems(handle.read())))
