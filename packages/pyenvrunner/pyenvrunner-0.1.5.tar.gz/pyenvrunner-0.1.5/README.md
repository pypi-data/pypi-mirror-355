# PyEnvRunner

[![PyPI version](https://badge.fury.io/py/pyenvrunner.svg)](https://badge.fury.io/py/pyenvrunner)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A smart Python script runner that automatically manages virtual environments and handles missing dependencies.

## 🚀 Quick Start

```bash
# Install PyEnvRunner
pip install pyenvrunner

# Run a Python script (automatically creates venv and installs dependencies)
pyenvrunner your_script.py
```

## 🎯 Overview

PyEnvRunner simplifies running Python scripts by:
- Creating and managing virtual environments automatically
- Installing missing dependencies on-the-fly
- Tracking installed packages in a requirements file
- Handling import-to-package name mappings (e.g., `cv2` → `opencv-python`)

## ✨ Features

- **Automatic venv Management**: Creates/uses virtual environments seamlessly
- **Smart Dependency Installation**: Detects and installs missing packages
- **Requirements Tracking**: Records installed packages automatically
- **Import Name Resolution**: Maps import names to correct PyPI packages
- **Environment Control**: Options to use current environment or force venv recreation
- **Cross-Platform**: Works on Windows, Linux, and macOS

## 📖 Usage

### Basic Usage

```bash
pyenvrunner [pyenvrunner-options] script_path [script-args]
```

- All PyEnvRunner options (those starting with `--` or `-` and listed below) **must come before** the script path.
- All arguments after the script path are passed to the Python script as-is.

> **Note:** If you place a PyEnvRunner option after the script path, it will result in an error.

### Command Options

| Option | Description |
|--------|-------------|
| `--no-save-reqs` | Don't append installed packages to requirements file |
| `--reqs-file <name>` | Custom requirements file name (default: `pyenvrunner_requirements.txt`) |
| `--use-current-env` | Use current Python environment instead of venv |
| `--env-name <name>` | Custom virtual environment directory name (default: `env`) |
| `--force-recreate-env` | Recreate virtual environment if it exists |
| `--list-import-mappings` | Show predefined import-to-package mappings |
| `--clear-env` | Remove all packages from target environment |
| `-h, --help` | Show help message |
| `script_path` | **Required.** Path to the Python script to run |
| `script-args` | Arguments to pass to your script (all after `script_path`) |

### Examples

1. **Basic Script Execution**
   ```bash
   pyenvrunner script.py
   ```

2. **Custom Environment Name**
   ```bash
   pyenvrunner --env-name custom_env script.py
   ```

3. **Use Current Environment**
   ```bash
   pyenvrunner --use-current-env script.py
   ```

4. **Custom Requirements File**
   ```bash
   pyenvrunner --reqs-file custom_requirements.txt script.py
   ```

5. **Passing Arguments to Your Script**
   ```bash
   pyenvrunner --env-name myenv script.py --arg1 value1 --arg2 value2
   # --arg1 and --arg2 are passed to script.py, not to pyenvrunner
   ```

6. **Incorrect Usage (will error)**
   ```bash
   pyenvrunner script.py --env-name myenv
   # Error: PyEnvRunner arguments must come before the script path.
   ```

7. **Clear Environment**
   ```bash
   pyenvrunner --clear-env --env-name old_env
   ```

## 🔧 How It Works

1. **Environment Setup**
   - Creates/uses specified virtual environment
   - Uses current environment if `--use-current-env` is set
   - Recreates environment if `--force-recreate-env` is set

2. **Script Execution**
   - Runs the target script
   - Catches `ModuleNotFoundError`s
   - Installs missing packages automatically
   - Retries script execution

3. **Package Management**
   - Maps import names to PyPI packages
   - Installs packages using pip
   - Records installations in requirements file
   - Handles package cleaning and environment management

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🛠️ Development Setup

1. Clone the repository
2. Install development dependencies
3. Set up pre-commit hooks
4. Run tests

## 📚 API Documentation

For detailed API documentation, please visit our [documentation page](https://pyenvrunner.readthedocs.io/).

## 🤔 FAQ

**Q: Can I use this with existing virtual environments?**  
A: Yes, specify the environment name using `--env-name`.

**Q: Is it safe to use `--clear-env`?**  
A: Use with caution, especially with `--use-current-env`. Always review the packages to be removed.

**Q: Why do I get an error about argument order?**  
A: All PyEnvRunner options (those listed above) must come before the script path. Any arguments after the script path are passed to your script. For example:
   ```bash
   pyenvrunner --env-name myenv script.py --my-script-arg
   # Correct
   pyenvrunner script.py --env-name myenv
   # Incorrect (will error)
   ```

## 🐛 Troubleshooting

For common issues and solutions, please check our [troubleshooting guide](https://github.com/yourusername/pyenvrunner/wiki/troubleshooting).