"""Tests for coordinator decorator behavior."""

import os
from unittest.mock import mock_open, patch

from evolve import default_coordinator, evolve


def test_evolve_decorator_overwrites_previous():
    """Test that applying @evolve multiple times properly overwrites."""
    test_file_path = os.path.abspath(__file__)

    # First decoration
    with (
        patch("inspect.getsourcefile", return_value=test_file_path),
        patch("builtins.open", mock_open(read_data="def first_func(a): return a")),
        patch("inspect.getsource", return_value="def first_func(a): return a"),
    ):

        @evolve(goal="First goal")
        def first_func(a):
            return a

    first_target = default_coordinator.target
    assert first_target is not None
    assert first_target.name == "first_func"
    assert first_target.goal == "First goal"

    # Second decoration should overwrite
    with (
        patch("inspect.getsourcefile", return_value=test_file_path),
        patch("builtins.open", mock_open(read_data="def second_func(b): return b")),
        patch("inspect.getsource", return_value="def second_func(b): return b"),
    ):

        @evolve(goal="Second goal")
        def second_func(b):
            return b

    second_target = default_coordinator.target
    assert second_target is not None
    assert second_target.name == "second_func"
    assert second_target.goal == "Second goal"

    # Verify first was overwritten
    assert default_coordinator.target.name != "first_func"
