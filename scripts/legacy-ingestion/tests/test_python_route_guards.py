"""Tests for .railway/python-route-guards.py, the ast check that every Python route is guarded."""

import importlib.util
import pathlib
import textwrap

import pytest

_HELPER = pathlib.Path(__file__).resolve().parents[3] / ".railway" / "python-route-guards.py"
_spec = importlib.util.spec_from_file_location("python_route_guards", _HELPER)
route_guards = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(route_guards)

HEADER = """
from fastapi import Depends, FastAPI
app = FastAPI()
verify_internal_api_key = make_internal_api_key_verifier(require_internal_api_key())

@app.get("/health")
async def health():
    return {}
"""


def problems_for(routes: str) -> list[str]:
    return route_guards.find_problems(HEADER + textwrap.dedent(routes))


GUARDED = """
@app.post("/api/run", response_model=Out)
async def run(
    request: Req,
    _: None = Depends(verify_internal_api_key),
):
    return {}

@app.get('/api/status')
def status(*, _: None = Depends(verify_internal_api_key)):
    return {}
"""


def test_guarded_routes_pass():
    assert problems_for(GUARDED) == []


@pytest.mark.parametrize(
    ("label", "routes", "expected"),
    [
        (
            "no dependency",
            '@app.post("/api/open")\nasync def open_route(payload: dict):\n    return payload\n',
            "route POST /api/open must take",
        ),
        (
            "dependency only in a comment",
            '@app.post("/api/open")\nasync def open_route(x: int = 1,  # Depends(verify_internal_api_key)\n):\n    return x\n',
            "route POST /api/open must take",
        ),
        (
            "dependency only in a string default",
            '@app.post("/api/open")\nasync def open_route(x: str = "Depends(verify_internal_api_key)"):\n    return x\n',
            "route POST /api/open must take",
        ),
        (
            "dependency only in a docstring",
            '@app.post("/api/open")\nasync def open_route():\n    """\ndef fake(_: None = Depends(verify_internal_api_key)):\n    """\n    return {}\n',
            "route POST /api/open must take",
        ),
        (
            "a different dependency",
            '@app.post("/api/open")\nasync def open_route(_: None = Depends(other_check)):\n    return {}\n',
            "route POST /api/open must take",
        ),
        (
            "POST /health",
            '@app.post("/health")\nasync def health_post():\n    return {}\n',
            "route POST /health must take",
        ),
        (
            "a route inside a function",
            'def register():\n    @app.get("/api/inner")\n    async def inner():\n        return {}\n',
            "outside a module-level decorator",
        ),
        (
            "add_api_route",
            'app.add_api_route("/api/added", handler)\n',
            "outside a module-level decorator",
        ),
        (
            "include_router",
            "app.include_router(other)\n",
            "outside a module-level decorator",
        ),
        ("an APIRouter", "router = APIRouter()\n", "creates an APIRouter"),
        ("mount", 'app.mount("/api/sub", sub_app)\n', "outside a module-level decorator"),
        ("add_route", 'app.add_route("/api/added", handler)\n', "outside a module-level decorator"),
        ("a decorator called as a function", 'app.get("/api/leak")(handler)\n', "outside a module-level decorator"),
        (
            "a non-literal path",
            '@app.get(PATH)\nasync def computed(_: None = Depends(verify_internal_api_key)):\n    return {}\n',
            "has no literal path",
        ),
        (
            "api_route",
            '@app.api_route("/api/any", methods=["GET"])\nasync def any_route(_: None = Depends(verify_internal_api_key)):\n    return {}\n',
            "which this check cannot verify",
        ),
    ],
)
def test_every_way_to_ship_an_open_route_is_a_problem(label, routes, expected):
    found = problems_for(routes)
    assert any(expected in problem for problem in found), (label, found)


def test_a_second_app_is_checked_too():
    found = problems_for('api = FastAPI()\n\n@api.get("/api/other")\nasync def other():\n    return {}\n')
    assert any("route GET /api/other must take" in problem for problem in found)


def test_fails_closed_on_no_routes_no_app_or_bad_syntax():
    assert route_guards.find_problems("app = FastAPI()\n") == ["has no routes to check"]
    assert route_guards.find_problems("x = 1\n") == ["defines no FastAPI app"]
    assert route_guards.find_problems("def broken(:\n")[0].startswith("does not parse")
