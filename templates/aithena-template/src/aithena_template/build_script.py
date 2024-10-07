import os
import shutil
import subprocess
import json
import sys

def build_common(config_file):
    """ Build a Python project using the provided configuration file."""

    # Load configuration from JSON file
    with open(config_file, "r") as f:
        config = json.load(f)

    project_name = config.get("project_name", "my_python_project")
    author_name = config.get("author_name", "Unknown Author")
    author_email = config.get("author_email", "unknown@example.com")
    packages = config.get("packages", ["src"])
    current_version = "0.1.0"

    # Step 1: Create project directory structure
    os.makedirs(f"{project_name}/src", exist_ok=True)
    os.makedirs(f"{project_name}/tests", exist_ok=True)

    # Create folders in src that match the packages in config
    for package in packages:
        package_path = package.replace("-", "_").replace(".", "/")
        os.makedirs(f"{project_name}/src/{package_path}", exist_ok=True)
        # Create __init__.py in each directory to make it a valid Python package
        package_parts = package_path.split("/")
        for i in range(1, len(package_parts) + 1):
            init_path = f"{project_name}/src/{'/'.join(package_parts[:i])}/__init__.py"
            with open(init_path, "w") as f:
                f.write(f'"""{package_parts[i-1]} module."""\n')

        # Write the __main__.py file with a simple hello world main function
        main_file_path = f"{project_name}/src/{package_path}/__main__.py"
        with open(main_file_path, "w") as main_file:
            main_file.write("""\
def main():
    print("Hello, World!")
    return "Hello, World!"

if __name__ == "__main__":
        main()
    """)
        
    # Add the current version to the top-level __init__.py
    with open(f"{project_name}/src/__init__.py", "w") as f:
        f.write(f'__version__ = "{current_version}"\n')

    # Step 2: Create necessary files
    with open(f"{project_name}/README.md", "w") as f:
        f.write(f"# {project_name} (v{current_version})\n")

    with open(f"{project_name}/VERSION", "w") as f:
        f.write(f"{current_version}\n")

    # Create pyproject.toml with necessary information
    base_package = packages[0].split(".")[0].replace("-", "_")
    pyproject_content = f"""\
[tool.poetry]
name = "{project_name}"
version = "{current_version}"
description = "{project_name}"
authors = ["{author_name} <{author_email}>"]
readme = "README.md"
packages = [{{include = "{base_package}",from = "src"}}]

[tool.poetry.dependencies]
python = ">=3.9,<3.13"

[tool.poetry.group.dev.dependencies]
pre-commit = "^3.8.0"
bump2version = "^1.0.1"
pytest = "^8.3.2"
pytest-sugar = "^1.0.0"
pytest-xdist = "^3.6.1"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.pytest.ini_options]
pythonpath = [
"."
]

[tool.poetry.scripts]
{project_name} = "{packages[0].replace('-', '_')}.__main__:main"
    """

    with open(f"{project_name}/pyproject.toml", "w") as f:
        f.write(pyproject_content)

    # Create .gitignore with sensible defaults
    gitignore_content = """\
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
# According to pypa/pipenv#598, it is recommended to include Pipfile.lock in version control.
# However, in case you do not want to do that, uncomment the following line:
# Pipfile.lock

# PEP 582; used by e.g. github.com/David-OConnor/pyflow
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyderworkspace

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/
"""

    with open(f"{project_name}/.gitignore", "w") as f:
        f.write(gitignore_content)

    # Create bumpversion configuration file
    bumpversion_content = f"""\
[bumpversion]
current_version = {current_version}
commit = False
tag = True
parse = (?P<major>\\d+)\\.(?P<minor>\\d+)\\.(?P<patch>\\d+)(\\-(?P<release>[a-z]+)(?P<dev>\\d+))?
serialize = 
    {{major}}.{{minor}}.{{patch}}-{{release}}{{dev}}
    {{major}}.{{minor}}.{{patch}}

[bumpversion:part:release]
optional_value = _
first_value = dev
values = 
    dev
    _

[bumpversion:part:dev]

[bumpversion:file:pyproject.toml]
search = version = "{{current_version}}"
replace = version = "{{new_version}}"

[bumpversion:file:VERSION]
search = {{current_version}}
replace = {{new_version}}

[bumpversion:file:README.md]

[bumpversion:file:src/__init__.py]

"""

    with open(f"{project_name}/.bumpversion.cfg", "w") as f:
        f.write(bumpversion_content)

    # Create pre-commit hook configuration file
    pre_commit_content = """\
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v3.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-json
    """

    with open(f"{project_name}/.pre-commit-config.yaml", "w") as f:
        f.write(pre_commit_content)

    # # Step 3: Create a virtual environment in a .venv folder and activate it
    # subprocess.run(["python3", "-m", "venv", f"{project_name}/.venv"])

    # # Activate the virtual environment
    # activate_script = os.path.join(project_name, ".venv", "bin", "activate")
    # subprocess.run(["source", activate_script], shell=True)

    # # Install pre-commit and set up the git hooks
    # subprocess.run([f"{project_name}/.venv/bin/pip", "install", "pre-commit"])

    # # Function to check if the directory or any of its parents is a Git repository
    # def is_git_repo(directory):
    #     try:
    #         subprocess.run(["git", "-C", directory, "rev-parse", "--show-toplevel"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #         return True
    #     except subprocess.CalledProcessError:
    #         return False   

    # subprocess.run(["poetry install"], shell=True, cwd=project_name)

    # # Run poetry install
    # if subprocess.run(["poetry", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
    #     subprocess.run(["poetry", "install"], cwd=project_name)
    #     print("Ran poetry install.")
    # else:
    #     print("Poetry is not installed. Package will not be installed.")

    print("Project scaffolded successfully!")