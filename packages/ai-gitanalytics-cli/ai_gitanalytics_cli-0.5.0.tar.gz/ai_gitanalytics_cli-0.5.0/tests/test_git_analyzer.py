import pytest
from gitanalytics.git_analyzer import GitAnalyzer
import git
from datetime import datetime, timedelta
import tempfile

def test_get_all_commits(test_repo):
    """
    Tests that the GitAnalyzer finds all commits in the test repository.
    """
    analyzer = GitAnalyzer(str(test_repo))
    commits = analyzer.get_commits()
    # The conftest fixture creates 3 commits
    assert len(commits) == 3
    assert commits[0].message == "refactor: Modify module_a"
    assert "module_a.py" in commits[0].diff

def test_no_commits_found(test_repo):
    """
    Tests that the GitAnalyzer returns an empty list when no commits match the criteria.
    """
    # A date far in the future
    future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    analyzer = GitAnalyzer(str(test_repo))
    commits = analyzer.get_commits(start_date=future_date)
    assert len(commits) == 0

def test_invalid_repo_path():
    """
    Tests that GitAnalyzer raises the correct exception for an invalid path.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(git.InvalidGitRepositoryError):
            GitAnalyzer(temp_dir)

def test_commit_content(test_repo):
    """
    Tests that the commit content (message, author, etc.) is extracted correctly.
    """
    analyzer = GitAnalyzer(str(test_repo))
    commits = analyzer.get_commits()
    latest_commit = commits[0]

    assert latest_commit.message == "refactor: Modify module_a"
    assert "Test User" in latest_commit.author_name # Default git user
    assert isinstance(latest_commit.date, datetime)
    assert len(latest_commit.commit_hash) == 40