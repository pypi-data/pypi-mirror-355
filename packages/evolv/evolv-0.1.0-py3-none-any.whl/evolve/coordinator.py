"""Unified evolution coordinator with async-first architecture."""

import asyncio
import functools
import inspect
import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, TypeVar

from .config import get_config
from .database import Program, ProgramDatabase
from .strategies import EvolutionStrategy

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class EvolutionTarget:
    """Target function/class to evolve."""

    name: str
    goal: str
    source: str
    original_file_path: str
    original_full_code: str
    is_class: bool
    iterations: Optional[int] = None
    sampling_strategy_name: Optional[str] = None
    strategy_config: Optional[Dict[str, Any]] = None
    mount_dir: Optional[str] = None
    extra_packages: Optional[List[str]] = None


class EvolutionCoordinator:
    """Unified coordinator with async internals and sync API."""

    def __init__(self):
        self.target: Optional[EvolutionTarget] = None
        self.main_func_reference: Optional[Callable[..., Any]] = None
        self.main_script_path: Optional[str] = None
        self.evolve_script_path: Optional[str] = None

    def evolve(
        self,
        goal: str,
        iterations: Optional[int] = None,
        strategy: Optional[str] = None,
        strategy_config: Optional[Dict[str, Any]] = None,
        mount_dir: Optional[str] = None,
        extra_packages: Optional[List[str]] = None,
    ) -> Callable[[T], T]:
        """Decorator to mark a function or class for evolution.

        Args:
            goal: Natural language description of the optimization goal
            iterations: Number of evolution iterations (default: from config)
            strategy: Evolution strategy name (default: 'linear')
            strategy_config: Strategy-specific configuration dict
            mount_dir: Local directory to mount in sandbox
            extra_packages: Additional pip packages to install
        """

        def decorator(func_or_class: T) -> T:
            # Validate extra packages
            validated_packages = extra_packages
            if validated_packages and not (
                isinstance(validated_packages, list) and all(isinstance(pkg, str) for pkg in validated_packages)
            ):
                logger.warning("Invalid 'extra_packages' provided to @evolve. Must be a list of strings.")
                validated_packages = None

            if self.target:
                logger.warning(
                    "@evolve decorator applied multiple times. Using: %s", getattr(func_or_class, "__name__", "unknown")
                )

            # Get source information
            source_file_path = inspect.getsourcefile(func_or_class)
            if not source_file_path:
                raise ValueError("Could not determine the source file path for the decorated object.")

            self.evolve_script_path = os.path.abspath(source_file_path)

            with open(self.evolve_script_path) as f:
                full_code = f.read()

            # Create evolution target
            self.target = EvolutionTarget(
                name=getattr(func_or_class, "__name__", "unknown"),
                goal=goal,
                source=inspect.getsource(func_or_class),
                original_file_path=self.evolve_script_path,
                original_full_code=full_code,
                is_class=inspect.isclass(func_or_class),
                iterations=iterations,
                sampling_strategy_name=strategy,
                strategy_config=strategy_config or {},
                mount_dir=mount_dir,
                extra_packages=validated_packages,
            )

            return func_or_class

        return decorator

    def main_entrypoint(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator to mark the main entry point for evolution.
        The decorated function should return a dict with metrics.
        When EVOLVE=1, triggers evolution mode.
        """
        self.main_func_reference = func
        main_func_file_path = inspect.getsourcefile(func)
        if not main_func_file_path:
            raise ValueError("Could not determine the source file path for the main_entrypoint function.")
        self.main_script_path = os.path.abspath(main_func_file_path)

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not os.environ.get("EVOLVE"):
                # Normal execution mode
                metrics = func(*args, **kwargs)
                with open("metrics.json", "w") as f:
                    try:
                        json.dump(metrics, f)
                    except TypeError as e:
                        json.dump({"error": str(e)}, f)
                return metrics

            # Evolution mode
            if not self.target:
                logger.error("@evolve decorator not used. Please decorate a target with @evolve(goal='...')")
                return {"error": "Evolution target not set."}

            # Run evolution (async internally, sync externally)
            asyncio.run(self._evolve_async())
            return {"status": "Evolution process initiated and concluded."}

        return wrapper

    async def _evolve_async(self) -> None:
        """Main async evolution implementation."""
        if not self.target:
            logger.error("Evolution target not set.")
            return

        config = get_config()

        # Import async modules
        from .aider_async import AsyncAiderModule
        from .dspy_async import AsyncDSPyModule
        from .executor_async import create_async_executor
        from .strategies import StrategyFactory

        # Setup components
        async with AsyncDSPyModule(config) as llm_module, AsyncAiderModule(config) as aider_module:
            executor = create_async_executor(config.executor_type)

            # Create database and strategy
            from .database import LinearSamplingStrategy

            database = ProgramDatabase(LinearSamplingStrategy())

            # Setup evolution strategy if specified
            evolution_strategy = None
            if (
                self.target.sampling_strategy_name
                and self.target.sampling_strategy_name in StrategyFactory.list_strategies()
            ):
                try:
                    evolution_strategy = StrategyFactory.create(self.target.sampling_strategy_name)
                    logger.info("Using strategy: %s", self.target.sampling_strategy_name)
                except Exception as e:
                    logger.warning("Failed to create strategy: %s", e)

            # Evaluate initial program
            logger.info("Evaluating initial program...")
            initial_program = await self._evaluate_program(self.target.original_full_code, self.target.source, executor)

            if not initial_program.success:
                logger.error("Initial program failed: %s", initial_program.stderr)
                return

            database.add(initial_program)
            if evolution_strategy:
                evolution_strategy.initialize(self.target.strategy_config, initial_program)
            logger.info("Initial program metrics: %s", initial_program.metrics)
            initial_fitness = initial_program.metrics.get(config.primary_metric, 0)
            logger.info(f"Initial {config.primary_metric}: {initial_fitness:.6f}")

            # Get iteration count
            num_iterations = self.target.iterations if self.target.iterations is not None else config.default_iterations
            parallel_variants = config.parallel_variants

            # Evolution loop
            logger.info("Starting %d iterations with %d parallel variants...", num_iterations, parallel_variants)
            start_time = asyncio.get_event_loop().time()

            for iteration in range(num_iterations):
                # Generate variants in parallel
                variants = await self._generate_variants_parallel(
                    database, evolution_strategy, llm_module, aider_module, executor, parallel_variants
                )

                # Update database with successful variants
                successful = 0
                for variant in variants:
                    if variant and variant.success:
                        if not evolution_strategy or evolution_strategy.should_accept(variant, database):
                            database.add(variant)
                            if evolution_strategy:
                                evolution_strategy.update_state(variant, database)
                            successful += 1

                # Progress update
                elapsed = asyncio.get_event_loop().time() - start_time
                best = database.get_best_program()
                best_fitness = best.metrics.get(config.primary_metric, 0)
                improvement = ((best_fitness - initial_fitness) / initial_fitness) * 100 if initial_fitness > 0 else 0

                logger.info(
                    f"Iteration {iteration + 1}/{num_iterations} completed: "
                    f"{successful}/{len(variants)} successful variants, "
                    f"best {config.primary_metric}={best_fitness:.6f} "
                    f"(+{improvement:.2f}% from initial)"
                )

                print(
                    f"\r[Evolution] Iteration {iteration + 1}/{num_iterations} | "
                    f"Variants: {successful}/{len(variants)} | "
                    f"Best: {best_fitness:.4f} (+{improvement:.1f}%) | "
                    f"Time: {elapsed:.1f}s",
                    end="",
                    flush=True,
                )

            print()  # New line after progress

            # Report results
            self._report_best_program(database)

    async def _generate_variants_parallel(
        self,
        database: ProgramDatabase,
        strategy: Optional[EvolutionStrategy],
        llm_module,
        aider_module,
        executor,
        count: int,
    ) -> List[Optional[Program]]:
        """Generate multiple variants in parallel."""
        # Select parents
        logger.debug(f"Selecting {count} parents for parallel generation")
        if strategy:
            parents = strategy.select_parents(database, count=count)
            # For each parent, get inspirations from database
            parents_with_inspirations = []
            for parent in parents:
                _, inspirations = database.sample()  # This gets inspirations based on sampling strategy
                parents_with_inspirations.append((parent, inspirations))
        else:
            # Fallback: use database sampling directly
            parents_with_inspirations = [database.sample() for _ in range(count)]
        logger.debug(f"Selected {len(parents_with_inspirations)} parents with inspirations")

        # Ensure we have enough parents
        if not parents_with_inspirations:
            logger.error("No parents available")
            return []
        while len(parents_with_inspirations) < count:
            parents_with_inspirations.append(parents_with_inspirations[0])  # Reuse first parent

        # Create variant tasks
        tasks = [
            asyncio.create_task(
                self._create_variant(parent, inspirations, llm_module, aider_module, executor, f"variant_{i}")
            )
            for i, (parent, inspirations) in enumerate(parents_with_inspirations[:count])
        ]

        # Wait for all variants
        variants = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_variants = [v for v in variants if not isinstance(v, Exception) and v is not None]
        logger.debug(f"Generated {len(valid_variants)}/{len(variants)} valid variants")
        return valid_variants

    async def _create_variant(
        self,
        parent: Program,
        inspirations: List[Program],
        llm_module,
        aider_module,
        executor,
        name: str,
    ) -> Optional[Program]:
        """Create a single variant."""
        try:
            # Get improvement suggestion
            logger.debug(f"{name}: Getting improvement suggestion from LLM")
            improvement = await llm_module.suggest_improvement_async(
                parent,
                {"goal": self.target.goal, "primary_metric": get_config().primary_metric},
                inspirations=inspirations,
            )
            logger.debug(f"{name}: LLM suggestion: {improvement[:100]}...")

            logger.debug(f"{name}: Applying changes with Aider")
            modified_code = await aider_module.apply_changes_async(parent.program_code, improvement)

            # Extract entity and evaluate
            logger.debug(f"{name}: Extracting evolved entity")
            evolved_entity = self._extract_entity(modified_code, self.target.name)

            logger.debug(f"{name}: Evaluating in executor")
            new_program = await self._evaluate_program(modified_code, evolved_entity, executor, parent_id=parent.id)

            if new_program.success:
                logger.info(f"{name}: Success! Metrics: {new_program.metrics}")
            else:
                logger.warning(f"{name}: Failed. Error: {new_program.stderr[:100]}...")
            return new_program

        except Exception as e:
            logger.error(f"{name}: Failed to create variant: {e}")
            return None

    async def _evaluate_program(
        self,
        program_code: str,
        evolve_code: str,
        executor,
        parent_id: Optional[str] = None,
    ) -> Program:
        """Evaluate a program."""
        result = await executor.run(program_code, self.target)
        return Program(
            program_code=program_code,
            evolve_code=evolve_code,
            parent_id=parent_id,
            success=result.success,
            stdout=result.stdout,
            stderr=result.stderr,
            metrics=result.metrics,
        )

    def _extract_entity(self, code: str, entity_name: str) -> str:
        """Extract entity source code using AST."""
        import ast

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == entity_name:
                    return ast.unparse(node)
        except Exception as e:
            logger.error(f"Failed to extract entity {entity_name}: {e}")

        return code

    def _report_best_program(self, database: ProgramDatabase) -> None:
        """Report the best program found."""
        best_program = database.get_best_program()
        if best_program:
            # Get initial program for comparison
            all_programs = list(database.programs.values())
            # Sort by ID to get the initial program (lowest ID)
            all_programs.sort(key=lambda p: int(p.id))
            initial_program = all_programs[0] if all_programs else None

            config = get_config()
            best_fitness = best_program.metrics.get(config.primary_metric, 0)
            initial_fitness = initial_program.metrics.get(config.primary_metric, 0) if initial_program else 0
            improvement = ((best_fitness - initial_fitness) / initial_fitness) * 100 if initial_fitness > 0 else 0

            logger.info("=" * 60)
            logger.info("EVOLUTION COMPLETE - RESULTS SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Initial {config.primary_metric}: {initial_fitness:.6f}")
            logger.info(f"Best {config.primary_metric}: {best_fitness:.6f}")
            logger.info(f"Improvement: +{improvement:.2f}%")
            logger.info(f"Total programs evaluated: {len(database.programs)}")
            logger.info(f"Best program ID: {best_program.id}")
            logger.info(f"Best metrics: {best_program.metrics}")
            logger.info("=" * 60)

            logger.info(
                "To use the best version of '%s', replace its code in '%s' with:",
                self.target.name,
                self.target.original_file_path,
            )
            logger.info("--- Best Program Code ---")
            logger.info("Full program code:\n%s", best_program.program_code)
            logger.info("--- End Best Program Code ---")
        else:
            logger.info("Evolution complete. No successful programs found.")


# Global coordinator instance
coordinator = EvolutionCoordinator()

# Export decorators
evolve = coordinator.evolve
main_entrypoint = coordinator.main_entrypoint
