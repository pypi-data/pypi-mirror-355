# Feature Implementation Workflow Template

## 1. Understanding Phase
```bash
# Read the issue
gh issue view {ISSUE_NUMBER}

# Read detailed specification
cat .github/issues/{ISSUE_NUMBER}_*.md

# Search for related code
python scripts/claude_tasks.py find_usage "{RELATED_CLASS}"
rg "{FEATURE_KEYWORD}" --type py
```

## 2. Test Writing Phase
```python
# src/tests/test_{feature_name}.py

import pytest
from evolve.{module} import {Class}


class Test{FeatureName}:
    """Test cases for {feature description}."""

    def test_{feature}_basic(self):
        """Test basic {feature} functionality."""
        # Arrange
        input_data = {...}
        expected = {...}

        # Act
        result = function_under_test(input_data)

        # Assert
        assert result == expected

    def test_{feature}_edge_case(self):
        """Test {feature} handles edge cases."""
        # Test empty input
        assert function_under_test([]) == []

        # Test None input
        with pytest.raises(ValueError):
            function_under_test(None)

    @pytest.mark.asyncio
    async def test_{feature}_async(self):
        """Test async version of {feature}."""
        result = await async_function(...)
        assert result == expected
```

## 3. Implementation Phase
```python
# src/evolve/{module}.py

from typing import Optional, List, Dict, Any


def new_feature(input_data: List[Any]) -> Dict[str, Any]:
    """
    Brief description of what this does.

    Args:
        input_data: Description of input

    Returns:
        Description of output

    Raises:
        ValueError: When input is invalid
    """
    if input_data is None:
        raise ValueError("Input cannot be None")

    # Implementation
    result = {}

    return result


async def new_feature_async(input_data: List[Any]) -> Dict[str, Any]:
    """Async version of new_feature."""
    # Async implementation
    return await process_async(input_data)
```

## 4. Integration Phase
```python
# Update existing code to use new feature

# Before
result = old_method(data)

# After
if use_new_feature:
    result = new_feature(data)
else:
    result = old_method(data)
```

## 5. Verification Phase
```bash
# Run specific tests
uv run pytest -xvs src/tests/test_{feature_name}.py

# Run related tests
python scripts/claude_tasks.py test_pattern "{feature}"

# Run all checks
make pr-ready

# Test end-to-end
./scripts/test_e2e.py --scenario {relevant_scenario}
```

## 6. Documentation Phase
```markdown
# Update relevant documentation

1. Add docstrings to all new functions/classes
2. Update README.md if adding user-facing features
3. Add to CLAUDE.md if adding development tools
4. Create ADR if making architectural decisions
5. Update error-log.md with any issues encountered
```

## 7. Commit Phase
```bash
# Stage changes
git add -p  # Review each change

# Commit with descriptive message
git commit -m "feat: Implement {feature} for {purpose}

- Add {specific change 1}
- Update {specific change 2}
- Test coverage at {X}%

Closes #{ISSUE_NUMBER}"
```
