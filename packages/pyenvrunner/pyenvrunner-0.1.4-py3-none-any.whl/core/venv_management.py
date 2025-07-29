import os
import sys
import shutil
import subprocess
from typing import Tuple, Optional, List
from .exceptions import VenvCreationError, VenvPathError

def create_or_get_venv_paths(
    env_name: str = "env",
    force_recreate: bool = False,
    use_current_env: bool = False
) -> Tuple[Optional[str], str, List[str]]:
    if use_current_env:
        python_executable: str = sys.executable
        pip_command_list: List[str] = [sys.executable, "-m", "pip"]

        if not os.path.exists(python_executable):
            raise VenvPathError(f"Current Python executable not found at {python_executable}")

        return None, python_executable, pip_command_list

    env_path: str = env_name
    if force_recreate and os.path.exists(env_path) and os.path.isdir(env_path):
        try:
            shutil.rmtree(env_path)
        except OSError as e:
            raise VenvCreationError(f"Error deleting existing virtual environment '{env_path}': {e}")

    if not os.path.exists(env_path):
        try:
            subprocess.run([sys.executable, "-m", "venv", env_path], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            stderr_msg: str = f"\nStderr: {e.stderr.strip()}" if e.stderr else ""
            raise VenvCreationError(f"Error creating virtual environment: {e}{stderr_msg}")
        except FileNotFoundError:
            raise VenvCreationError(f"Error: '{sys.executable}' not found. Cannot create virtual environment.")

    if os.name == "nt":
        activate_script: str = os.path.join(env_path, "Scripts", "activate")
        python_executable: str = os.path.join(env_path, "Scripts", "python.exe")
        pip_executable: str = os.path.join(env_path, "Scripts", "pip.exe")
    else:
        activate_script = os.path.join(env_path, "bin", "activate")
        python_executable = os.path.join(env_path, "bin", "python")
        pip_executable = os.path.join(env_path, "bin", "pip")

    if not os.path.exists(python_executable):
        raise VenvPathError(f"Python executable not found at {python_executable} in venv '{env_path}'")
    if not os.path.exists(pip_executable):
        raise VenvPathError(f"pip executable not found at {pip_executable} in venv '{env_path}'")

    return activate_script, python_executable, [pip_executable]