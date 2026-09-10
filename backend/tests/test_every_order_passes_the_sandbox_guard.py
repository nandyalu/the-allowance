"""The guard that keeps this a simulation, pinned mechanically.

**This is the highest-stakes invariant in the repo and it was held by nothing
but discipline until 2026-09-10.** All six order call sites did call
``_assert_sandbox()`` first. A seventh that forgot would have broken nothing
visible, passed every test, and placed an order against whatever account the
credentials pointed at.

``_assert_sandbox()`` runs immediately before every order rather than once at
import, so that flipping the environment mid-process cannot leave a live
client armed. That only holds if *every* order path does it, which is what
these tests check.

Two ways to bypass it, so there are two tests: write an order function that
skips the call, or reach the order API from a module that has no guard at all.

**Neither test asserts anything about a running system.** They read the source
with ``ast``, so they cannot be satisfied by a mock and cannot be skipped by a
code path that happens not to run in the suite.
"""
import ast
import pathlib

BROKER = pathlib.Path(__file__).resolve().parents[1] / "services" / "sandbox_broker.py"
BACKEND = pathlib.Path(__file__).resolve().parents[1]

# The Webull SDK methods that change something at the broker. `get_order_detail`
# and `preview_order` are reads and are deliberately not here: requiring the
# guard on a read would make the rule look arbitrary, and a rule that looks
# arbitrary is one somebody eventually relaxes.
MUTATING = {"place_order", "replace_order", "cancel_order"}

GUARD = "_assert_sandbox"


def _functions(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _calls_in(node: ast.AST) -> list[ast.Call]:
    """Every call in this function, excluding ones inside nested functions —
    a guard in an outer function does not protect an inner one that is called
    from somewhere else."""
    out: list[ast.Call] = []
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if isinstance(child, ast.Call):
            out.append(child)
        out.extend(_calls_in(child))
    return out


def _mutating_calls(func: ast.AST) -> list[str]:
    names = []
    for call in _calls_in(func):
        if isinstance(call.func, ast.Attribute) and call.func.attr in MUTATING:
            names.append(call.func.attr)
    return names


def _guards(func: ast.AST) -> bool:
    return any(
        isinstance(call.func, ast.Name) and call.func.id == GUARD for call in _calls_in(func)
    )


def test_every_function_that_places_an_order_asserts_the_sandbox_first():
    """The rule, stated where it cannot rot: a function that changes something
    at the broker calls _assert_sandbox() in its own body."""
    tree = ast.parse(BROKER.read_text())

    unguarded = [
        f"{func.name}() calls {', '.join(sorted(set(_mutating_calls(func))))} "
        f"at line {func.lineno} without {GUARD}()"
        for func in _functions(tree)
        if _mutating_calls(func) and not _guards(func)
    ]

    assert not unguarded, (
        "An order path does not assert the sandbox:\n  "
        + "\n  ".join(unguarded)
        + f"\n\nAdd {GUARD}() as the first statement. It is what stands between this "
        "experiment and a machine spending real money, and it is checked before "
        "every order rather than once at import so that flipping the environment "
        "mid-process cannot leave a live client armed. See CLAUDE.md, "
        "'Four guards keep this a simulation'."
    )


def test_the_order_api_is_reachable_from_one_module_only():
    """A guard in sandbox_broker.py protects nothing if another module imports
    the order API directly. Every import of it is lazy and inside that one
    file, which is what makes the guard above sufficient rather than merely
    conventional."""
    offenders = []
    for path in BACKEND.rglob("*.py"):
        if path == BROKER or "tests" in path.parts:
            continue
        text = path.read_text(errors="ignore")
        if "OrderOperationV3" in text or "order_opration_v3" in text:
            offenders.append(str(path.relative_to(BACKEND.parent)))

    assert not offenders, (
        "The Webull order API is imported outside sandbox_broker.py:\n  "
        + "\n  ".join(offenders)
        + "\n\nEvery order goes through sandbox_broker so that one file holds the "
        "guard. A second entry point means a second place to forget it."
    )


def test_the_guard_actually_refuses(monkeypatch):
    """The two tests above are about shape. This one is about behaviour, so a
    refactor that renames the guard into something inert fails here."""
    import pytest

    from backend.services import sandbox_broker

    monkeypatch.setattr(sandbox_broker.quotes, "is_sandbox", lambda: False)
    with pytest.raises(sandbox_broker.NotSandboxError):
        sandbox_broker._assert_sandbox()

    monkeypatch.setattr(sandbox_broker.quotes, "is_sandbox", lambda: True)
    sandbox_broker._assert_sandbox()  # does not raise
