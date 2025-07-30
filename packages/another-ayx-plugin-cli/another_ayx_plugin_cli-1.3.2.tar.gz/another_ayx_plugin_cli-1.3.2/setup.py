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
with open(os.path.join("another_ayx_plugin_cli", "version.py"), "r") as f:
    exec(f.read(), version)

setup(
    name="another-ayx-plugin-cli",
    version=version["version"],  # This will be dynamically set from another_ayx_plugin_cli.version.version
    description="Command Line Interface for Alteryx Plugin Development",
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
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Build Tools",
        "Environment :: Console",
    ],
    install_requires=[
        "typer",
        "pydantic",
        "packaging",
        "jinja2",
        "requests",
        "doit>=0.36.0",
        "xmltodict",
        "pyyaml",
        "click",
        "typing-extensions",
        "another-ayx-python-sdk",
    ],
    extras_require={
        "dev": [
            "pytest",
            "black",
            "isort",
            "flake8",
            "mypy",
        ],
    },
    project_urls={
        "Homepage": "https://github.com/jupiterbak/another-ayx-plugin-cli",
        "Repository": "https://github.com/jupiterbak/another-ayx-plugin-cli.git",
    },
    entry_points={
        "console_scripts": [
            "another-ayx-plugin-cli=another_ayx_plugin_cli.__main__:main",
        ],
    },
    packages=find_packages(
        exclude=["tests*", "docs*", "**/__pycache__", "**/*.pyc"]
        ),
    include_package_data=True,
    zip_safe=False,
    package_data={
        "another_ayx_plugin_cli": [
            "assets/*",
            "assets/**/*",
            "ayx_workspace/*",
            "ayx_workspace/**/*",
            "assets/workspace_files/.gitignore",
        ],
    },
    cmdclass={
        'clean': CleanCommand,
    },
) 