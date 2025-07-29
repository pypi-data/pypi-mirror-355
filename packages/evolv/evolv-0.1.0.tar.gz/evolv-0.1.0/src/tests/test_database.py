import itertools
from unittest.mock import Mock, patch

# import unittest # No longer needed
# from unittest import mock as umock # Using from unittest.mock import ... is cleaner
import pytest

from evolve.database import LinearSamplingStrategy, Program, ProgramDatabase, RandomSamplingStrategy, SamplingStrategy


# --- Pytest Fixtures --- (Existing fixtures remain unchanged)
@pytest.fixture(autouse=True)
def reset_program_id_counter():
    """Ensures Program.id starts from 1 for each test."""
    Program._id_counter = itertools.count(1)


@pytest.fixture
def program_factory():
    _factory_default_code_counter = itertools.count(1000)

    def _factory(**kwargs):
        if "program_code" not in kwargs:
            kwargs["program_code"] = f"default_prog_{next(_factory_default_code_counter)}"
        kwargs.setdefault("evolve_code", f"evolve_for_{kwargs['program_code']}")
        kwargs.setdefault("success", True)
        return Program(**kwargs)

    return _factory


@pytest.fixture
def p1(program_factory):
    return program_factory(program_code="code1", evolve_code="evolve1", metrics={"fitness": 10.0})


@pytest.fixture
def p2(program_factory):
    return program_factory(program_code="code2", evolve_code="evolve2", metrics={"fitness": 20.0})


@pytest.fixture
def p3(program_factory):
    return program_factory(program_code="code3", evolve_code="evolve3", metrics={"fitness": 5.0})


@pytest.fixture
def sample_programs_dict(p1, p2, p3):
    return {p.id: p for p in [p1, p2, p3]}


# --- Pytest-style tests for Program ---


def test_program_initialization_default_values():
    """Tests Program initialization with default values."""
    # reset_program_id_counter fixture handles ID counter reset
    p = Program("print('h')", "# e")
    assert p.success is None
    assert p.stdout == ""
    assert p.stderr == ""
    assert p.metrics == {}
    assert p.parent_id is None
    assert p.id == "1"

    p2 = Program("print('w')", "# e2")
    assert p2.id == "2"


def test_program_initialization_all_values_specified():
    """Tests Program initialization with all values specified."""
    # reset_program_id_counter fixture handles ID counter reset
    Program("d1", "e1")  # Consumes ID "1"
    Program("d2", "e2")  # Consumes ID "2"
    p = Program("p", "i", success=True, stdout="o", stderr="e", metrics={"fitness": 0.95}, parent_id="p0")
    assert p.id == "3"
    assert p.success is True  # Or just `assert p.success`
    assert p.metrics == {"fitness": 0.95}


def test_program_str_method():
    """Tests the __str__ method of the Program class."""
    # reset_program_id_counter fixture handles ID counter reset
    p = Program("a=1", "M", success=True, stdout="3", metrics={"fitness": 0.8}, parent_id="p1")
    # ID will be "1" due to reset_program_id_counter
    assert "ID: 1" in str(p)
    assert "M" in str(p)
    assert "Metrics: {'fitness': 0.8}" in str(p)  # Check more details


# --- Pytest-style tests for ProgramDatabase ---


def test_programdatabase_initialization():
    """Tests ProgramDatabase initialization."""
    mstrat = Mock(spec=SamplingStrategy)
    db = ProgramDatabase(mstrat)
    assert db.programs == {}
    assert db.best_program_id is None


def test_programdatabase_add_successful_program(program_factory):
    """Tests adding a successful program to the database."""
    mstrat = Mock(spec=SamplingStrategy)
    db = ProgramDatabase(mstrat)
    # program_factory already uses reset_program_id_counter implicitly for ID generation
    p = program_factory(program_code="p1", evolve_code="e1", success=True, metrics={"fitness": 10})

    db.add(p)

    assert p.id in db.programs
    mstrat.add.assert_called_once_with(p)
    assert db.best_program_id == p.id


def test_programdatabase_add_unsuccessful_program(program_factory):
    """Tests that an unsuccessful program is not added to active programs."""
    mstrat = Mock(spec=SamplingStrategy)
    db = ProgramDatabase(mstrat)
    p = program_factory(program_code="pf", evolve_code="ef", success=False)

    db.add(p)

    assert p.id not in db.programs  # Should not be in the main dict of active programs
    mstrat.add.assert_not_called()  # Sampling strategy should not be notified


