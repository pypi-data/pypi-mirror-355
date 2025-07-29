import git
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Tuple
from collections import defaultdict
import os
from .historical_metrics import HistoricalMetrics, TimeSeriesPoint

class Commit(BaseModel):
    """
    Pydantic model to represent a single Git commit.
    """
    commit_hash: str = Field(..., alias='hexsha')
    author_name: str
    author_email: str
    date: datetime
    message: str
    diff: str

    class Config:
        arbitrary_types_allowed = True

class GitAnalyzer:
    """
    Analyzes a Git repository to extract commit information and calculate churn.
    """
    def __init__(self, repo_path: str):
        """
        Initializes the GitAnalyzer.

        Args:
            repo_path: The file path to the Git repository.

        Raises:
            git.InvalidGitRepositoryError: If the path is not a valid Git repository.
            git.NoSuchPathError: If the path does not exist.
        """
        try:
            self.repo = git.Repo(repo_path, search_parent_directories=True)
        except (git.InvalidGitRepositoryError, git.NoSuchPathError) as e:
            print(f"Error: {e}")
            raise

        # Exclude common non-source files from diffs
        self.exclude_patterns = ['*.json', '*.md', '*.txt', 'LICENSE', '.gitignore']

        # Initialize historical metrics
        self.historical_metrics = HistoricalMetrics(repo_path)

    def _calculate_file_sizes(self) -> Tuple[int, Dict[str, int]]:
        """
        Calculates the total size of all files and individual file sizes.
        Returns a tuple of (total_size, file_sizes_dict).
        """
        total_size = 0
        file_sizes = {}

        for root, _, files in os.walk(self.repo.working_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    rel_path = os.path.relpath(file_path, self.repo.working_dir)
                    file_sizes[rel_path] = size
                    total_size += size
                except OSError:
                    continue

        return total_size, file_sizes

    def _calculate_commit_frequency(self, commits: List[Commit], days: int = 30) -> int:
        """
        Calculates the average number of commits per day over the specified period.
        """
        if not commits:
            return 0

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        recent_commits = [c for c in commits if start_date <= c.date <= end_date]
        return len(recent_commits) / days

    def collect_historical_metrics(self, branch: Optional[str] = None) -> TimeSeriesPoint:
        """
        Collects current metrics for historical tracking.
        """
        commits = self.get_commits(branch)

        # Get unique contributors
        contributors = set(c.author_name for c in commits)

        # Calculate commit frequency (commits per day over last 30 days)
        commit_frequency = self._calculate_commit_frequency(commits)

        # Calculate file sizes
        total_size, file_sizes = self._calculate_file_sizes()

        # Create metrics point with UTC timestamp
        metrics_point = TimeSeriesPoint(
            timestamp=datetime.now(timezone.utc),
            num_contributors=len(contributors),
            commit_frequency=commit_frequency,
            total_file_size=total_size,
            file_changes=file_sizes
        )

        # Save to historical metrics
        self.historical_metrics.add_metrics_point(metrics_point)

        return metrics_point

    def set_milestone_baseline(self, name: str, commit_hash: str):
        """
        Sets a baseline using a specific commit as a milestone.
        """
        try:
            commit = self.repo.commit(commit_hash)
            self.repo.git.checkout(commit_hash)

            # Collect metrics at this point
            metrics_point = self.collect_historical_metrics()

            # Set as baseline
            self.historical_metrics.set_baseline(
                name=name,
                reference_date=commit.authored_datetime,
                reference_commit=commit_hash,
                metrics=metrics_point
            )

            # Return to previous state
            self.repo.git.checkout('-')

        except git.GitCommandError as e:
            print(f"Error setting milestone baseline: {e}")
            raise

    def get_commits(self, branch: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Commit]:
        """
        Extracts commits. If a branch is specified, it shows commits on that
        branch which are not in the 'main' branch. Otherwise, it shows commits
        from the current HEAD.
        """
        if branch:
            commit_spec = f"main..{branch}"
        else:
            commit_spec = self.repo.head.ref

        kwargs = {}
        if start_date:
            kwargs['after'] = start_date
        if end_date:
            kwargs['before'] = end_date

        try:
            commits_iter = self.repo.iter_commits(commit_spec, **kwargs)
        except git.GitCommandError:
            commits_iter = self.repo.iter_commits(branch or self.repo.head.ref, **kwargs)

        commit_list = []
        for commit in commits_iter:
            try:
                if commit.parents:
                    diff_text = self.repo.git.diff(commit.parents[0].hexsha, commit.hexsha)
                else:
                    diff_text = self.repo.git.show(commit.hexsha)
            except Exception:
                diff_text = "Could not retrieve diff."

            # Ensure commit date is timezone-aware
            commit_date = commit.authored_datetime
            if commit_date.tzinfo is None:
                commit_date = commit_date.replace(tzinfo=timezone.utc)

            commit_data = {
                'hexsha': commit.hexsha,
                'author_name': commit.author.name,
                'author_email': commit.author.email,
                'date': commit_date,
                'message': commit.message.strip(),
                'diff': diff_text
            }
            commit_list.append(Commit.model_validate(commit_data))

        return commit_list

    def calculate_churn(self, branch: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, int]:
        """
        Calculates the churn (number of times each file was modified) for Python files.

        Args:
            branch: The branch to analyze.
            start_date: The start date for analysis.
            end_date: The end date for analysis.

        Returns:
            A dictionary mapping file paths to their modification count.
        """
        if branch:
            commit_spec = f"main..{branch}"
        else:
            commit_spec = self.repo.head.ref

        kwargs = {}
        if start_date:
            kwargs['after'] = start_date
        if end_date:
            kwargs['before'] = end_date

        try:
            commits = list(self.repo.iter_commits(commit_spec, **kwargs))
        except git.GitCommandError:
            commits = list(self.repo.iter_commits(branch or self.repo.head.ref, **kwargs))

        churn_data = defaultdict(int)

        for commit in commits:
            for file_path in commit.stats.files:
                if file_path.endswith('.py'):
                    churn_data[file_path] += 1

        return churn_data
