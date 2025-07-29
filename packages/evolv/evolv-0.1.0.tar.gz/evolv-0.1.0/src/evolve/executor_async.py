"""Async executors for running code in sandboxed environments."""

import asyncio
import json
import logging
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

import aiofiles

if TYPE_CHECKING:
    from .coordinator import EvolutionTarget

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of executing a program."""

    success: bool
    metrics: Dict[str, float]
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None


class AsyncModalExecutor:
    """Async Modal executor using sandbox execution."""

    def __init__(self):
        import modal

        self.app = modal.App.lookup("evolve-executor", create_if_missing=True)

    async def run_async(
        self,
        code: str,
        evolution_target: "EvolutionTarget",
        timeout: int = 60,
    ) -> ExecutionResult:
        """Execute code asynchronously in Modal sandbox."""
        import modal

        from evolve.config import get_config

        config = get_config()
        loop = asyncio.get_event_loop()

        # Build image with packages
        image = modal.Image.debian_slim()
        packages = list(config.sandbox_packages)
        if evolution_target.extra_packages:
            packages.extend(evolution_target.extra_packages)
        image = image.pip_install(packages).add_local_python_source("evolve")

        # Mount directory if specified
        work_dir = "/app"
        if evolution_target.mount_dir:
            image = image.add_local_dir(evolution_target.mount_dir, "/mnt/user_code")
            work_dir = "/mnt/user_code"

        # Execute in thread pool since Modal SDK is sync
        def run_in_sandbox():
            sb = None
            try:
                sb = modal.Sandbox.create(image=image, app=self.app, timeout=timeout)

                # Write and execute script
                sb.mkdir("/app")
                with sb.open("/app/main.py", "wb") as f:
                    f.write(code.encode())

                process = sb.exec("python", "/app/main.py", workdir=work_dir)
                process.wait()

                # Read results
                stdout = process.stdout.read() if process.stdout else ""
                stderr = process.stderr.read() if process.stderr else ""

                # Read metrics
                metrics = {}
                try:
                    with sb.open(f"{work_dir}/metrics.json", "rb") as f:
                        metrics = json.loads(f.read().decode())
                except Exception:
                    pass

                return ExecutionResult(
                    success=process.returncode == 0,
                    metrics=metrics,
                    stdout=stdout,
                    stderr=stderr,
                )
            except Exception as e:
                return ExecutionResult(
                    success=False,
                    metrics={},
                    stdout="",
                    stderr=str(e),
                )
            finally:
                if sb:
                    sb.terminate()

        return await loop.run_in_executor(None, run_in_sandbox)

    # Alias for compatibility
    run = run_async


class AsyncLocalExecutor:
    """Simple async local executor for development."""

    def __init__(self):
        """Initialize the local executor."""
        from .config import get_config

        config = get_config()
        self.default_timeout = config.local_executor_timeout

    async def run_async(
        self,
        code: str,
        evolution_target: "EvolutionTarget",
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        """Run code locally with async subprocess.

        Args:
            code: The code to execute
            evolution_target: Evolution target with configuration
            timeout: Execution timeout in seconds (uses config default if not specified)

        Returns:
            ExecutionResult with metrics and output
        """
        # Use default timeout if not specified
        if timeout is None:
            timeout = self.default_timeout

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            tmp_path = f.name

        # Prepare environment
        env = os.environ.copy()
        if evolution_target.mount_dir:
            env["PYTHONPATH"] = f"{evolution_target.mount_dir}:{env.get('PYTHONPATH', '')}"

        # Determine working directory
        cwd = evolution_target.mount_dir if evolution_target.mount_dir else os.getcwd()

        try:
            # Create and run subprocess
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=cwd,
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ExecutionResult(
                    success=False,
                    metrics={},
                    stdout="",
                    stderr="",
                    error=f"Execution timeout after {timeout}s",
                )

            # Parse metrics
            metrics = {}
            metrics_path = Path(cwd) / "metrics.json"
            if metrics_path.exists():
                try:
                    async with aiofiles.open(metrics_path, "r") as f:
                        content = await f.read()
                        metrics = json.loads(content)
                except Exception as e:
                    logger.warning(f"Failed to parse metrics.json: {e}")

            return ExecutionResult(
                success=process.returncode == 0,
                metrics=metrics,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else "",
            )

        except Exception as e:
            logger.error(f"Error in local executor: {e}")
            return ExecutionResult(
                success=False,
                metrics={},
                stdout="",
                stderr=str(e),
                error=f"Execution error: {e}",
            )
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    # Alias for compatibility
    run = run_async


def create_async_executor(executor_type: str) -> Any:
    """Create an async executor based on type.

    Args:
        executor_type: Type of executor ("modal" or "local")

    Returns:
        Executor instance
    """
    if executor_type == "local":
        return AsyncLocalExecutor()
    else:
        return AsyncModalExecutor()
