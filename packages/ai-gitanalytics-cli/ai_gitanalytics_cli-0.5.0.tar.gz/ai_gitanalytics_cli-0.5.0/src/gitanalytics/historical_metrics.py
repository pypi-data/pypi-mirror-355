from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import json
import os
from pathlib import Path

@dataclass
class TimeSeriesPoint:
    """Represents a single point in time for metrics tracking."""
    timestamp: datetime
    num_contributors: int
    commit_frequency: int  # commits per day
    total_file_size: int  # in bytes
    file_changes: Dict[str, int]  # file path -> size change in bytes

@dataclass
class BaselineMetrics:
    """Represents baseline metrics for comparison."""
    reference_date: datetime
    reference_commit: str
    metrics: TimeSeriesPoint

class HistoricalMetrics:
    """
    Manages collection and analysis of historical metrics for a repository.
    """
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.metrics_file = os.path.join(repo_path, '.gitanalytics', 'historical_metrics.json')
        self._ensure_metrics_dir()
        self.time_series: List[TimeSeriesPoint] = []
        self.baselines: Dict[str, BaselineMetrics] = {}
        self._load_existing_metrics()

    def _ensure_metrics_dir(self):
        """Ensures the .gitanalytics directory exists."""
        metrics_dir = os.path.join(self.repo_path, '.gitanalytics')
        os.makedirs(metrics_dir, exist_ok=True)

    def _load_existing_metrics(self):
        """Loads existing metrics from storage if available."""
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    self.time_series = [
                        TimeSeriesPoint(
                            timestamp=datetime.fromisoformat(point['timestamp']),
                            num_contributors=point['num_contributors'],
                            commit_frequency=point['commit_frequency'],
                            total_file_size=point['total_file_size'],
                            file_changes=point['file_changes']
                        )
                        for point in data.get('time_series', [])
                    ]
                    self.baselines = {
                        name: BaselineMetrics(
                            reference_date=datetime.fromisoformat(baseline['reference_date']),
                            reference_commit=baseline['reference_commit'],
                            metrics=TimeSeriesPoint(**baseline['metrics'])
                        )
                        for name, baseline in data.get('baselines', {}).items()
                    }
            except Exception as e:
                print(f"Warning: Could not load historical metrics: {e}")

    def save_metrics(self):
        """Saves current metrics to storage."""
        data = {
            'time_series': [
                {
                    'timestamp': point.timestamp.isoformat(),
                    'num_contributors': point.num_contributors,
                    'commit_frequency': point.commit_frequency,
                    'total_file_size': point.total_file_size,
                    'file_changes': point.file_changes
                }
                for point in self.time_series
            ],
            'baselines': {
                name: {
                    'reference_date': baseline.reference_date.isoformat(),
                    'reference_commit': baseline.reference_commit,
                    'metrics': {
                        'timestamp': baseline.metrics.timestamp.isoformat(),
                        'num_contributors': baseline.metrics.num_contributors,
                        'commit_frequency': baseline.metrics.commit_frequency,
                        'total_file_size': baseline.metrics.total_file_size,
                        'file_changes': baseline.metrics.file_changes
                    }
                }
                for name, baseline in self.baselines.items()
            }
        }
        with open(self.metrics_file, 'w') as f:
            json.dump(data, f, indent=2)

    def add_metrics_point(self, point: TimeSeriesPoint):
        """Adds a new metrics point to the time series."""
        self.time_series.append(point)
        self.save_metrics()

    def set_baseline(self, name: str, reference_date: datetime, reference_commit: str, metrics: TimeSeriesPoint):
        """Sets a baseline for comparison."""
        self.baselines[name] = BaselineMetrics(
            reference_date=reference_date,
            reference_commit=reference_commit,
            metrics=metrics
        )
        self.save_metrics()

    def get_trend_analysis(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
        """
        Analyzes trends in the metrics over the specified time period.
        Returns a dictionary with trend analysis results.
        """
        filtered_points = self.time_series
        if start_date:
            filtered_points = [p for p in filtered_points if p.timestamp >= start_date]
        if end_date:
            filtered_points = [p for p in filtered_points if p.timestamp <= end_date]

        if not filtered_points:
            return {}

        # Calculate trends
        first_point = filtered_points[0]
        last_point = filtered_points[-1]
        days_diff = (last_point.timestamp - first_point.timestamp).days or 1

        return {
            'contributor_growth': last_point.num_contributors - first_point.num_contributors,
            'commit_frequency_change': last_point.commit_frequency - first_point.commit_frequency,
            'total_size_change': last_point.total_file_size - first_point.total_file_size,
            'size_change_per_day': (last_point.total_file_size - first_point.total_file_size) / days_diff,
            'period_days': days_diff
        }

    def compare_with_baseline(self, baseline_name: str) -> Dict:
        """
        Compares current metrics with a specified baseline.
        Returns a dictionary with comparison results.
        """
        if baseline_name not in self.baselines:
            return {}

        baseline = self.baselines[baseline_name]
        if not self.time_series:
            return {}

        current = self.time_series[-1]
        days_diff = (current.timestamp - baseline.reference_date).days or 1

        return {
            'contributor_change': current.num_contributors - baseline.metrics.num_contributors,
            'commit_frequency_change': current.commit_frequency - baseline.metrics.commit_frequency,
            'total_size_change': current.total_file_size - baseline.metrics.total_file_size,
            'size_change_per_day': (current.total_file_size - baseline.metrics.total_file_size) / days_diff,
            'days_since_baseline': days_diff
        }