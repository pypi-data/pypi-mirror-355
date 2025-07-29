"""Async Aider module for code modifications."""

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path

import aiofiles

from .config import EvolveConfig
from .errors import AiderError

logger = logging.getLogger(__name__)


class AsyncAiderModule:
    """Async wrapper for Aider code modifications."""

    def __init__(self, config: EvolveConfig):
        self.config = config
        self.aider_path: str = shutil.which("aider") or ""
        if not self.aider_path:
            raise RuntimeError("Aider not found. Install with: uv tool install aider-chat")
        self.active_processes = 0
        self.max_concurrent = config.max_concurrent_llm_calls

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Wait for any remaining processes
        while self.active_processes > 0:
            await asyncio.sleep(0.1)

    async def apply_changes_async(
        self,
        code: str,
        improvement: str,
    ) -> str:
        """Apply changes using Aider asynchronously.

        Args:
            code: The original code
            improvement: The improvement suggestion

        Returns:
            Modified code

        Raises:
            AiderError: If Aider fails to apply changes
        """
        # Wait if too many concurrent Aider processes
        while self.active_processes >= self.max_concurrent:
            await asyncio.sleep(0.5)

        self.active_processes += 1

        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
            ) as tmp_file:
                tmp_file.write(code)
                tmp_path = tmp_file.name

            # Prepare Aider command
            cmd = [
                self.aider_path,
            ]

            # Add flags based on config
            if self.config.aider_yes_always:
                cmd.append("--yes-always")

            if not self.config.aider_auto_commits:
                cmd.extend(
                    [
                        "--no-auto-commits",
                        "--no-dirty-commits",
                        "--no-attribute-author",
                        "--no-attribute-committer",
                        "--no-attribute-commit-message-author",
                        "--no-attribute-commit-message-committer",
                    ]
                )

            # Add ignore file if specified
            if self.config.aider_ignore_file:
                cmd.extend(["--ignore-file", self.config.aider_ignore_file])

            # Add message and file
            cmd.extend(
                [
                    "--message",
                    improvement,
                    tmp_path,
                ]
            )

            # Run Aider in subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.aider_timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise AiderError("Aider timed out") from None

            if process.returncode != 0:
                stderr_text = stderr.decode() if stderr else "No error output"
                raise AiderError(f"Aider failed with return code {process.returncode}: {stderr_text}")

            # Read modified code
            async with aiofiles.open(tmp_path, "r") as f:
                modified_code: str = await f.read()

            return modified_code

        finally:
            self.active_processes -= 1
            # Clean up temp file
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass
