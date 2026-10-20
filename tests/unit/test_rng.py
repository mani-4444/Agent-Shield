import random
import unicodedata

import numpy as np
import pytest

from injbench.rng import make_rng


def draws(seed: int, *keys: str | int) -> list[int]:
    return make_rng(seed, *keys).integers(0, 1_000_000, size=8).tolist()


def test_same_inputs_same_stream() -> None:
    assert draws(2026, "attack", "doc-001") == draws(2026, "attack", "doc-001")


def test_returns_numpy_generator() -> None:
    assert isinstance(make_rng(2026), np.random.Generator)


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ((2026, "doc-001"), (2027, "doc-001")),  # seed
        ((2026, "doc-001"), (2026, "doc-002")),  # key
        ((2026, "a", "b"), (2026, "b", "a")),  # key order
        ((2026, "a", "b"), (2026, "a|b")),  # no separator collisions
        ((2026, 1), (2026, "1")),  # int vs str
        ((2026,), (2026, "x")),  # extra key
    ],
)
def test_different_inputs_different_streams(a: tuple[int, ...], b: tuple[int, ...]) -> None:
    assert draws(*a) != draws(*b)


def test_nfc_equivalent_keys_share_a_stream() -> None:
    composed = "తెలుగు"
    decomposed = unicodedata.normalize("NFD", composed)
    accented = unicodedata.normalize("NFD", "café")
    assert draws(2026, composed) == draws(2026, decomposed)
    assert draws(2026, "café") == draws(2026, accented)


def test_independent_of_call_order() -> None:
    first = draws(2026, "x")
    make_rng(2026, "y").random(100)
    assert draws(2026, "x") == first


def test_does_not_touch_global_rng_state() -> None:
    np_state = np.random.get_state()[1].copy()  # type: ignore[index]
    py_state = random.getstate()
    make_rng(2026, "x").random(10)
    assert (np.random.get_state()[1] == np_state).all()  # type: ignore[index]
    assert random.getstate() == py_state


@pytest.mark.parametrize("bad", [1.5, True, None, b"x"])
def test_rejects_non_str_int_keys(bad: object) -> None:
    with pytest.raises(TypeError):
        make_rng(2026, bad)  # type: ignore[arg-type]
