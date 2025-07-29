# Evolv Development Patterns

## ✅ Patterns (What Works)

### 1. Async-First Design
```python
# Good: Async from the ground up
async def suggest_improvement_async(self, parent: Program, ...) -> str:
    result = await self.async_predictor(...)
    return result.improvement

# Bad: Sync wrapper around async
def suggest_improvement(self, parent: Program, ...) -> str:
    return asyncio.run(self.suggest_improvement_async(parent, ...))
```

### 2. Explicit Type Hints with Pydantic
```python
# Good: Clear types with validation
class ProgramInfo(BaseModel):
    code: str = Field(description="The program code")
    metrics: Dict[str, float] = Field(description="Performance metrics")

# Bad: Dict typing without validation
def process_program(program: dict) -> dict:
    return {"code": program["code"], "metrics": program["metrics"]}
```

### 3. Early Validation
```python
# Good: Validate at entry points
@evolve(goal="Improve accuracy", iterations=3)
def my_function():
    # Validation happens in decorator
    pass

# Bad: Late validation
def evolve_function(func, goal=None, iterations=None):
    # ... lots of code ...
    if not goal:
        raise ValueError("Goal is required")
```

## ❌ Anti-Patterns (What to Avoid)

### 1. Over-Engineering Before Testing
**Problem**: Creating abstractions before understanding the problem
**Example**: Complex prompt strategies when DSPy handles Pydantic natively
**Solution**: Start simple, test capabilities, then abstract if needed

### 2. Floating Point Comparisons
```python
# Bad: Direct equality
assert score == 0.9

# Good: Approximate comparison
assert abs(score - 0.9) < 0.0001
```

### 3. Ignoring Async Context Managers
```python
# Bad: Manual cleanup
llm_module = AsyncDSPyModule(config)
try:
    result = await llm_module.suggest_improvement_async(...)
finally:
    await llm_module.cleanup()

# Good: Context manager
async with AsyncDSPyModule(config) as llm_module:
    result = await llm_module.suggest_improvement_async(...)
```

## 🔍 Common Debugging Scenarios

### 1. Import Errors in CI but not Local
**Symptom**: Tests pass locally but fail in CI with import errors
**Common Cause**: Missing `__init__.py` or incorrect PYTHONPATH
**Debug Steps**:
1. Check all directories have `__init__.py`
2. Verify import paths are relative
3. Test with `python -m pytest` instead of `pytest`

### 2. Async Test Failures
**Symptom**: "RuntimeError: This event loop is already running"
**Common Cause**: Missing `@pytest.mark.asyncio` or incorrect event loop handling
**Solution**: Always use pytest-asyncio markers and fixtures

### 3. Pre-commit vs CI Formatting
**Symptom**: Pre-commit passes but CI fails on formatting
**Common Cause**: Different tool versions or configurations
**Solution**: Pin tool versions in both environments

## 📋 Checklist for New Features

- [ ] Write ADR for significant design decisions
- [ ] Add comprehensive docstrings with examples
- [ ] Include "Why" comments for non-obvious code
- [ ] Create integration test showing real usage
- [ ] Update CLAUDE.md with new patterns
- [ ] Add error scenarios to test suite
