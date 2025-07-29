import os
import sys
import argparse

from core.venv_management import create_or_get_venv_paths
from core.package_management import install_missing_packages, clear_environment_packages
from core.config import DEFAULT_IMPORT_TO_PACKAGE_MAP, DEFAULT_REQUIREMENTS_FILE
from core.exceptions import PyEnvRunnerError


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Wrapper to manage Python venvs & run scripts, installing missing dependencies.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "script_path", nargs="?", default="main.py", help="Path to the Python script to run."
    )
    parser.add_argument(
        "--save-reqs", action="store_true", help="If set, newly installed packages will be saved to the requirements file."
    )
    parser.add_argument(
        "--reqs-file", default=DEFAULT_REQUIREMENTS_FILE, help="Name of the requirements file."
    )
    parser.add_argument(
        "--use-current-env", action="store_true", help="Use the current Python environment instead of creating/using a virtual environment."
    )
    parser.add_argument(
        "--env-name", default="env", help="Name of the virtual environment directory. Ignored if --use-current-env is set."
    )
    parser.add_argument(
        "--force-recreate-env", action="store_true", help="Delete and recreate the virtual environment if it exists. Ignored if --use-current-env."
    )
    parser.add_argument(
        "--list-import-mappings", action="store_true", help="Print the predefined import-to-package mappings and exit."
    )
    parser.add_argument(
        "--clear-env", action="store_true", help="Remove all installed non-editable packages from the target environment and exit."
    )

    args: argparse.Namespace = parser.parse_args()

    if args.list_import_mappings:
        print("--- Import to Package Mappings ---")
        for imp, pkg in DEFAULT_IMPORT_TO_PACKAGE_MAP.items():
            print(f"  {imp} -> {pkg}")
        print("----------------------------------")
        sys.exit(0)

    try:
        if args.clear_env:
            pip_to_use_for_clear: list[str] = []
            env_description: str = ""
            if args.use_current_env:
                env_description = "current Python environment"
                print(f"Preparing to clear packages from the {env_description}.")
                pip_to_use_for_clear = [sys.executable, "-m", "pip"]
            else:
                env_dir_to_clear: str = args.env_name
                env_description = f"virtual environment: '{env_dir_to_clear}'"
                print(f"Preparing to clear packages from {env_description}.")
                if not os.path.isdir(env_dir_to_clear):
                    print(f"Virtual environment directory '{env_dir_to_clear}' does not exist. Nothing to clear.")
                    sys.exit(0)

                pip_exe_path: str
                if os.name == "nt":
                    pip_exe_path = os.path.join(env_dir_to_clear, "Scripts", "pip.exe")
                else:
                    pip_exe_path = os.path.join(env_dir_to_clear, "bin", "pip")

                if not os.path.exists(pip_exe_path):
                    print(f"Pip executable not found at '{pip_exe_path}' in venv '{env_dir_to_clear}'. Cannot clear.")
                    sys.exit(1)

                pip_to_use_for_clear = [pip_exe_path]

            print(f"Target for clearing: {env_description}")
            clear_environment_packages(pip_to_use_for_clear)
            sys.exit(0)

        target_script_path: str = args.script_path
        if not os.path.exists(target_script_path):
            print(f"Error: Target script '{target_script_path}' not found.")
            sys.exit(1)

        activate_script_path: str | None
        venv_python_path: str | None
        venv_pip_command_list: list[str]

        activate_script_path, venv_python_path, venv_pip_command_list = create_or_get_venv_paths(
            env_name=args.env_name,
            force_recreate=args.force_recreate_env,
            use_current_env=args.use_current_env
        )

        if not args.use_current_env and activate_script_path:
            print(f"\nVirtual environment is ready in './{args.env_name}'.")
            print(f"To activate it manually in your shell:")
            try:
                rel_activate_path: str = os.path.relpath(activate_script_path, os.getcwd())
            except ValueError:
                rel_activate_path = activate_script_path

            if os.name == 'nt':
                print(f"  {rel_activate_path}")
            else:
                print(f"  source {rel_activate_path}")
            print("-" * 30)
        elif args.use_current_env:
            print("\nRunning in current Python environment. No venv activation needed by this script.")
            print("-" * 30)

        install_missing_packages(
            script_path=target_script_path,
            import_to_package_map=DEFAULT_IMPORT_TO_PACKAGE_MAP,
            venv_python_executable=venv_python_path,
            venv_pip_command_list=venv_pip_command_list,
            save_requirements_flag=args.save_reqs,
            requirements_file_name=args.reqs_file
        )

    except PyEnvRunnerError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

    print("\nWrapper script finished.")


if __name__ == "__main__":
    main()