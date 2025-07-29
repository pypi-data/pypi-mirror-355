"""Async DSPy module with Pydantic models for clean code."""

import logging
from typing import Any, Dict, List, Optional

import dspy

from .config import EvolveConfig
from .database import Program
from .history import EvolutionHistory
from .prompting.models import ProgramInfo

logger = logging.getLogger(__name__)


class CodeEvolutionWithInspirations(dspy.Signature):
    """Improve code by learning from high-scoring examples."""

    current_program: ProgramInfo = dspy.InputField(desc="Current program to improve")
    inspiration_programs: List[ProgramInfo] = dspy.InputField(desc="High-scoring example programs")
    goal: str = dspy.InputField(desc="Optimization goal")
    primary_metric: str = dspy.InputField(desc="Primary metric to optimize")
    improvement: str = dspy.OutputField(desc="Specific improvement description for the code")


class AsyncDSPyModule:
    """Async DSPy integration with Pydantic models for inspiration programs."""

    def __init__(self, config: EvolveConfig):
        self.config = config
        self.request_count = 0
        self.history = EvolutionHistory()
        self._setup_dspy()

    def _setup_dspy(self):
        """Configure DSPy with async support."""
        try:
            # Configure DSPy LM
            lm = dspy.LM(
                model=self.config.model,
                api_key=self.config.openrouter_api_key,
                api_base=self.config.api_base,
                temperature=self.config.temperature,
            )
            # Enable async with worker pool
            dspy.settings.configure(lm=lm, async_max_workers=self.config.dspy_async_max_workers)

            # Create async version of ChainOfThought with new signature
            sync_predictor = dspy.ChainOfThought(CodeEvolutionWithInspirations)
            self.async_predictor = dspy.asyncify(sync_predictor)

        except Exception as e:
            logger.error(f"Failed to setup async DSPy: {e}")
            raise

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - nothing to clean up."""
        pass

    async def suggest_improvement_async(
        self,
        parent: Program,
        context: Dict[str, Any],
        inspirations: Optional[List[Program]] = None,
    ) -> str:
        """Generate improvement suggestion using DSPy with Pydantic models.

        Args:
            parent: The parent program to improve
            context: Context including goal and primary metric
            inspirations: Optional list of high-scoring programs for inspiration

        Returns:
            Improvement suggestion string
        """
        try:
            primary_metric = context.get("primary_metric", "fitness")

            # Create ProgramInfo from parent
            # NOTE: We use Pydantic models directly here because DSPy automatically
            # serializes them to JSON. This was discovered through testing and saves
            # us from manual JSON formatting. See ADR-001 for details.
            parent_info = ProgramInfo.from_program(parent, primary_metric)

            # Create ProgramInfo list from inspirations
            if inspirations:
                # Sort by primary metric and take top max_inspiration_samples
                sorted_inspirations = sorted(
                    inspirations, key=lambda p: p.metrics.get(primary_metric, 0), reverse=True
                )[: self.config.max_inspiration_samples]
                inspiration_infos = [ProgramInfo.from_program(prog, primary_metric) for prog in sorted_inspirations]
            else:
                # Empty list if no inspirations
                inspiration_infos = []

            # Log the input being sent to DSPy
            logger.info("=== DSPy Input ===")
            logger.info(f"Current program score: {parent_info.score:.4f}")
            logger.info(f"Current program code preview: {parent_info.code[:100]}...")
            if len(inspiration_infos) == 0:
                logger.info(
                    "Number of inspiration programs: 0 (this is normal for the first generation - building knowledge base...)"
                )
            else:
                logger.info(f"Number of inspiration programs: {len(inspiration_infos)}")
            for i, insp in enumerate(inspiration_infos):
                logger.info(f"  Inspiration {i + 1} score: {insp.score:.4f}")
                logger.info(f"  Inspiration {i + 1} code preview: {insp.code[:100]}...")
            logger.info(f"Goal: {context.get('goal', 'Optimize code')}")
            logger.info(f"Primary metric: {primary_metric}")

            # Call async DSPy predictor with Pydantic models
            result = await self.async_predictor(
                current_program=parent_info,
                inspiration_programs=inspiration_infos,
                goal=context.get("goal", "Optimize code"),
                primary_metric=primary_metric,
            )

            self.request_count += 1

            # Inspect DSPy history after the call
            if hasattr(dspy, "inspect_history"):
                logger.info("=== DSPy History ===")
                history = dspy.inspect_history(n=1)
                if history:
                    logger.info(f"DSPy history: {history}")

            if hasattr(result, "improvement") and result.improvement:
                improvement = str(result.improvement)

                # Log the output
                logger.info("=== DSPy Output ===")
                logger.info(f"Improvement suggestion: {improvement[:200]}...")

                # Track in history
                self.history.add_record(
                    fitness=parent.metrics.get(primary_metric, 0),
                    success=parent.success,
                    improvement=improvement[:100],  # Store first 100 chars
                )

                return improvement
            else:
                logger.warning("DSPy result missing improvement")
                return "Refactor the code to improve performance and readability."

        except Exception as e:
            logger.error(f"Async DSPy call failed: {e}")
            # Track failure in history
            self.history.add_record(fitness=parent.metrics.get(primary_metric, 0), success=False, error=str(e))
            # Fallback suggestion
            return (
                f"Optimize the {context.get('primary_metric', 'performance')} metric through algorithmic improvements."
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get DSPy usage statistics."""
        return {
            "request_count": self.request_count,
            "generation": self.history.generation,
            "best_fitness": self.history.best_fitness,
            "plateau_count": self.history.plateau_count,
        }
