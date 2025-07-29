# Async Parallel Evolution Architecture

## Overview

This document details the design for converting Evolve to an async-first architecture that enables efficient parallel variant generation, evaluation, and evolution. The goal is to achieve 3-5x performance improvement while maintaining the simple decorator API.

## Core Architecture Changes

### 1. Async Evolution Coordinator

```python
# coordinator.py changes
import asyncio
from typing import List, Optional, AsyncIterator
import aiofiles
from concurrent.futures import ThreadPoolExecutor

class AsyncEvolutionCoordinator:
    def __init__(self):
        self.database = ProgramDatabase()
        self.llm_semaphore = asyncio.Semaphore(5)  # Limit concurrent LLM calls
        self.executor_semaphore = asyncio.Semaphore(10)  # Limit concurrent executions
        self.thread_pool = ThreadPoolExecutor(max_workers=4)  # For CPU-bound tasks

    async def evolve_async(self,
                          evolution_target: EvolutionTarget,
                          iterations: int,
                          parallel_variants: int = 4) -> Program:
        """Main async evolution loop"""
        # Initialize with original program
        initial_program = await self._evaluate_program_async(
            evolution_target.initial_code,
            evolution_target
        )
        self.database.add_program(initial_program)

        # Evolution loop
        for iteration in range(iterations):
            # Generate and evaluate variants in parallel
            variants = await self._generate_variants_parallel(
                evolution_target,
                parallel_variants
            )

            # Update database with successful variants
            for variant in variants:
                if variant.success:
                    self.database.add_program(variant)

            # Progress callback
            await self._report_progress(iteration, self.database.best_program)

        return self.database.best_program

    async def _generate_variants_parallel(self,
                                        evolution_target: EvolutionTarget,
                                        count: int) -> List[Program]:
        """Generate multiple variants in parallel"""
        tasks = []

        for _ in range(count):
            # Select parent (can use different strategies)
            parent = self.database.sample()

            # Create task for variant generation
            task = self._create_variant_task(parent, evolution_target)
            tasks.append(task)

        # Wait for all variants
        variants = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out failed variants
        return [v for v in variants if isinstance(v, Program) and v is not None]

    async def _create_variant_task(self,
                                 parent: Program,
                                 evolution_target: EvolutionTarget) -> Optional[Program]:
        """Create and evaluate a single variant"""
        try:
            # Generate improvement suggestion (rate limited)
            async with self.llm_semaphore:
                improvement = await self._suggest_improvement_async(parent, evolution_target)

            # Apply changes using Aider
            modified_code = await self._apply_changes_async(parent.code, improvement)

            # Evaluate the variant (rate limited)
            async with self.executor_semaphore:
                result = await self._evaluate_program_async(modified_code, evolution_target)

            return result

        except Exception as e:
            logger.error(f"Variant creation failed: {e}")
            return None
```

### 2. Async LLM Integration

```python
# dspy_async.py
import aiohttp
from typing import Dict, Any
import backoff

class AsyncDSPyModule:
    def __init__(self, config: EvolveConfig):
        self.config = config
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientError,
        max_tries=3,
        max_time=60
    )
    async def suggest_improvement_async(self,
                                      parent: Program,
                                      context: Dict[str, Any]) -> str:
        """Generate improvement suggestion using async HTTP"""
        prompt = self._build_prompt(parent, context)

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": "You are an expert code optimizer."},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config.temperature
        }

        async with self.session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        ) as response:
            result = await response.json()
            return result["choices"][0]["message"]["content"]

    def _build_prompt(self, parent: Program, context: Dict[str, Any]) -> str:
        """Build context-aware prompt"""
        return f"""
        Goal: {context['goal']}

        Current code performance:
        - Primary metric: {parent.metrics.get(context['primary_metric'], 0)}
        - All metrics: {parent.metrics}

        Current code:
        ```python
        {parent.evolved_code}
        ```

        Suggest a specific improvement to achieve the goal.
        Focus on: {self._analyze_weakness(parent, context)}
        """

    def _analyze_weakness(self, parent: Program, context: Dict[str, Any]) -> str:
        """Analyze what aspect needs improvement"""
        # Smart analysis based on metrics trends
        if context.get('history'):
            return self._analyze_trends(context['history'])
        return "general optimization"
```

### 3. Async Aider Integration

```python
# aider_async.py
import asyncio
import aiofiles
from pathlib import Path
import ast

class AsyncAiderModule:
    def __init__(self):
        self.aider_path = self._find_aider()

    async def apply_changes_async(self,
                                code: str,
                                improvement: str) -> str:
        """Apply changes using Aider asynchronously"""
        # Create temporary file
        temp_file = Path(f"/tmp/evolve_{asyncio.current_task().get_name()}.py")

        async with aiofiles.open(temp_file, 'w') as f:
            await f.write(code)

        # Run Aider in subprocess
        process = await asyncio.create_subprocess_exec(
            self.aider_path,
            '--yes-always',
            '--no-auto-commits',
            '--message', improvement,
            str(temp_file),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise AiderError(f"Aider failed: {stderr.decode()}")

        # Read modified code
        async with aiofiles.open(temp_file, 'r') as f:
            modified_code = await f.read()

        # Clean up
        temp_file.unlink()

        return modified_code
```

### 4. Async Executor

