"""
Command execution utilities for DepMan.
"""
import logging
import os
import subprocess
import shlex
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union


class CommandResult:
    """Represents the result of a command execution."""
    
    def __init__(
        self,
        returncode: int,
        stdout: str,
        stderr: str,
        cmd: str,
        success: bool = None,
        execution_time: float = None
    ) -> None:
        """
        Initialize the command result.
        
        Args:
            returncode (int): Return code of the command.
            stdout (str): Standard output of the command.
            stderr (str): Standard error of the command.
            cmd (str): Command that was executed.
            success (bool, optional): Override success determination. Defaults to None.
            execution_time (float, optional): Command execution time in seconds. Defaults to None.
        """
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.cmd = cmd
        self._success = success if success is not None else (returncode == 0)
        self.execution_time = execution_time
    
    @property
    def success(self) -> bool:
        """Check if the command was successful."""
        return self._success
    
    def __bool__(self) -> bool:
        """Boolean representation of the result."""
        return self.success
        
    def get_formatted_execution_time(self) -> str:
        """
        Get formatted execution time as a human-readable string.
        
        Returns:
            str: Formatted execution time string or empty string if not available.
        """
        if self.execution_time is None:
            return ""
            
        if self.execution_time < 0.1:
            return f"{self.execution_time * 1000:.0f}毫秒"
        elif self.execution_time < 1:
            return f"{self.execution_time * 1000:.0f}毫秒"
        elif self.execution_time < 60:
            return f"{self.execution_time:.2f}秒"
        else:
            minutes = int(self.execution_time // 60)
            seconds = self.execution_time % 60
            return f"{minutes}分{seconds:.2f}秒"


class CommandExecutor:
    """Utility class for executing shell commands."""
    
    def __init__(self):
        """Initialize the command executor."""
        self.logger = logging.getLogger("depman.cmd_executor")
    
    def run_command(
        self,
        cmd: Union[str, List[str]],
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 120,
        shell: bool = False,
        check: bool = False,
        capture_output: bool = True,
        measure_time: bool = True,
    ) -> CommandResult:
        """
        Run a command and return the result.
        
        Args:
            cmd (Union[str, List[str]]): Command to run.
            cwd (Optional[Union[str, Path]], optional): Working directory. Defaults to None.
            env (Optional[Dict[str, str]], optional): Environment variables. Defaults to None.
            timeout (int, optional): Timeout in seconds. Defaults to 120.
            shell (bool, optional): Whether to use shell. Defaults to False.
            check (bool, optional): Whether to raise if returncode is non-zero. Defaults to False.
            capture_output (bool, optional): Whether to capture output. Defaults to True.
            measure_time (bool, optional): Whether to measure execution time. Defaults to True.
            
        Returns:
            CommandResult: Result of the command.
            
        Raises:
            subprocess.TimeoutExpired: If the command times out.
            subprocess.SubprocessError: If check is True and returncode is non-zero.
        """
        # Format the command as needed
        import platform
        is_windows = platform.system().lower() == 'windows'
        
        if isinstance(cmd, list) and not shell:
            if is_windows:
                # Windows不使用shlex引用
                cmd_str = " ".join(str(c) for c in cmd)
            else:
                # Unix系统使用shlex引用
                cmd_str = " ".join(shlex.quote(c) for c in cmd)
        else:
            if isinstance(cmd, list):
                cmd_str = " ".join(str(c) for c in cmd)
            else:
                cmd_str = cmd
        
        self.logger.debug(f"Running command: {cmd_str}")
        
        # Set up environment variables
        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)
        
        # Start execution time measurement
        start_time = time.time() if measure_time else None
        
        try:
            # Run the command
            process = subprocess.run(
                cmd,
                cwd=cwd,
                env=cmd_env,
                timeout=timeout,
                shell=shell,
                check=check,
                capture_output=capture_output,
                text=True,
            )
            
            # Calculate execution time if requested
            execution_time = time.time() - start_time if measure_time else None
            
            # Create the result object
            result = CommandResult(
                returncode=process.returncode,
                stdout=process.stdout if capture_output else "",
                stderr=process.stderr if capture_output else "",
                cmd=cmd_str,
                execution_time=execution_time
            )
            
            # Log the outcome
            if result.success:
                time_str = f" (耗时: {result.get_formatted_execution_time()})" if measure_time else ""
                self.logger.debug(f"Command succeeded{time_str}: {cmd_str}")
            else:
                time_str = f" after {result.get_formatted_execution_time()}" if measure_time else ""
                self.logger.warning(f"Command failed with exit code {result.returncode}{time_str}: {cmd_str}")
                if capture_output and result.stderr:
                    self.logger.warning(f"Error output: {result.stderr}")
            
            return result
            
        except subprocess.TimeoutExpired as e:
            execution_time = time.time() - start_time if measure_time else None
            self.logger.error(f"Command timed out after {timeout}s: {cmd_str}")
            return CommandResult(
                returncode=124,  # Common timeout exit code
                stdout=getattr(e, 'stdout', '') or '',
                stderr=getattr(e, 'stderr', '') or f"Timeout after {timeout} seconds",
                cmd=cmd_str,
                success=False,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time if measure_time else None
            
            # 对于命令检测类操作（which/where），使用debug级别而不是error
            if isinstance(cmd, list) and any(x in ['which', 'where'] for x in cmd):
                self.logger.debug(f"Command check failed: {cmd_str}")
                self.logger.debug(f"Details: {str(e)}")
            else:
                self.logger.error(f"Error executing command: {cmd_str}")
                self.logger.error(f"Error details: {str(e)}")
            
            return CommandResult(
                returncode=1,
                stdout='',
                stderr=str(e),
                cmd=cmd_str,
                success=False,
                execution_time=execution_time
            )
    
    def command_exists(self, cmd: str) -> bool:
        """
        Check if a command exists in the system.
        
        Args:
            cmd (str): Command to check.
            
        Returns:
            bool: True if the command exists, False otherwise.
        """
        import shutil
        import platform
        
        # First try using shutil.which, which is more reliable
        if shutil.which(cmd) is not None:
            return True
            
        # Fallback to platform-specific command
        is_windows = platform.system().lower() == 'windows'
        
        if is_windows:
            # On Windows, use 'where' command
            result = self.run_command(['where', cmd], shell=False)
        else:
            # On Unix-like systems, use 'which' command
            result = self.run_command(['which', cmd], shell=False)
        
        return result.success

    def get_command_output(self, cmd: Union[str, List[str]], **kwargs) -> str:
        """
        Run a command and return its output.
        
        Args:
            cmd (Union[str, List[str]]): Command to run.
            
        Returns:
            str: Output of the command.
        """
        result = self.run_command(cmd, capture_output=True, **kwargs)
        return result.stdout.strip() if result.success else '' 