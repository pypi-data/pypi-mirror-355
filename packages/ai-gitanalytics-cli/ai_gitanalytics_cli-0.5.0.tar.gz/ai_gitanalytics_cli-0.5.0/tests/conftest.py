import pytest
import git
import tempfile
import shutil
from pathlib import Path
import os

@pytest.fixture(scope="function")
def test_repo():
    """
    Pytest fixture to create a temporary Git repository for testing.

    This fixture creates a new directory, initializes a Git repository,
    makes a few commits, and then yields the path to the repository.
    After the test function completes, it cleans up by deleting the
    temporary directory.

    Yields:
        Path: The path to the temporary Git repository.
    """
    repo_dir = Path(tempfile.mkdtemp())

    # Store the original working directory
    original_cwd = Path.cwd()
    os.chdir(repo_dir)

    repo = git.Repo.init(repo_dir)

    # Set a specific author for the test commits
    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Test User").release()
        cw.set_value("user", "email", "test@example.com").release()

    # Create and commit some python files
    py_file_1 = repo_dir / "module_a.py"
    py_file_1.write_text("def hello():\n    print('hello')\n")
    repo.index.add([str(py_file_1.relative_to(repo_dir))])
    repo.index.commit("feat: Add module_a")

    py_file_2 = repo_dir / "module_b.py"
    py_file_2.write_text("def world():\n    pass\n")
    repo.index.add([str(py_file_2.relative_to(repo_dir))])
    repo.index.commit("feat: Add module_b")

    # Modify the first file to generate churn
    py_file_1.write_text("def hello(name):\n    print(f'hello {name}')\n")
    repo.index.add([str(py_file_1.relative_to(repo_dir))])
    repo.index.commit("refactor: Modify module_a")

    yield repo_dir

    # Teardown: change back to the original directory and remove the temp one
    os.chdir(original_cwd)
    shutil.rmtree(repo_dir)