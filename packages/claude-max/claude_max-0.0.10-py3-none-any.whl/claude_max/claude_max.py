"""Claude Max integration for the SDK - simplified access for Max subscribers."""

import subprocess
import os
import asyncio
from pathlib import Path
from typing import Optional


def claude_max(prompt: str, claude_path: Optional[str] = None) -> str:
    """
    Execute a query using Claude Max subscription.
    
    This function provides a simple interface for Max subscribers to use Claude
    without dealing with API keys or complex configurations.
    
    Args:
        prompt: The query or prompt to send to Claude
        claude_path: Optional path to the claude CLI binary
        
    Returns:
        The response from Claude as a string
        
    Raises:
        FileNotFoundError: If claude CLI is not found
        RuntimeError: If the command fails
        
    Example:
        >>> from claude_max.claude_max import claude_max
        >>> response = claude_max("What is the capital of France?")
        >>> print(response)
        Paris
    """
    # Find claude binary
    if claude_path is None:
        # Try common locations
        possible_paths = [
            "/Users/agent/.nvm/versions/node/v22.13.0/bin/claude",
            Path.home() / ".local/bin/claude",
            Path("/usr/local/bin/claude"),
            Path.home() / ".npm-global/bin/claude",
            Path.home() / "node_modules/.bin/claude",
            Path.home() / ".yarn/bin/claude",
        ]
        
        # Check PATH first
        import shutil
        claude_path = shutil.which("claude")
        
        if not claude_path:
            for path in possible_paths:
                if path.exists() and path.is_file():
                    claude_path = str(path)
                    break
        
        if not claude_path:
            raise FileNotFoundError(
                "Claude CLI not found. Please install it with:\n"
                "  npm install -g @anthropic-ai/claude-code"
            )
    
    # Build command with print flag and bypass permissions
    cmd = [claude_path, "--print", "--dangerously-skip-permissions", prompt]
    
    # Set environment to force Claude Max subscription usage
    env = os.environ.copy()
    env["CLAUDE_CODE_ENTRYPOINT"] = "sdk-max"
    env["CLAUDE_USE_SUBSCRIPTION"] = "true"
    env["CLAUDE_BYPASS_BALANCE_CHECK"] = "true"
    
    # Remove API key to force subscription usage
    env.pop("ANTHROPIC_API_KEY", None)
    
    # Execute the command
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            raise RuntimeError(f"Claude command failed: {error_msg}")
        
        return result.stdout.strip()
        
    except subprocess.TimeoutExpired:
        raise RuntimeError("Claude command timed out after 5 minutes")
    except Exception as e:
        raise RuntimeError(f"Error executing claude: {e}")


async def claude_max_async(prompt: str, claude_path: Optional[str] = None) -> str:
    """
    Async version of claude_max for use in async contexts.
    
    Args:
        prompt: The query or prompt to send to Claude
        claude_path: Optional path to the claude CLI binary
        
    Returns:
        The response from Claude as a string
        
    Example:
        >>> from claude_max.claude_max import claude_max_async
        >>> response = await claude_max_async("Explain async/await in Python")
        >>> print(response)
    """
    # Find claude binary (same logic as sync version)
    if claude_path is None:
        import shutil
        claude_path = shutil.which("claude")
        
        if not claude_path:
            possible_paths = [
                "/Users/agent/.nvm/versions/node/v22.13.0/bin/claude",
                Path.home() / ".local/bin/claude",
                Path("/usr/local/bin/claude"),
                Path.home() / ".npm-global/bin/claude",
                Path.home() / "node_modules/.bin/claude",
                Path.home() / ".yarn/bin/claude",
            ]
            
            for path in possible_paths:
                if path.exists() and path.is_file():
                    claude_path = str(path)
                    break
        
        if not claude_path:
            raise FileNotFoundError(
                "Claude CLI not found. Please install it with:\n"
                "  npm install -g @anthropic-ai/claude-code"
            )
    
    # Set environment
    env = os.environ.copy()
    env["CLAUDE_CODE_ENTRYPOINT"] = "sdk-max"
    env["CLAUDE_USE_SUBSCRIPTION"] = "true"
    env["CLAUDE_BYPASS_BALANCE_CHECK"] = "true"
    env.pop("ANTHROPIC_API_KEY", None)
    
    # Create subprocess
    proc = await asyncio.create_subprocess_exec(
        claude_path,
        "--print",
        "--dangerously-skip-permissions",
        prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )
    
    # Wait for completion with timeout
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=300  # 5 minutes
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise RuntimeError("Claude command timed out after 5 minutes")
    
    if proc.returncode != 0:
        error_msg = stderr.decode() if stderr else stdout.decode() if stdout else "Unknown error"
        raise RuntimeError(f"Claude command failed: {error_msg}")
    
    return stdout.decode().strip()


async def claude_max_batch(prompts: list[str], claude_path: Optional[str] = None) -> list[str]:
    """
    Process multiple prompts in parallel using Claude Max.
    
    Args:
        prompts: List of prompts to process
        claude_path: Optional path to the claude CLI binary
        
    Returns:
        List of responses in the same order as prompts
        
    Example:
        >>> from claude_max.claude_max import claude_max_batch
        >>> prompts = ["What is 2+2?", "What is the capital of France?", "Explain Python"]
        >>> responses = await claude_max_batch(prompts)
        >>> for prompt, response in zip(prompts, responses):
        ...     print(f"Q: {prompt}")
        ...     print(f"A: {response[:50]}...")
    """
    tasks = [claude_max_async(prompt, claude_path) for prompt in prompts]
    return await asyncio.gather(*tasks)


# Convenience function for Jupyter notebooks
def claude_max_sync(prompt: str, claude_path: Optional[str] = None) -> str:
    """
    Synchronous wrapper for claude_max_async, useful in Jupyter notebooks.
    
    This is identical to claude_max() but provided for clarity when used
    alongside the async version.
    """
    return claude_max(prompt, claude_path)


def main():
    """CLI entry point for claude_max command."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: claude_max <prompt>", file=sys.stderr)
        print("Example: claude_max 'What is the capital of France?'", file=sys.stderr)
        sys.exit(1)
    
    prompt = " ".join(sys.argv[1:])
    
    try:
        response = claude_max(prompt)
        print(response)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


__all__ = [
    "claude_max",
    "claude_max_async",
    "claude_max_batch",
    "claude_max_sync",
]