```python
# executor_async.py
import asyncio
from typing import Dict, Any, Optional

class AsyncModalExecutor:
    def __init__(self):
        self.modal_stub = None
        self._init_modal()

    async def run_async(self,
                       code: str,
                       evolution_target: EvolutionTarget) -> ExecutionResult:
        """Execute code asynchronously in Modal"""
        # Create Modal function dynamically
        modal_func = self._create_modal_function(
            code,
            evolution_target.mount_dir,
            evolution_target.extra_packages
        )

        # Run asynchronously
        try:
            result = await asyncio.create_task(
                self._run_modal_async(modal_func)
            )

            return ExecutionResult(
                success=True,
                metrics=result.get('metrics', {}),
                stdout=result.get('stdout', ''),
                stderr=result.get('stderr', '')
            )

        except asyncio.TimeoutError:
            return ExecutionResult(
                success=False,
                error="Execution timeout"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=str(e)
            )

    async def _run_modal_async(self, modal_func) -> Dict[str, Any]:
        """Wrapper to run Modal function asynchronously"""
        loop = asyncio.get_event_loop()

        # Run Modal function in thread pool (since it's not async-native)
        return await loop.run_in_executor(
            None,  # Default executor
            modal_func.remote
        )

class AsyncLocalExecutor:
    """Async local executor for development/testing"""

    async def run_async(self,
                       code: str,
                       evolution_target: EvolutionTarget,
                       timeout: int = 30) -> ExecutionResult:
        """Run code locally with async subprocess"""

        # Write code to temp file
        temp_file = Path(f"/tmp/evolve_local_{asyncio.current_task().get_name()}.py")
        async with aiofiles.open(temp_file, 'w') as f:
            await f.write(code)

        try:
            # Run in subprocess
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                str(temp_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=evolution_target.mount_dir or Path.cwd()
            )

            # Wait with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise

            # Parse metrics from stdout
            metrics = self._extract_metrics(stdout.decode())

            return ExecutionResult(
                success=process.returncode == 0,
                metrics=metrics,
                stdout=stdout.decode(),
                stderr=stderr.decode()
            )

        finally:
            temp_file.unlink(missing_ok=True)
```

### 5. Progress Tracking & Monitoring

```python
# progress_async.py
import asyncio
from typing import Callable, Optional
from datetime import datetime

class AsyncProgressTracker:
    def __init__(self,
                 callback: Optional[Callable] = None,
                 update_interval: float = 1.0):
        self.callback = callback
        self.update_interval = update_interval
        self.start_time = datetime.now()
        self.events = []
        self._running = False

    async def start(self):
        """Start progress monitoring"""
        self._running = True
        asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """Stop progress monitoring"""
        self._running = False

    async def log_event(self, event_type: str, data: Dict[str, Any]):
        """Log an evolution event"""
        self.events.append({
            "timestamp": datetime.now(),
            "type": event_type,
            "data": data
        })

        if self.callback:
            await self.callback(event_type, data)

    async def _monitor_loop(self):
        """Background monitoring loop"""
        while self._running:
            # Calculate current statistics
            stats = self._calculate_stats()

            # Display progress
            print(f"\r[Evolution] "
                  f"Time: {stats['elapsed']:.1f}s | "
                  f"Variants: {stats['total_variants']} | "
                  f"Success Rate: {stats['success_rate']:.1%} | "
                  f"Best Fitness: {stats['best_fitness']:.4f}",
                  end='', flush=True)

            await asyncio.sleep(self.update_interval)
```

### 6. Integration with Existing API

```python
# Backward compatibility wrapper
def evolve(goal: str, **kwargs):
    """Original decorator with async execution under the hood"""
    def decorator(target):
        # Store metadata
        target._evolve_metadata = {
            "goal": goal,
            "async": kwargs.pop("async", True),  # Default to async
            **kwargs
        }

        # Return unmodified target
        return target
    return decorator

def main_entrypoint(func):
    """Enhanced main entrypoint with async support"""
    def wrapper(*args, **kwargs):
        if os.environ.get("EVOLVE"):
            # Run evolution asynchronously
            coordinator = AsyncEvolutionCoordinator()

            # Get evolution target
            target = _find_evolution_target()

            # Run async evolution in sync context
            best_program = asyncio.run(
                coordinator.evolve_async(
                    target,
                    iterations=int(os.environ.get("EVOLVE_ITERATIONS", "3")),
                    parallel_variants=int(os.environ.get("EVOLVE_PARALLEL", "4"))
                )
            )

            # Execute best program
            return _execute_best_program(best_program)
        else:
            # Normal execution
            return func(*args, **kwargs)

    return wrapper
```

## Performance Optimizations

### 1. Connection Pooling
- Reuse HTTP connections for LLM calls
- Modal connection pooling
- Aider process pooling

### 2. Resource Management
- Semaphores to limit concurrent operations
- Backpressure handling
- Memory-efficient streaming

### 3. Caching
- LLM response caching for similar prompts
- Modal image caching
- Compiled AST caching

## Configuration

```python
# New async-related config options
@dataclass
class EvolveConfig:
    # ... existing fields ...

    # Async settings
    parallel_variants: int = 4
    max_concurrent_llm_calls: int = 5
    max_concurrent_executions: int = 10
    async_timeout: int = 300
    enable_progress_bar: bool = True

    # Executor selection
    executor_type: str = "modal"  # "modal", "local", "docker"
```

## Migration Path

1. **Phase 1**: Add async variants alongside sync methods
2. **Phase 2**: Default to async with sync fallback
3. **Phase 3**: Deprecate sync-only paths

## Benefits

1. **3-5x Performance**: Parallel variant generation
2. **Better Resource Usage**: Non-blocking I/O
3. **Responsive UI**: Real-time progress updates
4. **Scalability**: Handle more variants efficiently
5. **Flexibility**: Easy to add new async strategies

This async architecture provides the foundation for high-performance evolution while maintaining the simple API that makes Evolve accessible.
