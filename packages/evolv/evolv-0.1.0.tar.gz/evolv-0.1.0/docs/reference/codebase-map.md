# Evolve Codebase Map

## 🗺️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     User Code                           │
│                  @evolve decorator                      │
└────────────────────────┬───────────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────────┐
│                 EvolutionCoordinator                    │
│  • Orchestrates the evolution loop                      │
│  • Manages async variant generation                     │
│  • Coordinates all components                           │
└──────┬─────────────┬────────────┬──────────────┬───────┘
       │             │            │              │
┌──────▼──────┐ ┌───▼────┐ ┌────▼─────┐ ┌──────▼──────┐
│ DSPyModule  │ │ Aider  │ │ Executor │ │  Database   │
│ • LLM calls │ │ • Code │ │ • Runs   │ │ • Stores    │
│ • Prompts   │ │   mods  │ │   code   │ │   programs  │
└─────────────┘ └────────┘ └──────────┘ └─────────────┘
```

## 📁 Directory Structure

```
src/evolve/
├── __init__.py          # Entry point, exports main API
├── coordinator.py       # 🎯 Main orchestrator (START HERE)
├── dspy_async.py        # LLM integration with inspirations
├── aider_async.py       # Code modification via Aider
├── executor_async.py    # Sandboxed code execution
├── database.py          # Program storage and retrieval
├── strategies/          # Evolution algorithms
│   ├── base.py         # Strategy interface
│   ├── basic.py        # Linear, Random, Tournament
│   └── map_elites.py   # Quality-diversity optimization
├── prompting/          # LLM prompt models
│   └── models.py       # Pydantic models for DSPy
├── config.py           # Configuration management
├── errors.py           # Custom exceptions
└── history.py          # Evolution history tracking
```

## 🔄 Data Flow

1. **User Input** → `@evolve(goal="...")` decorator
2. **Coordinator** → Manages evolution iterations
3. **Strategy** → Selects parent programs
4. **Database** → Provides inspiration programs
5. **DSPy Module** → Generates improvement suggestions
6. **Aider Module** → Applies code changes
7. **Executor** → Runs modified code safely
8. **Database** → Stores successful variants

## 🔑 Key Files to Understand

### For Overall Flow
1. `coordinator.py` - Start here to understand the main loop
2. `__init__.py` - See how decorators are wired

### For LLM Integration
1. `dspy_async.py` - How we prompt the LLM
2. `prompting/models.py` - Data structures for prompts

### For Evolution Logic
1. `strategies/base.py` - Strategy interface
2. `database.py` - How programs are stored/retrieved

### For Testing
1. `tests/test_coordinator.py` - Main flow tests
2. `tests/test_inspiration_prompting.py` - Prompting tests

## 💡 Quick Navigation Tips

- **To understand evolution flow**: Start at `coordinator.py:_evolve_async()`
- **To modify LLM prompts**: Look at `dspy.py` signatures
- **To add new strategy**: Extend `strategies/base.py`
- **To change execution**: Modify `executor_async.py`

## ⚠️ Common Pitfalls

1. **Async Everywhere**: Most methods are async - don't forget `await`
2. **Singleton Coordinator**: Don't instantiate, use the global instance
3. **Database IDs**: Are strings, not integers
4. **Metrics Dict**: Must include the primary_metric key
