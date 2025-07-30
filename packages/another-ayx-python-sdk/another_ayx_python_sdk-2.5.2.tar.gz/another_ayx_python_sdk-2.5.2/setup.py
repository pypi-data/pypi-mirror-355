from setuptools import setup, find_packages, Command
import os
import shutil

class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        for dir_to_remove in ['build', 'dist', '*.egg-info']:
            try:
                shutil.rmtree(dir_to_remove)
            except:
                pass

# Read version from version.py
version = {}
with open(os.path.join("another_ayx_python_sdk", "version.py"), "r") as f:
    exec(f.read(), version)

setup(
    name="another-ayx-python-sdk",
    version=version['version'],
    description="Python SDK for Alteryx Plugin Development and Testing",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Jupiter Bakakeu",
    author_email="jupiter.bakakeu@gmail.com",
    maintainer="Jupiter Bakakeu",
    maintainer_email="jupiter.bakakeu@gmail.com",
    license="MIT",
    license_files=["LICENSE"],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Testing",
        "Environment :: Console",
    ],
    packages=find_packages(
        exclude=["tests*", "docs*", "**/__pycache__", "**/*.pyc"]
    ),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "pydantic",
        "packaging",
        "setuptools",
        "pyarrow",
        "xmltodict",
        "pyyaml",
        "requests",
        "another-ayx-plugin-cli>=1.2.4",
        "typing-extensions",
        "pypac",
        "pandas",
        "numpy",
        "deprecation",
        "grpcio",
        "grpcio-tools",   
        "protobuf",
        "psutil", 
        "Click",
        "python-dateutil",
        "pytz",
        "six",
        "typer",
        "wincertstore"
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
            "black",
            "isort",
            "flake8",
            "mypy",
            "twine"
        ]
    },
    entry_points={
        "console_scripts": [
            "another-ayx-python-sdk=another_ayx_python_sdk.__main__:main",
        ],
    },
    package_data={
        "another_ayx_python_sdk": [
            "assets/workspace_files/*",
            "assets/workspace_files/**/*",
            "assets/executables/*",
            "assets/executables/**/*",
            "assets/base_tool_config/*",
            "assets/base_tool_config/**/*",
            "cli/*",
            "core/**/*",
            "docs/**/*",
            "examples/**/*",
            "providers/**/*",
            "test_harness/**/*",
            "providers/amp_provider/resources/generated/*",
        ],
    },
    project_urls={
        "Homepage": "https://github.com/jupiterbak/another-ayx-python-sdk",
        "Repository": "https://github.com/jupiterbak/another-ayx-python-sdk.git",
    },
    cmdclass={
        'clean': CleanCommand,
    },
) 