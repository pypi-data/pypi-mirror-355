"""Test addition module."""

from space_collector.game.add import add


def test_add() -> None:
    result = add(5, 5)

    assert result == 10
