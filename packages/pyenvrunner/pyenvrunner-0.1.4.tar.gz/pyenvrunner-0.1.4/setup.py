from setuptools import setup, find_packages

setup(
    name="pyenvrunner",
    version="0.1.4",
    description="Wrapper to manage Python venvs & run scripts, installing missing dependencies",
    author="Aditya Thiyyagura",
    author_email="thiyyaguraadityareddy@gmail.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "pyenvrunner=cli.main:main",
        ],
    },
    python_requires=">=3.6",
    install_requires=[
        # Add your base dependencies here
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)