@patch("evolve.config.get_config")
def test_programdatabase_get_best_program_logic(mock_get_config, program_factory):
    """Tests the logic for getting the best program."""
    mock_config = Mock()
    mock_config.primary_metric = "fitness"
    mock_get_config.return_value = mock_config

    mstrat = Mock(spec=SamplingStrategy)
    db = ProgramDatabase(mstrat)

    p1 = program_factory(metrics={"fitness": 10}, success=True)  # ID 1
    db.add(p1)
    p2 = program_factory(metrics={"fitness": 5}, success=True)  # ID 2, worse
    db.add(p2)
    p3 = program_factory(metrics={"fitness": 20}, success=True)  # ID 3, best
    db.add(p3)

    assert db.get_best_program() == p3


@patch("evolve.config.get_config")
def test_programdatabase_get_best_program_different_primary_metric(mock_get_config, program_factory):
    """Tests getting the best program with a different primary metric."""
    mock_config = Mock()
    mock_config.primary_metric = "size"
    mock_get_config.return_value = mock_config

    mstrat = Mock(spec=SamplingStrategy)
    db = ProgramDatabase(mstrat)

    # program_factory ensures IDs are unique and reset for the test
    p1 = program_factory(metrics={"size": 50, "fitness": 5}, success=True)
    db.add(p1)
    p2 = program_factory(metrics={"size": 30, "fitness": 10}, success=True)  # Lower size, but higher fitness
    db.add(p2)
    p3 = program_factory(metrics={"size": 60, "fitness": 2}, success=True)  # Highest size
    db.add(p3)

    assert db.get_best_program() == p3  # p3 has the highest 'size'


def test_programdatabase_sample_method_empty_database():
    """Tests that sampling from an empty database raises ValueError."""
    mstrat = Mock(spec=SamplingStrategy)
    db = ProgramDatabase(mstrat)
    with pytest.raises(ValueError, match="Cannot sample from empty database."):
        db.sample()


# --- Pytest-style tests for Sampling Strategies --- (These were already pytest-style)
# (No changes needed for the existing sampling strategy tests)


def test_random_select_parent_returns_valid_program(sample_programs_dict):
    strategy = RandomSamplingStrategy()
    if not sample_programs_dict:
        pytest.skip("sample_programs_dict is empty")
    parent = strategy.select_parent(sample_programs_dict)
    assert parent.id in sample_programs_dict


def test_random_select_parent_empty_raises_error():
    strategy = RandomSamplingStrategy()
    with pytest.raises(ValueError, match="No programs available for sampling."):
        strategy.select_parent({})


def test_random_select_inspirations_returns_valid_programs(sample_programs_dict, p1):
    strategy = RandomSamplingStrategy()
    parent_program = p1
    num_inspirations = 1
    candidates = {k: v for k, v in sample_programs_dict.items() if v.id != parent_program.id}
    if not candidates:  # pragma: no cover
        inspirations = strategy.select_inspirations(sample_programs_dict, parent_program, num_inspirations)
        assert len(inspirations) == 0
        return
    inspirations = strategy.select_inspirations(sample_programs_dict, parent_program, num_inspirations)
    assert len(inspirations) <= num_inspirations
    assert len(inspirations) > 0
    for program in inspirations:
        assert program.id != parent_program.id
        assert program.id in sample_programs_dict
    assert inspirations[0] in candidates.values()


def test_linear_select_parent_returns_highest_id(p1, p2, p3):
    strategy = LinearSamplingStrategy()
    programs = {p1.id: p1, p2.id: p2, p3.id: p3}
    parent = strategy.select_parent(programs)
    assert parent == p3


def test_linear_select_parent_empty_raises_error():
    strategy = LinearSamplingStrategy()
    with pytest.raises(ValueError, match="No programs available for sampling."):
        strategy.select_parent({})


def test_linear_select_inspirations_returns_valid_programs(sample_programs_dict, p2):
    strategy = LinearSamplingStrategy()
    parent_program = p2
    num_inspirations = 1
    candidates = {k: v for k, v in sample_programs_dict.items() if v.id != parent_program.id}
    if not candidates:  # pragma: no cover
        inspirations = strategy.select_inspirations(sample_programs_dict, parent_program, num_inspirations)
        assert len(inspirations) == 0
        return
    inspirations = strategy.select_inspirations(sample_programs_dict, parent_program, num_inspirations)
    assert len(inspirations) <= num_inspirations
    assert len(inspirations) > 0
    for program in inspirations:
        assert program.id != parent_program.id
        assert program.id in sample_programs_dict
    assert inspirations[0] in candidates.values()


# Final check for unused imports: 'unittest' and 'unittest.mock.mock' are removed or aliased.
# 'random' is used by RandomSamplingStrategy tests (implicitly, if strategy uses it).
# 'os' is used by @patch.dict(os.environ, ...).
# 'itertools' is used by fixtures.
# 'pytest', 'Mock', 'patch' are used.
# All evolve.database imports are used.
