"""Pydantic models for enhanced prompting."""

from typing import Dict

from pydantic import BaseModel, Field

from ..database import Program


class ProgramInfo(BaseModel):
    """Structured program information for DSPy."""

    code: str = Field(description="The program code")
    metrics: Dict[str, float] = Field(description="Performance metrics")
    score: float = Field(description="Primary metric score")

    @classmethod
    def from_program(cls, program: Program, primary_metric: str) -> "ProgramInfo":
        """Create from database Program object."""
        return cls(code=program.evolve_code, metrics=program.metrics, score=program.metrics.get(primary_metric, 0.0))
