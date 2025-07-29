# 🚀 Super Agentic Mode: Maximizing Claude Code Efficiency

## Core Principle: Clear Targets + Automated Verification = Maximum Autonomy

This guide shows how to use Claude Code at peak efficiency by providing clear objectives and letting automated systems guide the work.

## 🎯 The Super Agentic Formula

```
1. Define Clear Success Criteria (Tests/Metrics)
2. Provide Context & Constraints
3. Enable Parallel Workflows
4. Let Claude Code Iterate Autonomously
5. Review Final Results
```

## 📋 Task Templates for Maximum Autonomy

### 1. Feature Implementation (Most Agentic)
```
"Implement issue #X. The tests should pass and e2e should work. Use TDD."

Why this works:
- Clear target: passing tests
- Defined workflow: TDD
- Measurable success: e2e tests
- Claude can iterate independently
```

### 2. Performance Optimization
```
"Make the async evolution 2x faster. Current baseline: X seconds for 10 iterations."

Why this works:
- Quantifiable goal: 2x faster
- Clear baseline for comparison
- Claude can try multiple approaches
- Success is measurable
```

### 3. Bug Investigation & Fix
```
"Fix the failing test in test_coordinator.py. It should pass in CI."

Why this works:
- Specific failure to fix
- Clear success state: passing CI
- Claude can debug autonomously
- Verification is automated
```

### 4. Refactoring with Constraints
```
"Refactor the database module to use async/await. All existing tests must still pass."

Why this works:
- Clear transformation goal
- Safety constraint: tests must pass
- Claude can work incrementally
- Progress is verifiable
```

## 🔄 Optimal Workflows by Task Type

### New Feature Development
```bash
# User provides:
"Implement MAP-Elites strategy from issue #2. Follow TDD. Make sure all tests pass."

# Claude Code will:
1. Read issue specification
2. Search for similar code patterns
3. Write failing tests first
4. Implement incrementally
5. Run make pr-ready
6. Iterate until all checks pass
```

### Complex Investigation
```bash
# User provides:
"Find why evolution is slower with 10+ variants. Profile and optimize."

# Claude Code will:
1. Set up profiling
2. Run benchmarks
3. Analyze bottlenecks
4. Try optimizations
5. Measure improvements
6. Document findings
```

### Multi-File Refactoring
```bash
# User provides:
"Update all strategies to support new metrics format. Tests should guide you."

# Claude Code will:
1. Find all strategy files
2. Understand current format
3. Write tests for new format
4. Update each file
5. Verify nothing breaks
6. Run integration tests
```

## 🎮 Power User Commands

### 1. The "Fire and Forget" Pattern
```
"Implement all issues labeled 'good first issue'. Run tests after each. Stop if any fail."
```

### 2. The "Exploration" Pattern
```
"Find the slowest part of the codebase and make it 50% faster. Show benchmarks."
```

### 3. The "Quality Sweep" Pattern
```
"Add comprehensive tests for any module with <80% coverage. Follow existing patterns."
```

### 4. The "Documentation Generation" Pattern
```
"Create visual diagrams for all major workflows. Save as PNG in docs/diagrams/."
```

## 🛠️ Environmental Setup for Maximum Agenticity

### Terminal Setup (for user)
```bash
# Terminal 1: Let Claude Code work
# Terminal 2: Watch tests
watch -n 2 'uv run pytest -x'

# Terminal 3: Watch linting
watch -n 2 'uv run ruff check .'

# Terminal 4: Monitor changes
watch -n 1 'git status'
```

### Automated Feedback Loops
```bash
# Create a feedback script
cat > watch_progress.sh << 'EOF'
#!/bin/bash
while true; do
    clear
    echo "=== Test Status ==="
    uv run pytest --tb=no | tail -20
    echo -e "\n=== Lint Status ==="
    uv run ruff check . | tail -10
    echo -e "\n=== Git Status ==="
    git status --short
    sleep 3
done
EOF
chmod +x watch_progress.sh
```

