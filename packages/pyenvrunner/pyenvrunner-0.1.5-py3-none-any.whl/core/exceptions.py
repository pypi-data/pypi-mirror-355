# src/core/exceptions.py

class PyEnvRunnerError(Exception):
    """Base exception for pyenvrunner issues."""
    pass

class VenvError(PyEnvRunnerError):
    """Base exception for venv related errors."""
    pass

class VenvCreationError(VenvError):
    """Error during venv creation."""
    pass

class VenvPathError(VenvError):
    """Error related to paths within a venv."""
    pass

class ScriptExecutionError(PyEnvRunnerError):
    """Error during script execution."""
    pass

class PackageManagementError(PyEnvRunnerError):
    """Base exception for package management errors."""
    pass

class PackageInstallationError(PackageManagementError):
    """Error during package installation."""
    pass

class RequirementsFileError(PackageManagementError):
    """Error related to the requirements file."""
    pass