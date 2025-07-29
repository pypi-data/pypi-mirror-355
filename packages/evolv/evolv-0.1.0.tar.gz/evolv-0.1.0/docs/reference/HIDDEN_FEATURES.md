# 🎩 Hidden Claude Code Features for Evolve

This document covers advanced Claude Code features discovered from the best practices guide that can supercharge your development workflow.

## 🧠 Multi-Level Thinking Modes

Claude Code supports different thinking depths for complex problems:

```
/think         - Basic analysis
/think hard    - Deeper analysis
/think harder  - Complex problem solving
/ultrathink    - Maximum computational budget
```

### Usage Examples:

```bash
# For complex refactoring
/think harder
"Refactor the entire async system to use trio instead of asyncio"

# For architectural decisions
/ultrathink
"Design a plugin system for custom evolution strategies"
```

## 🎯 Custom Slash Commands

We've added project-specific commands in `.claude/commands/`:

### `/test-focused <pattern>`
Runs tests matching a pattern with detailed output and coverage
```
/test-focused async
/test-focused test_coordinator
```

### `/evolve-demo [iterations] [strategy] [scenario]`
Quick evolution demo with custom parameters
```
/evolve-demo 5 tournament simple
/evolve-demo 10 map_elites regression
```

### `/benchmark-quick [scenario]`
Fast performance benchmark with automatic baseline
```
/benchmark-quick async
/benchmark-quick simple
```

## 🔄 Parallel Development with Git Worktrees

For working on multiple features simultaneously:

```bash
# Create worktree for feature
git worktree add ../evolve-feature-X feature/issue-X

# In terminal 1: Work on main branch
cd /Users/johan/Documents/evolve

# In terminal 2: Work on feature branch
cd /Users/johan/Documents/evolve-feature-X

# Run separate Claude sessions in each!
```

## 🤖 Subagent Verification Pattern

Use Claude's ability to spawn subagents for verification:

```
"Implement the island evolution strategy. Use a subagent to verify that the migration
logic correctly preserves population diversity by analyzing the implementation."
```

## 🚀 Headless Mode for Automation

For CI/build scripts or automated workflows:

```bash
# Non-interactive mode with specific task
claude-code -p "Run all tests and fix any formatting issues"

# With streaming JSON output
claude-code -p "Analyze test coverage" --json

# In CI pipeline
claude-code -p "Verify PR #$PR_NUMBER meets all quality standards"
```

## 🎨 Visual Development Workflow

For UI or visualization features:

1. **Provide Visual Target**:
   ```
   "Here's a screenshot of the desired evolution progress chart.
   Implement it using matplotlib."
   ```

2. **Iterative Refinement**:
   ```
   "The chart is close but needs: 1) Legend in top-right,
   2) Different colors for each strategy, 3) Grid lines"
   ```

## 🔒 Safe YOLO Mode

For maximum speed in isolated environments:

```bash
# In Docker container or VM only!
claude-code --dangerously-skip-permissions

# Claude works without confirmation prompts
# ⚠️ Only use in disposable environments!
```

## 📡 MCP Server Integration

The `.mcp.json` file enables advanced integrations:

### GitHub Integration
- Automatic issue management
- PR creation and review
- Issue triage

### Filesystem Integration
- Enhanced file operations
- Batch processing
- Advanced search

### Usage:
```bash
# With debug mode
claude-code --mcp-debug

# Check MCP status
/mcp status

# Use GitHub features
"Triage all open issues and label them appropriately"
"Create a PR for issue #42 with the changes we just made"
```

## 🎭 Context Preservation Techniques

### 1. Session Management
```bash
# Save session state
/save-session evolution-work

# Resume later
/load-session evolution-work
```

### 2. Context Anchoring
```
"Remember: We're working on issue #42 about async performance.
The key insight was that semaphores were causing bottlenecks."
```

### 3. Checkpoint Commands
```
/checkpoint "Finished implementing base async structure"
/checkpoint "All tests passing, starting optimization"
```

## 🎪 Advanced Task Patterns

### The "Swarm Pattern"
```
"Create 5 different implementations of the crossover function.
Test each one and keep the fastest that maintains quality."
```

### The "Evolution Pattern" (Meta!)
```
"Take the current test suite and evolve it to have better coverage.
Create 3 variants and measure their effectiveness."
```

### The "Exploration Pattern"
```
/think harder
"Explore 3 different ways to implement plugin architecture.
Create proof-of-concepts for each and compare."
```

## 💡 Pro Tips

1. **Chain Commands**:
   ```
   /test-focused async && /benchmark-quick async
   ```

2. **Use Thinking Modes for Design**:
   ```
   /ultrathink
   "Design the most efficient way to parallelize fitness evaluation"
   ```

3. **Combine Visual + Code**:
   ```
   "Here's a diagram of the data flow. Implement it exactly as shown."
   ```

4. **Leverage MCP for GitHub**:
   ```
   "Find all issues related to performance and create a tracking issue"
   ```

## 🚦 Quick Reference

| Feature | Command/Usage | When to Use |
|---------|--------------|-------------|
| Deep thinking | `/think harder` | Complex problems |
| Custom commands | `/test-focused` | Repeated workflows |
| Worktrees | `git worktree add` | Parallel development |
| Headless | `claude-code -p` | Automation/CI |
| MCP | `--mcp-debug` | GitHub integration |
| Visual | Screenshots | UI development |

## Remember

These advanced features are designed to make Claude Code more autonomous and efficient. The key is knowing when to use each feature for maximum impact.
