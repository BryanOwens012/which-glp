"""
Print, as a JSON list, every way a Python service's routes break the INTERNAL_API_KEY rule.

Used by check.ts. Every route a FastAPI app serves, except GET /health, must take
`Depends(verify_internal_api_key)` as a parameter default, so a new endpoint cannot
ship open. Static (ast), so comments, strings and docstrings never count as a
dependency. Fails closed: a route it cannot verify (a non-literal path, a decorator
inside a function, routes added by `add_api_route` or `include_router`, an
`APIRouter`) is a problem, and so is a file with no routes at all. An empty list
means the file passes. Usage: python3 python-route-guards.py <entry.py>
"""
import ast
import json
import sys

ROUTE_METHODS = {
    "get", "post", "put", "patch", "delete", "head", "options", "trace",
    "api_route", "route", "websocket", "websocket_route",
    "add_api_route", "add_route", "add_websocket_route", "add_api_websocket_route",
    "include_router", "mount",
}
DECORATOR_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}
PUBLIC_ROUTES = {("GET", "/health")}
VERIFIER = "verify_internal_api_key"


def find_problems(source: str) -> list[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return [f"does not parse: {error}"]

    app_names = {
        target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "FastAPI"
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    problems = []
    if any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "APIRouter"
        for node in ast.walk(tree)
    ):
        problems.append("creates an APIRouter, whose routes this check cannot verify")

    def is_route_call(node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in app_names
            and node.func.attr in ROUTE_METHODS
        )

    verified = set()
    routes = 0
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not is_route_call(decorator):
                continue
            verified.add(id(decorator))
            routes += 1
            method = decorator.func.attr
            first = decorator.args[0] if decorator.args else None
            if method not in DECORATOR_METHODS:
                problems.append(f"route on {node.name} uses @{decorator.func.value.id}.{method}, which this check cannot verify")
                continue
            if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
                problems.append(f"route on {node.name} has no literal path")
                continue
            if (method.upper(), first.value) in PUBLIC_ROUTES:
                continue
            defaults = [*node.args.defaults, *node.args.kw_defaults]
            if not any(
                isinstance(default, ast.Call)
                and isinstance(default.func, ast.Name)
                and default.func.id == "Depends"
                and len(default.args) == 1
                and isinstance(default.args[0], ast.Name)
                and default.args[0].id == VERIFIER
                for default in defaults
            ):
                problems.append(f"route {method.upper()} {first.value} must take `_: None = Depends({VERIFIER})`")

    for node in ast.walk(tree):
        if is_route_call(node) and id(node) not in verified:
            problems.append(
                f"registers a route with {node.func.value.id}.{node.func.attr}(...) outside a module-level decorator, "
                "which this check cannot verify"
            )
    if not app_names:
        problems.append("defines no FastAPI app")
    elif routes == 0:
        problems.append("has no routes to check")
    return problems


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as handle:
        print(json.dumps(find_problems(handle.read())))
