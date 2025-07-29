import os
import platform
from pathlib import Path
from textwrap import dedent

IS_WINDOWS: bool = platform.system() in ("Windows")

def create_pypi_skeleton(
    module_name: str,
    target_path: str = ".",
    author_name: str = "YOUR_NAME",
    author_email: str = "YOUR_EMAIL",
    project_description: str = "SOME DESCRIPTION",
    project_homepage: str = "https://github.com/github_username/project_name",
    project_issues_link: str = "https://github.com/github_username/project_name/issues",  
) -> None:
    """
    Automatically creates PyPI project skeleton in the current directory

    Typical PyPI project skeleton given module_name="testing123"

    testing123/                 
        src/                    # all code goes here
            testing123/         
                __init__.py     # main folder where users import functions from
            tests/              
                main.py         # unit tests go here
                __init__.py
            __init__.py
        .gitignore              # files/folders written here are ignored by git
        LICENSE                 # license stuff
        pyproject.toml          # contains important config stuff for PyPI
        README.md               # tells users what your project is about
        upload.py               # helper script to upload project to PyPI
        test.py                 # testing script to run
        tests.py                # import and run tests in /src/testing123/tests/

    Args:
        module_name (str): name of module. This will be your folder name.
        target_path (str): where you want to create your project folder. Defualts to current directory "."
        author_name (str): your name
        author_email (str): your email
        project_description (str): one-liner description of project
        project_homepage (str): homepage of project repo eg. https://github.com/username/projectname
        project_issues_link (str): issues page of project repo eg. https://github.com/username/projectname/issues
    """
    # create required folders
    BASE_PATH: Path = Path(target_path) / module_name
    SRC_PATH: Path = BASE_PATH / 'src'
    CODE_PATH: Path = SRC_PATH / module_name
    TESTS_PATH: Path = SRC_PATH / 'tests'

    paths: list[Path] = [
        BASE_PATH,
        SRC_PATH,
        CODE_PATH,
        TESTS_PATH
    ]
    for path in paths:
        os.mkdir(path)

    # created required .py files
    with open(SRC_PATH / "__init__.py", "w") as f:
        pass

    with open(CODE_PATH / "__init__.py", "w") as f:
        pass

    with open(CODE_PATH / f"{module_name}_main.py", "w") as f:
        f.write(
            dedent(f"""
                def {module_name}():
                    pass
            """)
        )

    with open(TESTS_PATH / "main.py", "w") as f:
        f.write(dedent("""
            import unittest

            class TestMain(unittest.TestCase):
                \"\"\"
                Unit test cases go here
                \"\"\"
                pass
        """))

    with open(TESTS_PATH / "__init__.py", "w") as f:
        pass

    with open(BASE_PATH / ".gitignore", "w") as f:
        f.write(dedent("""
            __pycache__
            */__pycache__ 
            */__pycache__/*
            .DS_Store
            *.pyc
            dist
            venv
        """))

    with open(BASE_PATH / "LICENSE", "w") as f:
        f.write("this is a license")

    with open(BASE_PATH / "pyproject.toml", "w") as f:
        f.write(dedent(f"""
            [build-system]
            requires = ["hatchling"]
            build-backend = "hatchling.build"

            [project]
            name = "{module_name}"
            version = "0.0.1"
            authors = [
                {{ name="{author_name}", email="{author_email}" }},
            ]
            description = "{project_description}"
            readme = "README.md"
            requires-python = ">=3.8"
            classifiers = [
                "Programming Language :: Python :: 3",
                "License :: OSI Approved :: MIT License",
                "Operating System :: OS Independent",
            ]
            dependencies = [

            ]

            [project.urls]
            Homepage = "{project_homepage}"
            Issues = "{project_issues_link}"
        """))

    with open(BASE_PATH / "README.md", "w") as f:
        f.write(dedent(f"""
            # {module_name}
            Short description of project

            # Installation
            ```
            pip install {module_name}
            ```

            # Quickstart
            ```python
            # some code
            ```
        """))

    python_cmd: str = "python" if IS_WINDOWS else "python3"

    with open(BASE_PATH / "upload.py", "w") as f:
        f.write(dedent(f"""
            \"\"\"
            - finds and increments project version eg. 0.0.4 to 0.0.5 (else version conflict error)
            - builds PyPI package locally into dist/* using "python -m build"
            - uploads built PyPI package using "python -m twine upload dist/*" (need to key in your API key)

            "pip install build twine" if you haven't already
            \"\"\"
            import os
            import re
            import sys

            with open('pyproject.toml') as f:
                text = f.read()

            # "python -m upload.py --nowrite" if you don't want this script to increment version in pyproject.toml
            if "--nowrite" not in sys.argv:
                print("incrementing version by 1 in pyproject.toml")
                old_version: str = re.findall('version = "(.*?)"', text)[0]     # "0.0.4"
                major, minor, patch = old_version.split('.')                    # major="0" minor="0" patch="4"
                new_patch = int(patch) + 1
                new_version = f'{{major}}.{{minor}}.{{new_patch}}'                    # "0.0.5"
                text = re.sub(old_version, new_version, text)
                with open('pyproject.toml', 'w') as f:
                    f.write(text)   

            with open('pyproject.toml', 'w') as f:
                f.write(text)    

            commands = [
                'rm -rf ./dist',                    # removes current dist folder
                '{python_cmd} -m build',                 # build PyPI project
                '{python_cmd} -m twine upload dist/*'    # upload to PyPI
            ]

            for command in commands:
                print(command)
                os.system(command)
        """))

    with open(BASE_PATH / "test.py", "w") as f:
        f.write(
            dedent(f"""
            from src.{module_name} import {module_name}

            # do stuff with {module_name}
            """)
        )

    with open(BASE_PATH / "tests.py", "w") as f:
        f.write(
            dedent(f"""
            import unittest
            from src.tests.main import TestMain

            if __name__ == "__main__":
                   unittest.main()
            """)
        )

    print(f"successfully created PyPI project skeleton for {module_name}")
