# ADR-001: Use Pydantic Models Directly in DSPy Signatures

## Status
Accepted

## Context
Initially, we assumed DSPy signatures required string inputs and created complex prompt formatting strategies with manual JSON serialization. This led to over-engineered code with multiple abstraction layers.

## Decision
Use Pydantic models directly as DSPy InputFields, leveraging DSPy's automatic serialization to JSON.

## Consequences
**Positive:**
- Cleaner, more maintainable code
- Type safety with automatic validation
- Less code to maintain
- Self-documenting field descriptions

**Negative:**
- Dependency on DSPy's serialization behavior
- Less control over exact JSON formatting

## Lessons Learned
- Always test library capabilities before building abstractions
- Start with the simplest possible implementation
- Read the source code, not just documentation

## Code Examples
```python
# Before (what we initially tried)
class BasePromptStrategy(ABC):
    @abstractmethod
    def format_program(self, program: Program) -> str:
        pass

class JSONPromptStrategy(BasePromptStrategy):
    def format_program(self, program: Program) -> str:
        return json.dumps({
            "code": program.evolve_code,
            "metrics": program.metrics,
            "score": program.metrics.get(self.primary_metric, 0)
        })

# After (what actually works)
class ProgramInfo(BaseModel):
    code: str = Field(description="The program code")
    metrics: Dict[str, float] = Field(description="Performance metrics")
    score: float = Field(description="Primary metric score")

class CodeEvolutionWithInspirations(dspy.Signature):
    current_program: ProgramInfo = dspy.InputField(desc="Current program to improve")
    inspiration_programs: List[ProgramInfo] = dspy.InputField(desc="High-scoring example programs")
```