## 📊 Success Metrics for Agentic Tasks

Good agentic tasks have:
- ✅ **Binary success criteria** (passes/fails, faster/slower)
- ✅ **Automated verification** (tests, benchmarks, linting)
- ✅ **Clear boundaries** (specific files/modules)
- ✅ **Incremental progress** (can be done in steps)

Poor agentic tasks:
- ❌ "Make the code better" (too vague)
- ❌ "Design a new architecture" (needs discussion)
- ❌ "Fix all the bugs" (unbounded scope)
- ❌ "Make it pretty" (subjective)

## 🎯 The Ultimate Agentic Commands

### Level 1: Guided Autonomy
```
"Fix issue #X. Tests will guide you."
```

### Level 2: Goal-Based Autonomy
```
"Make evolution 3x faster while keeping accuracy above 90%."
```

### Level 3: Discovery Autonomy
```
"Find and fix the three biggest performance bottlenecks. Show before/after metrics."
```

### Level 4: Creative Autonomy
```
"Add a useful feature that improves developer experience. Write tests to prove it works."
```

## 🚦 When to Intervene

Let Claude Code work autonomously UNTIL:
- Tests are failing after multiple attempts
- The approach seems fundamentally wrong
- You want to change requirements
- Claude asks for clarification

## 💡 Pro Tips

1. **Start with tests**: "Write tests for X, then implement it"
2. **Use metrics**: "Improve Y metric by Z%"
3. **Leverage CI**: "Make sure CI passes"
4. **Trust the process**: Let Claude iterate and learn
5. **Batch similar tasks**: "Fix all typing issues in src/"

## 🎪 Example: Full Agentic Session

```bash
# User:
"I need the island evolution strategy from issue #3 implemented.
Use TDD, make it faster than linear strategy, and ensure 95% test coverage.
The e2e test should show it finding better solutions."

# What happens:
1. Claude reads issue #3 specification
2. Studies existing strategies for patterns
3. Writes comprehensive tests first
4. Implements incrementally
5. Runs benchmarks against linear strategy
6. Adjusts for performance
7. Ensures test coverage meets target
8. Runs e2e to verify quality
9. Iterates until all criteria are met
10. Presents final results with metrics

# User reviews:
- Check test coverage: ✅ 96%
- Check performance: ✅ 1.5x faster
- Check e2e results: ✅ Better solutions
- Check code quality: ✅ Follows patterns
```

## 🎁 The Magic Words

For maximum agenticity, use these patterns:

- "**Tests will guide you**" - Enables TDD autonomy
- "**CI should pass**" - Clear success criteria
- "**Benchmark before and after**" - Measurable progress
- "**Follow existing patterns**" - Reduces decision fatigue
- "**Stop if tests fail repeatedly**" - Automatic circuit breaker

## 🎩 Advanced Features

### Thinking Modes for Complex Tasks
```bash
/think         # Basic analysis
/think hard    # Deeper exploration
/think harder  # Complex problem solving
/ultrathink    # Maximum depth for architecture/design
```

### Custom Commands (in .claude/commands/)
```bash
/test-focused async      # Run focused tests with coverage
/evolve-demo 5 tournament # Quick evolution demo
/benchmark-quick async   # Fast performance check
```

### Parallel Development
```bash
# Use git worktrees for multiple features
git worktree add ../evolve-fix-async fix/async-bug
# Run separate Claude sessions in each directory
```

### MCP Integration
```bash
# GitHub automation via MCP
"Find all performance issues and create a meta-issue to track them"
"Create PR from current changes with comprehensive description"
```

See [HIDDEN_FEATURES.md](docs/HIDDEN_FEATURES.md) for more advanced capabilities.

## Remember

The key to super agentic mode is **trusting the process**. Give clear goals, enable verification loops, and let Claude Code iterate towards success. The more specific your success criteria, the more autonomously Claude can work.

**Your role**: Set destination and constraints
**Claude's role**: Find the optimal path
**Tests' role**: Ensure safe arrival
