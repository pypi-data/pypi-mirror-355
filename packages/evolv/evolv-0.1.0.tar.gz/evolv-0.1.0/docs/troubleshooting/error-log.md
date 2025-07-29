# Evolv Error Log

This document tracks errors encountered during development and their solutions.

## Error: Over-Engineering Prompt Strategies
**Date**: 2024-06-10
**Context**: Implementing enhanced LLM prompting
**What Happened**: Created complex BasePromptStrategy, ContextualPromptStrategy classes
**Root Cause**: Assumed DSPy needed string inputs without testing
**Solution**: Discovered DSPy accepts Pydantic models directly
**Prevention**: Always test library capabilities before building abstractions
**Code Reference**: See commit 93a8d54 for the simplified implementation

## Error: CI Formatting Failures
**Date**: 2024-06-10
**Context**: PR #38 CI failures
**What Happened**: Pre-commit passed locally but CI failed on ruff formatting
**Root Cause**: Slight differences in ruff behavior between environments
**Solution**: Run `ruff format` explicitly before pushing
**Prevention**: Add `make format` command that runs all formatters

## Error: Floating Point Test Failures
**Date**: 2024-06-10
**Context**: test_inspiration_prompting.py
**What Happened**: `assert scores[0] == 0.9` failed with 0.8999999999999999
**Root Cause**: Floating point precision issues
**Solution**: Use approximate comparisons: `assert abs(scores[0] - 0.9) < 0.0001`
**Prevention**: Always use approximate comparisons for floats in tests

## Template for New Errors
## Error: [Title]
**Date**: YYYY-MM-DD
**Context**: Where/when this occurred
**What Happened**: Description of the error
**Root Cause**: Why it happened
**Solution**: How it was fixed
**Prevention**: How to avoid in the future
**Code Reference**: Link to fix commit or PR
